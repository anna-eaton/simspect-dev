set -u
cd /tmp/anonchk/code
export WORK=/tmp/anonchk/work GEM5_ROOT=/work/amulet TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900
for R in T1g T2g T3g; do
  python3 - $R <<'PY'
import json, os, sys
r = sys.argv[1]
t = open(f"runconfigs/timing/{r}.json").read().replace("@WORK@", os.environ["WORK"]).replace("@GEM5@", os.environ["GEM5_ROOT"])
os.makedirs("/tmp/anonchk/cfg", exist_ok=True)
open(f"/tmp/anonchk/cfg/{r}.json", "w").write(t)
PY
  nice -n 19 python3 STAGE3_gem5/timing/firstdet_stream.py --code-root /tmp/anonchk/code --config /tmp/anonchk/cfg/$R.json \
     --model Footprint_6_u_core_lpP_s2A --out /tmp/anonchk/out/$R --seed 20261109 --parallel 4 --only-file /tmp/anonchk/s20.tsv \
     --n-max 20 --poll 10 > /tmp/anonchk/$R.stdout 2>&1
  echo "$R rc=$? rows=$(wc -l < /tmp/anonchk/out/$R/results.jsonl)"
done
