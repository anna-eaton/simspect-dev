from __future__ import annotations

import argparse
import json
import random
import sys
import traceback
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import parsexml

MODES = ["mispredict_not_taken", "mispredict_taken"]


def run_pipeline(xml_text, stem, out_dir, mode, interleave_cfg, fpr_cfg, reg_naming_cfg, fv2_cfg, brcond_cfg):
    icfg = interleave_cfg or {}
    enabled = icfg.get("enabled", False)
    n_variants = int(icfg.get("variants_per_instance", 1)) if enabled else 1
    inst = parsexml.parse_alloy_xml(xml_text)
    r1 = parsexml.pass1_specify_state_a(inst)
    variant_zero_no_chain = bool(icfg.get("variant_zero_no_chain", False))
    num_chains_choices = icfg.get("num_chains_choices")
    for v in range(n_variants):
        vseed = zlib.crc32(f"{stem}_v{v}".encode())
        random.seed(vseed)
        r2 = parsexml.pass2_specify_instructions(r1, vocab_rj=fv2_cfg.get("vocab_rj"))
        r25 = parsexml.pass2_5_specify_branches(r2, branch_mode=mode)
        rng = random.Random(vseed ^ 0xABCD_1234)
        if enabled and (variant_zero_no_chain or num_chains_choices):
            icfg_v = dict(icfg)
            if variant_zero_no_chain and v == 0:
                icfg_v["num_chains"] = 0
            elif num_chains_choices:
                icfg_v["num_chains"] = rng.choice(list(num_chains_choices))
            r_il = parsexml.pass_interleave(r25, icfg_v, rng)
        else:
            r_il = parsexml.pass_interleave(r25, icfg if enabled else None, rng)
        vstem = f"{stem}_v{v}" if n_variants > 1 else stem
        rn = {"mode": reg_naming_cfg.get("mode", "sorted")}
        if rn["mode"] == "random":
            rn["seed"] = zlib.crc32(f"regs:{reg_naming_cfg.get('seed', 0)}:{vstem}".encode())
        r3 = parsexml.pass3_assign_operands(r_il, reg_naming=rn)
        r4 = parsexml.pass4_ssa(r3)
        parsexml.pass5_emit_llvm(r4, func_name=vstem, out_path=str(out_dir / f"{vstem}.ll"),
                                 fpr_cfg=fpr_cfg, fv2_cfg=fv2_cfg, brcond_cfg=brcond_cfg)
        parsexml.emit_branch_annotations(r4, out_path=str(out_dir / f"{vstem}.ann.json"))


def main():
    ap = argparse.ArgumentParser(description="Stage 2: Alloy XML instances -> LLVM IR + branch annotations.")
    ap.add_argument("input_dir")
    ap.add_argument("--out", dest="output_dir", required=True)
    ap.add_argument("--instruction-tables", required=True)
    ap.add_argument("--mode", action="append", dest="modes", choices=MODES)
    ap.add_argument("--interleave-config", default="{}")
    ap.add_argument("--fpr-config", required=True)
    ap.add_argument("--reg-naming-config", required=True)
    ap.add_argument("--fanout-v2-config", required=True)
    ap.add_argument("--branch-cond-config", required=True)
    a = ap.parse_args()
    parsexml.reload_tables(a.instruction_tables)
    modes = a.modes or MODES
    cfgs = dict(interleave_cfg=json.loads(a.interleave_config), fpr_cfg=json.loads(a.fpr_config),
                reg_naming_cfg=json.loads(a.reg_naming_config), fv2_cfg=json.loads(a.fanout_v2_config),
                brcond_cfg=json.loads(a.branch_cond_config))
    out = Path(a.output_dir).resolve()
    xml_files = sorted(Path(a.input_dir).resolve().glob("inst-*.xml"))
    ok = err = 0
    for x in xml_files:
        text = x.read_text(encoding="utf-8")
        for mode in modes:
            d = out if len(modes) == 1 else out / mode
            d.mkdir(parents=True, exist_ok=True)
            try:
                run_pipeline(text, x.stem, d, mode, **cfgs)
                print(f"  [ok]  {x.name}  ({mode})")
                ok += 1
            except NotImplementedError as exc:
                print(f"  [skip] {x.name}  ({mode}): {exc}")
                err += 1
            except Exception:
                print(f"  [err]  {x.name}  ({mode}):")
                traceback.print_exc()
                err += 1
    print(f"\nDone: {ok}/{ok + err} succeeded, {err}/{ok + err} failed.")


if __name__ == "__main__":
    main()
