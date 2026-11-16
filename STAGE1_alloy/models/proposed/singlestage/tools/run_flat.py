#!/usr/bin/env python3
"""run_flat.py — enumerate ONE flat (single-stage) Alloy model under several solver orders, with a careful log.

Runs inside the gem5_dev container on a cafe node. For each entry of --seeds ("default" = a6CountModels' stock
SAT4J order; an integer = a6RandomModels with that seed, random phase + random walk p=--p) it writes
  <out>/<seed>/inst-NNNNNN.{xml,txt}   + _java_stdout.txt / _java_stderr.txt
  <out>/runs.jsonl                     one line per finished run: seed, instances, verdict, secs, command
  <out>/run_flat.log                   start/end, model sha256, scope line, every command, every error
Verdicts: EXHAUSTED (solver reached UNSAT below the cap), CAPPED, TIMEOUT, ERROR. A finished seed is skipped on rerun.
Refuses to start if check_bound_consistency.py fails on the model, or free disk < --min-disk-gb.
Usage: run_flat.py --model M.als --out DIR --alloy-dir <dir with alloy6.jar + a6CountModels.class>
                   --classes <dir with a6RandomModels.class> [--seeds default,1,2] [--cap 20000] [--timeout 1800] [--jobs 3]
"""
import argparse, datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).resolve().parent
now = lambda: dt.datetime.now().astimezone().isoformat(timespec="seconds")
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--alloy-dir", required=True); ap.add_argument("--classes", required=True)
ap.add_argument("--seeds", default="default,1,2"); ap.add_argument("--cap", type=int, default=20000)
ap.add_argument("--timeout", type=int, default=1800); ap.add_argument("--jobs", type=int, default=3)
ap.add_argument("--p", default="0.05"); ap.add_argument("--xmx", default="4g"); ap.add_argument("--min-disk-gb", type=float, default=60)
a = ap.parse_args()
model, out = Path(a.model).resolve(), Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
log = open(out / "run_flat.log", "a", buffering=1)
L = lambda m: (log.write(f"{now()} {m}\n"), print(m, flush=True))
text = model.read_text()
scope = re.search(r"\}\s*(for [^\n]*Instruction[^\n]*)", text)
L(f"START pid={os.getpid()} host={os.uname().nodename} model={model} sha256={hashlib.sha256(text.encode()).hexdigest()} "
  f"scope='{scope.group(1) if scope else '?'}' seeds={a.seeds} cap={a.cap} timeout={a.timeout} jobs={a.jobs} p={a.p}")
lint = subprocess.run([sys.executable, str(HERE / "check_bound_consistency.py"), str(model)], capture_output=True, text=True)
L("LINT " + lint.stdout.strip())
if lint.returncode != 0:
    L("REFUSING: bound-consistency lint failed"); sys.exit(2)
if shutil.disk_usage(out).free / 1e9 < a.min_disk_gb:
    L("REFUSING: free disk below --min-disk-gb"); sys.exit(3)
done = set()
if (out / "runs.jsonl").exists():
    done = {json.loads(l)["seed"] for l in (out / "runs.jsonl").read_text().splitlines() if l.strip()}
def run(seed):
    d = out / seed
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    if seed == "default":
        cmd = ["java", f"-Xmx{a.xmx}", "-cp", "alloy6.jar:.", "a6CountModels", str(model), str(d), str(a.cap)]
    else:
        cmd = ["java", f"-Xmx{a.xmx}", "-cp", f"alloy6.jar:{a.classes}", "a6RandomModels", str(model), str(d), str(a.cap), seed, a.p]
    L(f"RUN seed={seed} $ {' '.join(cmd)}")
    t0 = time.time(); timed_out = False; rc = None
    try:
        with open(d / "_java_stdout.txt", "w") as so, open(d / "_java_stderr.txt", "w") as se:
            p = subprocess.Popen(cmd, cwd=a.alloy_dir, stdout=so, stderr=se)
            try: rc = p.wait(timeout=a.timeout)
            except subprocess.TimeoutExpired:
                p.kill(); rc = p.wait(); timed_out = True
        n = sum(1 for _ in d.glob("inst-*.xml"))
        so_t = (d / "_java_stdout.txt").read_text(errors="replace")
        # a6CountModels logs every 'solving' line to stdout: keep only the tail
        (d / "_java_stdout.txt").write_text("\n".join(so_t.splitlines()[-40:]) + "\n")
        verdict = "TIMEOUT" if timed_out else "ERROR" if rc != 0 else "CAPPED" if n >= a.cap else "EXHAUSTED" if "Total models:" in so_t else "UNKNOWN"
        if verdict in ("ERROR", "UNKNOWN"):
            L(f"{verdict} seed={seed} rc={rc} stderr tail:\n" + "\n".join((d / "_java_stderr.txt").read_text(errors="replace").splitlines()[-25:]))
    except Exception:
        import traceback
        n, verdict = 0, "ERROR"; L(f"EXCEPTION seed={seed}\n{traceback.format_exc()}")
    rec = {"seed": seed, "instances": n, "verdict": verdict, "rc": rc, "secs": int(time.time() - t0), "cmd": " ".join(cmd), "ended": now()}
    with open(out / "runs.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    L(f"DONE seed={seed} instances={n} verdict={verdict} secs={rec['secs']}")
seeds = [s for s in a.seeds.split(",") if s and s not in done]
with ThreadPoolExecutor(a.jobs) as ex: list(ex.map(run, seeds))
L("END")
