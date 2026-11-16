#!/usr/bin/env python3
"""shard_run.py -- run one whole testset (e.g. a GPR twin) as K parallel testrun.py --once processes over disjoint stem
shards and wait for them (regen-lp, 2026-11-10). Orchestration only (checker GIL-bound per process; see shard_eval.py).
Shard k: testset <model>__<tag><k> (symlinks to the model's asm/ann, both modes, round-robin over sorted stems),
config = <config> with ONLY paths.results_name -> <results_name>_<tag><k> and gem5.jobs -> --jobs, log
<loosepin_regen>/logs/eval_<results_name>_<tag><k>.log. Prints the result dir of every shard (pass them all to
bucket_eval.py --twin). Run from the eval code root. Usage: shard_run.py --config C --model M --k 8 --jobs 5 --tag sh [--wait]"""
import argparse, json, os, re, subprocess, time
from pathlib import Path
TS = Path("/tests/simspect_alloy_20261108/testsets_twostage"); LOGS = Path("/tests/simspect_alloy_20261108/loosepin_regen/logs")
MODES = ("mispredict_not_taken", "mispredict_taken")
ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--k", type=int, default=8); ap.add_argument("--jobs", type=int, default=5); ap.add_argument("--tag", default="sh")
ap.add_argument("--wait", action="store_true"); a = ap.parse_args()
src = open(a.config).read(); cfg = json.loads(re.sub(r"//[^\n]*", "", src)); rn = cfg["paths"]["results_name"]
wins = []
for k in range(a.k):
    tsn = f"{a.model}__{a.tag}{k}"; t = TS / tsn
    for m in MODES:
        for d in ("asm", "ann"):
            (t / m / d).mkdir(parents=True, exist_ok=True)
        stems = sorted(f[:-9] for f in os.listdir(TS / a.model / m / "ann"))[k::a.k]
        for s in stems:
            for d, e in (("asm", ".s"), ("ann", ".ann.json")):
                dst = t / m / d / f"{s}{e}"
                if not dst.exists():
                    os.symlink(TS / a.model / m / d / f"{s}{e}", dst)
    c = json.loads(json.dumps(cfg)); c["paths"]["results_name"] = f"{rn}_{a.tag}{k}"; c["gem5"]["jobs"] = a.jobs
    p = Path(a.config).with_name(f"{Path(a.config).stem}_{a.tag}{k}.jsonc")
    p.write_text(f"// shard {k}/{a.k} of {a.config} over {a.model} (shard_run.py): only results_name and gem5.jobs changed\n" + json.dumps(c, indent=2) + "\n")
    win = f"{rn}_{a.tag}{k}"; log = LOGS / f"eval_{win}.log"
    cmd = f"cd {os.getcwd()} && export TMPDIR=/tmp && python3 -u testrun.py --config {p} --model {tsn} --once --max-new 1000000 >> {log} 2>&1; echo EXIT rc=$? >> {log}"
    subprocess.run(["tmux", "new-window", "-d", "-t", "regenlp_eval", "-n", win, cmd], check=True)
    wins.append((win, log)); print(f"results/{win}__latest")
while a.wait and not all(l.exists() and "EXIT" in l.read_text() for _, l in wins):
    time.sleep(60)
