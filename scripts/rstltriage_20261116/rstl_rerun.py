#!/usr/bin/env python3
"""rstl_rerun.py -- faithful traced reruns of E2w-stl hits (agent rstltriage, 2026-11-16).

Re-runs single tests EXACTLY as the row did: `pipeline.py gem5` from the row's code snapshot with the row's config
(runconfigs/reconstl_20261116/E2wstl_Recon_6_u_stl_core_lpP_s2A.jsonc; same binary, scheme, store hold, alias prediction,
timing-grid seed), changing ONLY paths, jobs=1, keep_tmp=true, and extra debug flags (Commit, DelayUnit, Rename, IEW; debug flags
do not change timing). Keeps per key: the full checker record (sweep raw json), the gzipped full trace, the stats.txt lines about
taint/reveal/delay, the pipeline log. Analysis is separate (rstl_analyze.py), so signatures can change without rerunning gem5.
Keys file lines: <tag> <testset_dir> <stem>   (tag = main|twin; testset_dir holds stl_bypass/{asm,ann}).
Run in gem5_dev from the row's code root: python3 rstl_rerun.py --config C --keys K --work W [--par 8]
Log: <W>/rerun.log (start/end, per key ok/error with the pipeline log tail)."""
import argparse, concurrent.futures as cf, glob, gzip, json, os, re, shutil, subprocess, sys, time, traceback
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--keys", required=True)
ap.add_argument("--work", required=True); ap.add_argument("--par", type=int, default=8)
ap.add_argument("--flags", default="Commit,DelayUnit,Rename,IEW"); a = ap.parse_args()
W = Path(a.work); W.mkdir(parents=True, exist_ok=True); LOG = open(W / "rerun.log", "a")
def log(m):
    LOG.write(f"[{time.strftime('%F %T', time.gmtime())}] {m}\n"); LOG.flush(); print(m, flush=True)
cfg0 = json.loads(re.sub(r"//[^\n]*", "", open(a.config).read())); MODE = "stl_bypass"
keys = [l.split() for l in open(a.keys) if l.strip() and not l.startswith("#")]

def one(k):
    tag, tsd, s = k; d = W / f"{tag}_{s}"
    try:
        shutil.rmtree(d, ignore_errors=True)
        ts = d / "ts" / "X" / MODE
        for sub, e in (("asm", ".s"), ("ann", ".ann.json")):
            (ts / sub).mkdir(parents=True); shutil.copy(f"{tsd}/{MODE}/{sub}/{s}{e}", ts / sub / f"{s}{e}")
        c = json.loads(json.dumps(cfg0)); c["paths"].update(testset_dir=str(d / "ts"), results_dir=str(d / "res"), results_name="rr")
        c["pipeline"]["keep_tmp"] = True; c["gem5"]["jobs"] = 1
        c["gem5"]["debug_flags"] = list(c["gem5"]["debug_flags"]) + [f for f in a.flags.split(",") if f not in c["gem5"]["debug_flags"]]
        (d / "cfg.json").write_text(json.dumps(c, indent=1)); tmp = d / "tmp"; tmp.mkdir()
        p = subprocess.run([sys.executable, "pipeline.py", "gem5", "--model", "X", "--config", str(d / "cfg.json"), "--force"],
                           env=dict(os.environ, TMPDIR=str(tmp)), stdout=open(d / "pipeline.log", "w"), stderr=subprocess.STDOUT)
        pv = next(iter(glob.glob(f"{tmp}/**/pipeview.txt", recursive=True)), None)
        raw = sorted(glob.glob(f"{d}/res/**/sweep/**/*.json", recursive=True)) + sorted(glob.glob(f"{d}/res/**/batch_*results.json", recursive=True))
        rec = None
        for f in raw:
            x = json.load(open(f)); xs = x if isinstance(x, list) else x.get("results", [])
            rec = next((r for r in xs if isinstance(r, dict) and r.get("name", "").split("__")[0] == s), rec)
        out = dict(tag=tag, stem=s, rc=p.returncode, record=rec)
        if pv:
            with open(pv, "rb") as fi, gzip.open(d / "trace.txt.gz", "wb") as fo:
                shutil.copyfileobj(fi, fo)
            st = Path(pv).parent / "stats.txt"
            if st.exists():
                out["stats"] = [l.rstrip() for l in open(st) if re.search(r"reveal|taint|delay_unit|shadow_tracker|Leaked|stlForw", l, re.I)][:200]
        else:
            out["error"] = "no trace"
        (d / "result.json").write_text(json.dumps(out, indent=1)); shutil.rmtree(tmp, ignore_errors=True)
        return k, ("ok" if pv and rec else "error: " + ("no trace" if not pv else "no record") + " | " + open(d / "pipeline.log").read()[-300:])
    except Exception:
        return k, "error: " + traceback.format_exc()[-800:]

log(f"START keys={len(keys)} config={a.config} flags={a.flags} cwd={os.getcwd()}")
with cf.ThreadPoolExecutor(a.par) as ex:
    for k, r in ex.map(one, keys):
        log(f"{k[0]} {k[2]} {r}")
log("END")
