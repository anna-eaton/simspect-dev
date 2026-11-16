#!/usr/bin/env python3
"""rsa8_trace.py -- check the R-SA-8 signature ('release at the older source's commit', e2-losttaint) for branch-transmitter
hits, one faithful rerun per (mode, stem) with extra debug flags Commit,DelayUnit,Rename (regen-lp, 2026-11-10).
Signature (all from the rerun's pipeview/debug trace): the transmitter branch (the ann xmit pc) is inserted into the
delay unit as tainted, is released ("no longer tainted") BEFORE the window branch's held resolve fires (the resolve_hold
line with mispred=1; latest fire tick), and resolves mispredicted (resolve_visible mispred=1) before that fire tick. Anything else -> not R-SA-8.
Testset = the twin (or corpus) holding the stem; config = the row's twin config with paths/keep_tmp/jobs/modes changed.
Run from the eval code root. Usage: rsa8_trace.py --config C --testset-dirs T1 [T2 ...] --keys keys.txt --out out.json [--par 8]"""
import argparse, concurrent.futures as cf, glob, gzip, json, os, re, shutil, subprocess, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--testset-dirs", nargs="+", required=True)
ap.add_argument("--keys", required=True); ap.add_argument("--out", required=True); ap.add_argument("--par", type=int, default=8)
ap.add_argument("--work", default="/tests/simspect_alloy_20261108/loosepin_regen/bugwork/rsa8"); a = ap.parse_args()
cfg0 = json.loads(re.sub(r"//[^\n]*", "", open(a.config).read())); W = Path(a.work); W.mkdir(parents=True, exist_ok=True)
keys = [tuple(l.strip().split("/", 1)) for l in open(a.keys) if l.strip()]

def one(k):
    mode, s = k; tag = f"{mode[11:]}_{s}"
    src = next((Path(t) for t in a.testset_dirs if (Path(t) / mode / "ann" / f"{s}.ann.json").exists()), None)
    if src is None:
        return k, {"error": "stem not in any testset"}
    ts = W / tag / "ts" / "X" / mode
    shutil.rmtree(W / tag, ignore_errors=True)
    for d, e in (("asm", ".s"), ("ann", ".ann.json")):
        (ts / d).mkdir(parents=True); os.symlink(src / mode / d / f"{s}{e}", ts / d / f"{s}{e}")
    c = json.loads(json.dumps(cfg0)); c["paths"].update(testset_dir=str(W / tag / "ts"), results_dir=str(W / tag / "res"), results_name="rr")
    c.setdefault("pipeline", {})["keep_tmp"] = True; c["gem5"]["jobs"] = 1; c["gem5"].pop("sample_fraction", None)
    c["speculation"]["branch_modes"] = [mode]; c["gem5"]["debug_flags"] = list(c["gem5"]["debug_flags"]) + ["Commit", "DelayUnit", "Rename"]
    (W / tag / "cfg.json").write_text(json.dumps(c)); tmp = Path(f"/tmp/r8_{tag}"); shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    subprocess.run([sys.executable, "pipeline.py", "gem5", "--model", "X", "--config", str(W / tag / "cfg.json"), "--force"],
                   env=dict(os.environ, TMPDIR=str(tmp)), stdout=open(W / tag / "pipeline.log", "w"), stderr=subprocess.STDOUT)
    pv = next(iter(glob.glob(f"{tmp}/**/pipeview.txt", recursive=True)), None)
    if pv is None:
        shutil.rmtree(tmp, ignore_errors=True); return k, {"error": "no trace"}
    ann = json.load(open(src / mode / "ann" / f"{s}.ann.json")); xpc = ann["xmit"].get("addr")
    lines = [l for l in open(pv, errors="replace") if re.search(r"delay_unit|resolve_(hold|release|visible)", l)]
    with gzip.open(W / tag / "trace_excerpt.txt.gz", "wt") as f:
        f.writelines(lines)
    shutil.rmtree(tmp, ignore_errors=True)
    hold = [l for l in lines if "resolve_hold" in l and "mispred=1" in l]   # the held, mispredicted window branch
    fire = max((int(re.search(r"fire=(\d+)", l).group(1)) for l in hold), default=None)
    xv = [l for l in lines if "resolve_visible" in l and f"pc={hex(xpc)}:" in l and "mispred=1" in l]
    xtick = min((int(l.split(":")[2]) for l in xv), default=None)
    ins = [l for l in lines if "Inserting branch" in l]; rel = [l for l in lines if "Released tainted branch" in l]
    rtick = min((int(l.split(":")[0]) for l in rel), default=None)
    ok = bool(ins) and rtick is not None and fire is not None and xtick is not None and rtick < fire and xtick < fire
    return k, dict(xmit_pc=hex(xpc), hold_fire=fire, xmit_mispred_resolve=xtick, first_release=rtick, n_inserted=len(ins),
                   rsa8_signature=ok, trace=str(W / tag / "trace_excerpt.txt.gz"))

res = json.loads(Path(a.out).read_text()) if Path(a.out).exists() else {}
with cf.ThreadPoolExecutor(a.par) as ex:
    for k, r in ex.map(one, [k for k in keys if f"{k[0]}/{k[1]}" not in res]):
        res[f"{k[0]}/{k[1]}"] = r; print(f"{k[0]}/{k[1]}", r.get("rsa8_signature"), r.get("error", ""), flush=True)
Path(a.out).write_text(json.dumps(res, indent=1))
print(sum(1 for v in res.values() if v.get("rsa8_signature")), "of", len(res), "carry the R-SA-8 signature")
