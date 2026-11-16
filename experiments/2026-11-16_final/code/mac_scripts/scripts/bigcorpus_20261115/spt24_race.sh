#!/usr/bin/env bash
# spt24_race.sh -- second race line on SPT-Fence (agent bigcorpus 2026-11-15): the 24 race stems behind the paper's "15 of 24" (bug-investigate-a5,
# cafe2 /tests/simspect_alloy_20261108/bugwork/a5/stems, from spt_slowcomm_fence__20260602_121858, SPT_6_oneLP corpus), rerun with TODAY's code
# (check_ld incl. the data-obtained gate) under the bigcorpus SPT race config (= overnight E11 gem5 block: freeParam=3, fnc stall 0, random_all
# cache setup; se_exp.py) at commitToIEWDelay 1 and 4, then race_scan.classify on the records. NOTE: the timing grid is a pipeline.py feature,
# not applied by a direct check_ld call, so the per-branch unresolved stall here is the check_ld default (gem5_common), stated in the output.
# Run on cafe2 inside gem5_dev from <OUT>/code: bash scripts/bigcorpus_20261115/spt24_race.sh   -> <OUT>/race/spt24_d{1,4}.{json,txt}
set -u
O=/tests/bigcorpus_20261115; S=/tests/simspect_alloy_20261108/bugwork/a5/stems; cd $O/code; mkdir -p $O/race; export TMPDIR=/tmp
for d in 1 4; do
  C=runconfigs/bigcorpus_20261115/race_sptfence_d${d}_STT_6_u_core_lpP_s2A.jsonc
  echo "[$(date -u +%FT%TZ)] START d=$d config=$C stems=$S"
  eval "$(python3 - "$C" <<'PY'
import sys, shlex; sys.path.insert(0, "."); import pipeline
from pathlib import Path; cfg = pipeline.load_config(Path(sys.argv[1])); env = pipeline._build_gem5_env(cfg["gem5"], cfg.get("speculation", {}))
import os
for k, v in env.items():
    if k.startswith("SIMSPECT_") and os.environ.get(k) != str(v): print(f"export {k}={shlex.quote(str(v))}")
print(f"export SIMSPECT_COMMIT_IEW_DELAY={cfg['race_knobs']['commitToIEWDelay']}")
PY
)"
  env | grep ^SIMSPECT_ | sort | sed 's/\x1f/ /g'
  python3 STAGE3_gem5/check_ld.py $S --jobs 12 --scheme 2 --out $O/race/spt24_d$d.json > $O/race/spt24_d${d}_checkld.log 2>&1
  python3 - $O/race/spt24_d$d.json <<'PY' | tee $O/race/spt24_d$d.txt
import json, sys, collections; sys.path.insert(0, "scripts/bigcorpus_20261115"); import race_scan as rs
recs = json.load(open(sys.argv[1])); c = collections.Counter(rs.classify(r) for r in recs)
print(sys.argv[1], dict(c), "race", c["race"], "of", len(recs))
print("wp_obtained", sum(rs.wp_obtained(r) for r in recs))
for r in recs:
    print(r["name"], rs.classify(r), "wp_obtained" if rs.wp_obtained(r) else "-", r.get("cache_fate"), r.get("issued_in_window"))
PY
  echo "[$(date -u +%FT%TZ)] END d=$d"
done
