#!/usr/bin/env python3
"""TIME-1 (agent timing, 2026-11-15): re-time a sample of big-corpus Stage 1.5 (Stage 1b) Alloy jobs on a dedicated node.

Why: the big corpus PROVENANCE.json reports Stage 1.5 cost as the SUM OF PER-JOB WALL SECONDS on cafe3, which ran at load
~160-220 on 64 logical CPUs, so it overstates the CPU cost by an unknown factor. Here the same (core, seed) jobs are
re-run with the same code path (stage15lp.run_job -> alloy_solver_order.run_random_xml -> a6RandomModels, same model file,
seed, cap, timeout, walk_p, xmx), PARALLEL at once, each in its own child process reaped with os.wait4, so the CPU-s
(user+sys of the child and every JVM under it, GC threads included) is measured directly. A seeded a6RandomModels run
is deterministic, so instance counts can be compared with the cafe3 jobs.jsonl row.

Usage (cafe2 gem5_dev):
  python3 gen_retime.py --code <code root> --models <dir with <core>.als> --jobs-jsonl <cafe3 jobs.jsonl copy> \
      --n 16 --sample-seed 20261115 --parallel 16 --timeout 600 --cap 100 --walk-p 0.05 --xmx 4g --out <dir>
Writes <out>/retime.jsonl (one row per job: core, seed, cafe3 secs/instances/kept, here wall/cpu/instances/verdict),
<out>/retime.log, <out>/summary.json.
"""
import argparse, json, os, random, subprocess, sys, time, traceback, concurrent.futures as cf
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--stage15", required=True, help="path of stage15lp.py (for run_job)")
ap.add_argument("--models", required=True)
ap.add_argument("--jobs-jsonl", required=True)
ap.add_argument("--n", type=int, default=16)
ap.add_argument("--sample-seed", type=int, default=20261115)
ap.add_argument("--parallel", type=int, default=16)
ap.add_argument("--timeout", type=int, default=600)
ap.add_argument("--cap", type=int, default=100)
ap.add_argument("--walk-p", type=float, default=0.05)
ap.add_argument("--xmx", default="4g")
ap.add_argument("--out", required=True)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
logf = open(out / "retime.log", "a")


def log(m):
    logf.write(f"{time.strftime('%F %T', time.gmtime())} {m}\n"); logf.flush()


rows = [json.loads(l) for l in open(a.jobs_jsonl) if l.strip()]
rows = [r for r in rows if not r.get("error") and isinstance(r.get("seed"), int)
        and (Path(a.models) / f"{r['core']}.als").exists()]
pick = random.Random(a.sample_seed).sample(rows, a.n)
log(f"START n={a.n} parallel={a.parallel} from {len(rows)} eligible cafe3 jobs; sample seed {a.sample_seed}; loadavg {os.getloadavg()}")

CHILD = r'''
import sys, json, importlib.util
spec = importlib.util.spec_from_file_location("s15", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r = m.run_job(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), float(sys.argv[8]), sys.argv[9])
print("RESULT " + json.dumps({"rec": r.get("rec"), "error": r.get("error"), "kept": len(r.get("fps") or [])}))
'''


def one(r):
    xd = out / "jobs" / r["core"] / f"s{r['seed']}" / "xml"
    if xd.exists():
        import shutil; shutil.rmtree(xd)
    t0 = time.monotonic()
    p = subprocess.Popen([sys.executable, "-c", CHILD, a.stage15, a.code, str(Path(a.models) / f"{r['core']}.als"), str(xd),
                          str(r["seed"]), str(a.timeout), str(a.cap), str(a.walk_p), a.xmx],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    so = p.stdout.read()
    _, sts, ru = os.wait4(p.pid, 0)
    wall = time.monotonic() - t0
    res = {}
    for l in so.splitlines():
        if l.startswith("RESULT "):
            res = json.loads(l[7:])
    sd = ((res.get("rec") or {}).get("seeds") or [{}])[0]
    row = dict(core=r["core"], seed=r["seed"], cafe3_secs=r.get("secs"), cafe3_instances=r.get("instances"), cafe3_kept=r.get("kept"),
               cafe3_verdict=r.get("verdict"), wall_s=round(wall, 2), cpu_s=round(ru.ru_utime + ru.ru_stime, 2),
               cpu_user=round(ru.ru_utime, 2), cpu_sys=round(ru.ru_stime, 2), instances=sd.get("instances"), kept=res.get("kept"),
               verdict=sd.get("verdict"), solver_secs=sd.get("secs"), rc=os.waitstatus_to_exitcode(sts), error=res.get("error"),
               tail=None if res else so[-2000:])
    return row


with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex, open(out / "retime.jsonl", "a") as fo:
    for f in cf.as_completed([ex.submit(one, r) for r in pick]):
        try:
            row = f.result()
            fo.write(json.dumps(row) + "\n"); fo.flush()
            log(f"DONE {row['core']} s{row['seed']} wall={row['wall_s']} cpu={row['cpu_s']} inst={row['instances']} kept={row['kept']} "
                f"verdict={row['verdict']} | cafe3 secs={row['cafe3_secs']} inst={row['cafe3_instances']} rc={row['rc']}"
                + (f" ERROR {row['error'][-300:]}" if row.get("error") else "") + (f" TAIL {row['tail'][-300:]}" if row.get("tail") else ""))
        except Exception:
            log("ERROR " + traceback.format_exc())
rows = [json.loads(l) for l in open(out / "retime.jsonl")]
ok = [r for r in rows if r["kept"]]
s = dict(n=len(rows), ok=len(ok), cpu_sum=sum(r["cpu_s"] for r in rows), wall_sum=sum(r["wall_s"] for r in rows),
         cafe3_secs_sum=sum(r["cafe3_secs"] or 0 for r in rows), kept_sum=sum(r["kept"] or 0 for r in rows),
         cafe3_kept_sum=sum(r["cafe3_kept"] or 0 for r in rows))
s["cpu_per_kept_program"] = s["cpu_sum"] / s["kept_sum"] if s["kept_sum"] else None
s["cafe3_wall_per_kept_program"] = s["cafe3_secs_sum"] / s["cafe3_kept_sum"] if s["cafe3_kept_sum"] else None
s["ratio_cpu_here_to_cafe3_wall"] = s["cpu_sum"] / s["cafe3_secs_sum"] if s["cafe3_secs_sum"] else None
json.dump(s, open(out / "summary.json", "w"), indent=1)
log(f"END {json.dumps(s)} loadavg {os.getloadavg()}")
print(json.dumps(s, indent=1))
