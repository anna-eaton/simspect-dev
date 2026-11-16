#!/usr/bin/env python3
"""verify_interleave_only.py: check a Stage-2 testset built with the interleave-only category (ilv-vocab, 2026-11-12).

Works with chain interleaving off (corpus A) and on (corpus B). For each <stem>.ann.json it re-derives the pass-4
program exactly as batch_generate.run_pipeline did (same run config: instruction table, vocab_rj, interleave block
incl. interleave_only, reg_naming; same per-test seeds), then checks, read-only:
  E1 fillers/splices: every Alloy register/memory source still descends from its original Alloy writer
     (measure_xmit_path_alu.all_edges_intact, as verify_fanout_v2.py), and no filler writes a register that ANY
     instruction of the program (Alloy or chain step) reads or writes;
  E2 chain steps (corpus B): no chain step is the last writer of a location an Alloy instruction reads from an Alloy
     writer (the Alloy rf edge is never clobbered); chain outputs may feed unspecified Alloy slots (the intended hook-on);
  E3 ld transmitter fed by a load: the producer still feeds the transmitter's address;
  E4 every chain step drawn from the category ("ilv:<name>") is in the table, its template text is in the .ll, and
     every filler op is in the table;
  plus a census: filler-op and chain-op frequencies (expected uniform), `(%rsp)` references in the .s.
Usage: verify_interleave_only.py --config <run_config.jsonc> --xml <xml_dir> --out <mode dir with llvm/ asm/ ann/> --mode <mode>
Exit 1 if any problem. Prints one JSON line of totals.
"""
import argparse, collections, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "STAGE2_compilation")); sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import measure_xmit_path_alu as M  # noqa: E402
import parsexml as P  # noqa: E402
import batch_generate as BG  # noqa: E402


def edges_intact(base, new):
    """measure_xmit_path_alu.all_edges_intact, except a source whose writer in `base` is a synthetic op
    (a chain step's output hooked onto an Alloy operand, the intended chain-interleave mechanism, checked
    by E2) is not an Alloy rf edge and is skipped. With no chain steps this equals all_edges_intact."""
    def writer(ops, loc, before):
        for j in range(before - 1, -1, -1):
            if loc in ops[j]["dsts"]:
                return j
        return None
    def anc(ops, j, target, seen):
        if j in seen:
            return False
        seen.add(j)
        if ops[j]["atom"] == target and not ops[j]["synthetic"]:
            return True
        if not ops[j]["synthetic"] or ops[j]["atom"].startswith("_chain"):
            return False   # stop at another Alloy op or a chain step
        return any(anc(ops, w, target, seen) for s in ops[j]["srcs"] for w in [writer(ops, s, j)] if w is not None)
    idx = {o["atom"]: i for i, o in enumerate(new) if not o["synthetic"]}
    for j, o in enumerate(base):
        if o["synthetic"]:
            continue
        for s in o["srcs"]:
            w0 = writer(base, s, j)
            if w0 is None or base[w0]["synthetic"]:
                continue
            w1 = writer(new, s, idx[o["atom"]])
            if w1 is None or not anc(new, w1, base[w0]["atom"], set()):
                return False
    return True


def load_cfg(p):
    t = Path(p).read_text()
    return json.loads(re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S)))


def derive(cfg, xml_text, stem, mode):
    """Run batch_generate.run_pipeline with pass5/emit_ann replaced by capture: {vstem: pass4 result}."""
    got = {}
    if True:   # same order as batch_generate._load_parser; tables already reloaded in main()
        fns = [P.parse_alloy_xml, P.pass1_specify_state_a, P.pass2_specify_instructions, P.pass2_5_specify_branches,
               P.pass2_6_specify_stl, P.pass_interleave, P.pass3_assign_operands, P.pass4_ssa, None, None]

    def cap5(r4, func_name=None, **kw):
        got[func_name] = r4
    fns[8] = cap5
    fns[9] = lambda *a, **k: None
    BG.run_pipeline(xml_text, stem, Path("/nonexistent"), mode, _fns=tuple(fns),
                    interleave_cfg=cfg.get("interleave") or {}, fpr_cfg=cfg.get("fpr"),
                    reg_naming_cfg=cfg.get("reg_naming"), fv2_cfg=cfg.get("fanout_v2"),
                    stsep_cfg=None, brcond_cfg=cfg.get("branch_cond"))
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--xml", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--mode", required=True)
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    tab = cfg["paths"].get("instruction_tables")
    if tab:
        P.reload_tables(str(ROOT / tab))
    ilv_f = ((cfg.get("fanout_v2") or {}).get("interleave_only") or {})
    ilv_c = ((cfg.get("interleave") or {}).get("interleave_only") or {})
    table = P.load_interleave_only((ilv_f or ilv_c).get("table")) if (ilv_f.get("enabled") or ilv_c.get("enabled")) else {}
    out = Path(a.out)
    tot = collections.Counter(); bad = []
    fill_ops = collections.Counter(); chain_ops = collections.Counter()
    for annf in sorted((out / "ann").glob("*.ann.json")):
        vstem = annf.name[:-len(".ann.json")]
        stem = re.sub(r"_v\d+$", "", vstem)
        ann = json.loads(annf.read_text())
        r4s = derive(cfg, (Path(a.xml) / f"{stem}.xml").read_text(), stem, a.mode)
        r4 = r4s.get(vstem)
        if r4 is None:
            bad.append((vstem, "could not re-derive")); continue
        tot["tests"] += 1
        ll = (out / "llvm" / f"{vstem}.ll").read_text()
        sp = out / "asm" / f"{vstem}.s"
        if sp.exists():
            tot["rsp_refs"] += sp.read_text().count("(%rsp)")
        ops = M.to_ops(r4["instructions"])
        chain = [i for i, o in enumerate(ops) if o["synthetic"] and o["atom"].startswith("_chain")]
        # E4 chain steps
        for r in r4["instructions"]:
            c = r.get("concrete_instruction") or ""
            if r.get("synthetic") and r["instruction"].startswith("_chain"):
                chain_ops[c] += 1
                if c.startswith("ilv:"):
                    e = table.get(c[4:])
                    if e is None:
                        bad.append((vstem, "chain op not in table", c))
                    elif e["asm"] not in ll:
                        bad.append((vstem, "chain template missing from .ll", c))
        # E2 chain steps never clobber an Alloy rf edge
        if chain:
            noch = [o for i, o in enumerate(ops) if i not in set(chain)]
            def writer(lst, loc, before):
                for j in range(before - 1, -1, -1):
                    if loc in lst[j]["dsts"]:
                        return j
                return None
            pos_noch = {o["atom"]: j for j, o in enumerate(noch)}
            for j, o in enumerate(ops):
                if o["synthetic"]:
                    continue
                for s in o["srcs"]:
                    w0 = writer(noch, s, pos_noch[o["atom"]])
                    if w0 is None:
                        continue   # unspecified/initial value: chain hook-on allowed
                    w1 = writer(ops, s, j)
                    if w1 is None or ops[w1]["atom"] != noch[w0]["atom"]:
                        bad.append((vstem, "chain step clobbers Alloy edge", o["atom"], s)); tot["chain_edge_bad"] += 1
            tot["chain_tests"] += 1
        # E1 fillers and splices
        fv = ann.get("fanout_v2")
        if fv is not None:
            used = {x for o in ops for x in (o["srcs"] | o["dsts"]) if x.startswith("r:")}
            idx = {o["pc"]: i for i, o in enumerate(ops)}
            new = [dict(o) for o in ops]; ins = []
            for f in fv["fillers"]:
                fill_ops[f["op"]] += 1
                if table and f["op"] not in table:
                    bad.append((vstem, "filler op not in table", f["op"]))
                if "dst" not in f:
                    continue   # operand-less filler (jmp, nops): no dataflow
                d = "r:" + f["dst"]
                if d in used:
                    bad.append((vstem, "filler writes a program register", f)); tot["filler_bad"] += 1
                ins.append((idx[f["before_pc"]], dict(kind="other_n", alu=True, srcs={"r:" + s for s in f["srcs"]}, dsts={d},
                                                      xm=False, pc=-1, synthetic=True, atom="F")))
            for s in fv["splices"]:
                if s.get("shared_with_previous"):
                    continue
                r = "r:" + s["reg"]
                ins.append((idx[s["consumer_pc"]], dict(kind="other_n", alu=True, srcs={r}, dsts={r}, xm=False, pc=-1,
                                                        synthetic=True, atom="S%d" % s["consumer_pc"])))
            for pos, op in sorted(ins, key=lambda t: t[0], reverse=True):
                new.insert(pos, op)
            ok = edges_intact(ops, new)
            tot["edges_intact"] += ok
            if not ok:
                bad.append((vstem, "edge broken by filler/splice"))
            prod, _ = M.producer_of(r4)
            if prod:
                rp, ra = M.analyze(new, prod)
                tot["ld_xmit_load_fed"] += 1; tot["xmit_path_intact"] += rp; tot["alu_on_xmit_path"] += ra
                if not rp:
                    bad.append((vstem, "xmit path broken"))
    res = {"totals": dict(tot), "filler_ops": dict(fill_ops.most_common()), "chain_ops": dict(chain_ops.most_common()),
           "n_problems": len(bad), "problems": [list(map(str, b)) for b in bad[:20]]}
    print(json.dumps(res))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
