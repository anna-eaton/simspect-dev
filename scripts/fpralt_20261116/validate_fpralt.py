#!/usr/bin/env python3
"""validate_fpralt.py -- local validation of the fpr.p option (xmm-fix-agent, 2026-11-16).

Anna 2026-11-16: vector-register routing must be an ALTERNATIVE concretization of a load (next to the integer one), not applied to every
load. parsexml.py got an optional fpr.p (per-load routing probability; absent = old behavior). This script checks, on STT XMLs from the
evaluated big corpus STT_6_u_core_lpP_s2A (extracted read-only from experiments/2026-11-16_final/data/corpus_e2w_*.tar.xz):

  1. default unchanged: recipe A (runconfigs/bigcorpus_20261115/stage2_final_A.jsonc, no "p") through the edited parsexml.py gives .ll and
     .ann.json byte-identical to the pristine copy STAGE2_compilation/proposed/pre_fpr_p_20261116/parsexml.py (= the code that built the
     corpus, sha256 7611a4bc...), and the "fpr" block equals the one in the corpus's own .ann.json;
  2. p = 0 gives the same .ll as fpr off (a non-routed load is emitted exactly as without routing);
  3. the new recipe (stage2_final_A_fpralt.jsonc, p = 0.5): routed / eligible loads, integer-only tests, xmm only where expected
     (routed loads, plus the interleave-only SSE fillers on xmm14/xmm15 whose outputs are never read), register histogram;
  4. the .ll compiles with clang -O2 for x86-64 and assembles (well-formed .s), every PC label survives, the ann is consistent.
Full compile_annotate (address resolution) needs the cafe GNU toolchain + llvm-objdump-15 and is not run here.

Usage (repo root):
  python3 scripts/fpralt_20261116/validate_fpralt.py --src build/fpralt_20261116/src/STT_6_u_core_lpP_s2A \
      --sample20 build/fpralt_20261116/src/sample20.txt --sample300 build/fpralt_20261116/src/sample300.txt \
      --out build/fpralt_20261116/out
Writes <out>/validate_fpralt.log (every check) and <out>/summary.json; exit 1 on any failed check.
"""
import argparse
import collections
import copy
import datetime as dt
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S2 = ROOT / "STAGE2_compilation"
sys.path.insert(0, str(S2))
import parsexml as P            # noqa: E402
import batch_generate as BG     # noqa: E402

MODES = ["mispredict_not_taken", "mispredict_taken"]
CFG_A = ROOT / "runconfigs/bigcorpus_20261115/stage2_final_A.jsonc"
CFG_ALT = ROOT / "runconfigs/bigcorpus_20261115/stage2_final_A_fpralt.jsonc"
PRISTINE = S2 / "proposed/pre_fpr_p_20261116/parsexml.py"
CLANG = next((c for c in ("clang-15", "/opt/homebrew/opt/llvm/bin/clang", "clang") if shutil.which(c)), None)
XMM = re.compile(r"%xmm(\d+)")


def jsonc(path):
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'//[^\n]*', '', t)
    return json.loads(t)


def stage2_args(cfg):
    """the same keys pipeline.py phase_llvm hands batch_generate.py"""
    return dict(tables=str(ROOT / cfg["paths"]["instruction_tables"]),
                interleave=cfg.get("interleave") or None,
                fpr=cfg["fpr"] if cfg.get("fpr", {}).get("enabled") else None,
                reg_naming=cfg.get("reg_naming") or dict(BG.DEFAULT_REG_NAMING),
                fv2=cfg["fanout_v2"] if cfg.get("fanout_v2", {}).get("enabled") else None,
                brcond=cfg["branch_cond"] if cfg.get("branch_cond", {}).get("from_alloy") else None)


def load_pristine():
    td = Path(tempfile.mkdtemp(prefix="pristine_fpr_p_"))
    shutil.copy(PRISTINE, td / "parsexml.py")
    (td / "instruction_tables").symlink_to(S2 / "instruction_tables")
    spec = importlib.util.spec_from_file_location("parsexml_pristine_20261116", td / "parsexml.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m, td


def fns(mod):
    return (mod.parse_alloy_xml, mod.pass1_specify_state_a, mod.pass2_specify_instructions, mod.pass2_5_specify_branches,
            mod.pass2_6_specify_stl, mod.pass_interleave, mod.pass3_assign_operands, mod.pass4_ssa, mod.pass5_emit_llvm,
            mod.emit_branch_annotations)


def gen(xml, mode, a, mod=P):
    mod.reload_tables(a["tables"])
    with tempfile.TemporaryDirectory() as td:
        BG.run_pipeline(xml.read_text(encoding="utf-8"), xml.stem, Path(td), mode, _fns=fns(mod),
                        interleave_cfg=a["interleave"], fpr_cfg=a["fpr"], reg_naming_cfg=a["reg_naming"],
                        fv2_cfg=a["fv2"], brcond_cfg=a["brcond"])
        ll = (Path(td) / f"{xml.stem}.ll").read_text()
        annb = (Path(td) / f"{xml.stem}.ann.json").read_bytes()
    return ll, annb, json.loads(annb)


def xmm_lines(ll):
    return [l for l in ll.splitlines() if "%xmm" in l]


def classify_xmm(ll, ann, stem):
    """every .ll line naming an xmm register must be a routed load (its pc marker) or an interleave-only filler (%__fill_*)"""
    safe = stem.replace("-", "_").replace(".", "_")
    routed = {r["pc"] for r in ann.get("fpr", {}).get("routes", [])}
    out = collections.Counter()
    bad = []
    for l in xmm_lines(ll):
        pcs = {int(x) for x in re.findall(rf"__litmus_{safe}_pc(\d+):", l)}
        if "%__fill_" in l:
            out["filler"] += 1
            if set(XMM.findall(l)) - {"14", "15"}:
                bad.append(("filler uses a non-scratch xmm", l[:200]))
        elif pcs & routed:
            out["routed_load"] += 1
        else:
            bad.append(("xmm outside a routed load and outside fillers", l[:200]))
    return out, bad


def compile_check(ll, stem, td):
    """clang -O2 -S for x86-64, then assemble; returns (.s text, list of problems)"""
    probs = []
    lp = Path(td) / f"{stem}.ll"
    lp.write_text(ll)
    sp, op = lp.with_suffix(".s"), lp.with_suffix(".o")
    r = subprocess.run([CLANG, "--target=x86_64-unknown-linux-gnu", "-O2", "-S", str(lp), "-o", str(sp)], capture_output=True, text=True)
    if r.returncode:
        return "", [f"clang -S failed: {r.stderr[:500]}"]
    r = subprocess.run([CLANG, "--target=x86_64-unknown-linux-gnu", "-c", str(sp), "-o", str(op)], capture_output=True, text=True)
    if r.returncode:
        probs.append(f"assemble failed: {r.stderr[:500]}")
    s = sp.read_text()
    safe = stem.replace("-", "_").replace(".", "_")
    for lab in set(re.findall(rf"(__litmus_{safe}_pc\d+):", ll)):
        if f"{lab}:" not in s:
            probs.append(f"label {lab} missing in .s")
    return s, probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--sample20", required=True)
    ap.add_argument("--sample300", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "validate_fpralt.log", "w", buffering=1)

    def log(msg):
        line = f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
        logf.write(line + "\n")
        print(line, flush=True)

    fails = []

    def check(ok, what):
        if not ok:
            fails.append(what)
            log(f"FAIL {what}")
        return ok

    s20 = Path(a.sample20).read_text().split()
    s300 = Path(a.sample300).read_text().split()
    cA, cALT = jsonc(CFG_A), jsonc(CFG_ALT)
    # the new recipe differs from A only by fpr.p
    d = copy.deepcopy(cALT)
    d["fpr"].pop("p")
    check(d == cA, "stage2_final_A_fpralt.jsonc == stage2_final_A.jsonc apart from fpr.p")
    aA, aALT = stage2_args(cA), stage2_args(cALT)
    p_alt = cALT["fpr"]["p"]
    log(f"START src={src} n20={len(s20)} n300={len(s300)} p={p_alt} clang={CLANG} pristine={PRISTINE}")
    old, oldtd = load_pristine()
    summ = {"p": p_alt, "sample20": s20, "checks": {}}
    try:
        # ---- 1+2: default unchanged; p=0 == fpr off -------------------------------------------------------------
        n_same = n_corpus = n_p0 = 0
        a_off = dict(aA, fpr=None)
        a_p0 = dict(aA, fpr=dict(aA["fpr"], p=0.0))
        a_p1 = dict(aA, fpr=dict(aA["fpr"], p=1.0))
        for stem in s20:
            x = src / "xml" / f"{stem}.xml"
            for m in MODES:
                ll_new, ab_new, ann_new = gen(x, m, aA)
                ll_old, ab_old, _ = gen(x, m, aA, mod=old)
                if check(ll_new == ll_old and ab_new == ab_old, f"{stem} {m}: recipe A output differs from pristine"):
                    n_same += 1
                cann = json.loads((src / m / "ann" / f"{stem}.ann.json").read_text())
                if check(cann.get("fpr") == ann_new.get("fpr"), f"{stem} {m}: fpr block differs from the corpus ann"):
                    n_corpus += 1
                ll_off, _, _ = gen(x, m, a_off)
                ll_p0, _, ann_p0 = gen(x, m, a_p0)
                ll_p1, _, ann_p1 = gen(x, m, a_p1)
                ok = (ll_p0 == ll_off and not ann_p0["fpr"]["routes"] and ll_p1 == ll_new
                      and ann_p1["fpr"]["routes"] == ann_new["fpr"]["routes"]
                      and ann_p1["fpr"]["n_eligible"] == len(ann_new["fpr"]["routes"]) == ann_p0["fpr"]["n_eligible"])
                if check(ok, f"{stem} {m}: p=0 != fpr off, or p=1 != recipe A"):
                    n_p0 += 1
        tot = 2 * len(s20)
        summ["checks"]["default_identical_to_pristine"] = f"{n_same}/{tot}"
        summ["checks"]["fpr_block_equals_corpus_ann"] = f"{n_corpus}/{tot}"
        summ["checks"]["p0_equals_off_and_p1_equals_default"] = f"{n_p0}/{tot}"
        log(f"default identical to pristine {n_same}/{tot}; fpr block = corpus ann {n_corpus}/{tot}; p=0 == off and p=1 == A {n_p0}/{tot}")

        # ---- 3+4: new recipe on the 20, with compile ------------------------------------------------------------
        rows = []
        with tempfile.TemporaryDirectory(prefix="fpralt_cc_") as td:
            for stem in s20:
                x = src / "xml" / f"{stem}.xml"
                for m in MODES:
                    ll, ab, ann = gen(x, m, aALT)
                    f = ann["fpr"]
                    routes = f["routes"]
                    check(f.get("p") == p_alt and f["n_eligible"] >= len(routes), f"{stem} {m}: ann fpr block inconsistent")
                    kinds, bad = classify_xmm(ll, ann, stem)
                    for why, l in bad:
                        check(False, f"{stem} {m}: {why}: {l}")
                    s, probs = compile_check(ll, f"{stem}_{m}", td) if CLANG else ("", ["no clang"])
                    for pr in probs:
                        check(False, f"{stem} {m}: {pr}")
                    s_x = sorted({int(v) for v in XMM.findall(s)})
                    allowed = {r["xmm"] for r in routes} | {r["alu_xmm"] for r in routes if "alu_xmm" in r} | {14, 15}
                    check(set(s_x) <= allowed, f"{stem} {m}: .s uses xmm {s_x} outside routes/fillers {sorted(allowed)}")
                    if not routes:
                        check(set(s_x) <= {14, 15}, f"{stem} {m}: integer-only test has xmm {s_x} in .s")
                    rows.append({"stem": stem, "mode": m, "eligible": f["n_eligible"], "routed": len(routes),
                                 "routed_xmm": [r["xmm"] for r in routes], "ll_xmm_lines": dict(kinds), "s_xmm": s_x,
                                 "compiled": not probs})
                    log(f"{stem} {m}: eligible {f['n_eligible']} routed {len(routes)} xmm {[r['xmm'] for r in routes]} "
                        f".ll xmm lines {dict(kinds)} .s xmm {s_x} compile {'ok' if not probs else probs}")
        summ["sample20_rows"] = rows

        # ---- 3 at scale: fraction statistics over 300 stems x 2 modes (A and fpralt) ----------------------------
        agg = {}
        for name, cfg_a in (("A", aA), ("A_fpralt", aALT)):
            el = ro = tests = int_only = no_elig = xmm_free = 0
            per_reg = collections.Counter()
            xmm4_tests = 0
            for stem in s300:
                x = src / "xml" / f"{stem}.xml"
                for m in MODES:
                    ll, _, ann = gen(x, m, cfg_a)
                    routes = ann["fpr"]["routes"]
                    e = ann["fpr"].get("n_eligible")
                    if e is None:   # recipe A: every eligible load is routed
                        e = len(routes)
                    tests += 1
                    el += e
                    ro += len(routes)
                    no_elig += e == 0
                    int_only += not routes
                    xmm_free += "%xmm" not in ll
                    per_reg.update(r["xmm"] for r in routes)
                    xmm4_tests += any(r["xmm"] == 4 or r.get("alu_xmm") == 4 for r in routes)
            agg[name] = {"tests": tests, "eligible_loads": el, "routed_loads": ro,
                         "routed_fraction": round(ro / el, 4) if el else None,
                         "tests_without_eligible_load": no_elig, "tests_with_no_routed_load": int_only,
                         "tests_with_no_xmm_at_all": xmm_free, "tests_touching_xmm4_via_routing": xmm4_tests,
                         "routed_per_xmm": {str(k): per_reg[k] for k in sorted(per_reg)}}
            log(f"{name}: {json.dumps(agg[name])}")
        summ["sample300"] = agg
        alt = agg["A_fpralt"]
        if alt["eligible_loads"]:
            # binomial: |routed - p*n| within 4 sigma
            n = alt["eligible_loads"]
            sd = (n * p_alt * (1 - p_alt)) ** 0.5
            check(abs(alt["routed_loads"] - p_alt * n) <= 4 * sd + 1, f"routed fraction {alt['routed_fraction']} far from p={p_alt}")
        check(agg["A"]["routed_loads"] == agg["A"]["eligible_loads"], "recipe A must route every eligible load")
    except Exception:
        check(False, "exception\n" + traceback.format_exc())
    finally:
        old.reload_tables(None)
        P.reload_tables(None)
        shutil.rmtree(oldtd, ignore_errors=True)
    summ["fails"] = fails
    (out / "summary.json").write_text(json.dumps(summ, indent=1))
    log(f"END fails={len(fails)} summary={out / 'summary.json'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
