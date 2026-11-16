#!/usr/bin/env python3
"""merge.py (agent sptrace 2026-11-16) -- merged per-delay campaign view for race_scan: results/sptrace_fence_d<d>_<T>_merged/<mode>/_sweep_raw/
= symlinks to every _sweep_raw/*.json of the main campaign and of all its shards (_sh*). Reports duplicate stems (must be 0).
Usage (code root): merge.py 1 4 [3]"""
import glob, json, os, sys
T = "SPT_6_oneLP_v2_flat_ld_s2Aspt"
for d in sys.argv[1:]:
    out = f"results/sptrace_fence_d{d}_{T}_merged"
    for m in ("mispredict_not_taken", "mispredict_taken"):
        od = f"{out}/{m}/_sweep_raw"; os.makedirs(od, exist_ok=True)
        for f in glob.glob(f"{od}/*"):
            os.unlink(f)
        seen, dup, k = set(), 0, 0
        for camp in [f"results/sptrace_fence_d{d}_{T}__latest"] + sorted(glob.glob(f"results/sptrace_fence_d{d}_{T}_sh*__latest")):
            for f in sorted(glob.glob(f"{camp}/{m}/_sweep_raw/*.json")):
                try:
                    recs = json.load(open(f))
                except Exception as e:
                    print("WARN", f, e); continue
                for r in recs:
                    n = r.get("name") if isinstance(r, dict) else None
                    if n:
                        dup += n in seen; seen.add(n)
                k += 1; os.symlink(os.path.realpath(f), f"{od}/{k:05d}_{os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f))))}.json")
        print(f"d{d} {m}: {len(seen)} stems from {k} files, duplicates {dup}")
