#!/usr/bin/env python3
"""shard_run.py (agent sptrace 2026-11-16) -- run the race rows K-way parallel over disjoint stem shards (testrun/check_ld is GIL-bound:
one campaign uses ~1 core; same idea as scripts/bigcorpus_20261115/shard_rows.py). Checker, gem5_common, testrun.py unchanged.
For each delay d and mode: stems = the corpus stems (testsets/<T>/<mode>/ann) MINUS those already in the main campaign
results/sptrace_fence_d<d>_<T>__latest/<mode>/_sweep_raw (the first unsharded passes), sorted, dealt round-robin into K shards.
Shard s: testset testsets/<T>__d<d>_sh<s>/<mode>/{asm,ann} (symlinks), config runconfigs/sptrace_20261116/shards/race_sptfence_d<d>_<T>_sh<s>.jsonc
= the row config with ONLY paths.results_name (+ _sh<s>) and gem5.jobs (--jobs) changed; tmux window in session sptrace_sh running
`SIMSPECT_COMMIT_IEW_DELAY=<d> testrun.py --config <cfg> --model <shard ts> --once --max-new 100000` (log logs/shard_d<d>_sh<s>.log; on exit
writes logs/shard_d<d>_sh<s>.DONE with rc). merge.py builds the merged per-delay view for race_scan.
Usage (code root, gem5_dev): shard_run.py --delays 1,4 --k 14 --jobs 3 [--nice 5] [--dry]
"""
import argparse, glob, json, os, re, subprocess
from pathlib import Path
O = Path("/tests/sptrace_20261116"); T = "SPT_6_oneLP_v2_flat_ld_s2Aspt"; TS = O / "testsets"; MODES = ("mispredict_not_taken", "mispredict_taken")
R = "runconfigs/sptrace_20261116"


def done_stems(d, mode):
    s = set()
    for f in glob.glob(f"results/sptrace_fence_d{d}_{T}__latest/{mode}/_sweep_raw/*.json"):
        for r in json.load(open(f)):
            if isinstance(r, dict) and r.get("name"):
                s.add(r["name"].split("__")[0])
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--delays", required=True); ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--nice", type=int, default=5); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(); Path(f"{R}/shards").mkdir(parents=True, exist_ok=True); (O / "logs").mkdir(exist_ok=True)
    if not a.dry:
        subprocess.run("tmux has-session -t sptrace_sh 2>/dev/null || tmux new-session -d -s sptrace_sh -n ctl", shell=True)
    for d in [int(x) for x in a.delays.split(",")]:
        base = Path(f"{R}/race_sptfence_d{d}_{T}.jsonc").read_text()
        rest = {m: sorted({f[:-9] for f in os.listdir(TS / T / m / "ann")} - done_stems(d, m)) for m in MODES}
        print(f"d{d}: remaining " + " ".join(f"{m}={len(v)}" for m, v in rest.items()))
        for s in range(a.k):
            tsn = f"{T}__d{d}_sh{s}"; n = 0
            for m in MODES:
                for sub, ext in (("asm", ".s"), ("ann", ".ann.json")):
                    dd = TS / tsn / m / sub; dd.mkdir(parents=True, exist_ok=True)
                    for st in rest[m][s::a.k]:
                        l = dd / f"{st}{ext}"
                        if not l.exists():
                            l.symlink_to(TS / T / m / sub / f"{st}{ext}")
                n += len(rest[m][s::a.k])
            (TS / tsn / "READY").touch()
            name = f"sptrace_fence_d{d}_{T}_sh{s}"
            c = base.replace(f'"results_name": "sptrace_fence_d{d}_{T}"', f'"results_name": "{name}"')
            c = re.sub(r'"jobs": \d+', f'"jobs": {a.jobs}', c, count=1)
            assert name in c
            cfg = f"{R}/shards/race_sptfence_d{d}_{T}_sh{s}.jsonc"
            Path(cfg).write_text(f"// shard {s}/{a.k} of {R}/race_sptfence_d{d}_{T}.jsonc (shard_run.py): only results_name and gem5.jobs changed\n" + c)
            log = O / "logs" / f"shard_d{d}_sh{s}.log"
            cmd = (f"cd {O}/code && export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=300 SIMSPECT_GEM5_MAX_TICK=2000000000 SIMSPECT_COMMIT_IEW_DELAY={d} && echo START $(date -u) >> {log} && "
                   f"nice -n {a.nice} python3 -u testrun.py --config {cfg} --model {tsn} --once --max-new 100000 >> {log} 2>&1; "
                   f"echo rc=$? $(date -u) > {O}/logs/shard_d{d}_sh{s}.DONE")
            print(f"  sh{s}: {n} tests -> {name}")
            if not a.dry:
                subprocess.run(["tmux", "new-window", "-d", "-t", "sptrace_sh", "-n", f"d{d}s{s}", cmd], check=True)


if __name__ == "__main__":
    main()
