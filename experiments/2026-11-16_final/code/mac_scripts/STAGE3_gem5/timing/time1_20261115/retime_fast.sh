#!/bin/bash
# retime_fast.sh (agent fastpath, 2026-11-16): TC-4, re-time the SimSpect half of TIME-1 with the opt-in fast path.
# Same harness as run_simspect.sh (firstdet_stream.py -> timing_driver.run_one, the TIME-1 1,000-pair sample, the TIME-1
# configs, 16 workers pinned to CPUs 0-31 = one hardware thread per physical core), run TWICE per row back to back on the
# same idle node: first the production path (config unchanged), then the fast path (the same config + gem5.fast_path: true).
# Both use the code tree in $CODE (must contain the fast path: Anna runs `make sync`, then `git pull` on the node).
# Then retime_fast_summary.py compares them per row and cache setup, and checks every verdict against TIME-1's stored rows.
#
# Usage (inside gem5_dev on an IDLE node that has /tests/timing_20261115 = cafe2):
#   CODE=/tests/simspect bash retime_fast.sh [rows="T1g T2g T3g"] [parallel=16]
# Outputs: /tests/timing_20261115/simspect/<row>_p16_prod2/ and <row>_p16_fast/ (results.jsonl, driver.log, fastpath_logs/),
#          /tests/timing_20261115/retime_fast/{retime.log,summary.json,summary.md}
set -u
ROWS=${1:-"T1g T2g T3g"}; P=${2:-16}
B=/tests/timing_20261115; C=${CODE:-/tests/simspect}; MODEL=Footprint_6_u_core_lpP_s2A
SEL="--only-file $B/sample/sample.tsv --n-max 1000"
mkdir -p $B/retime_fast
exec > >(tee -a $B/retime_fast/retime.log) 2>&1
echo "=== retime_fast START $(date -u '+%F %T') rows=[$ROWS] parallel=$P code=$C uptime: $(uptime)"
test -f $C/STAGE3_gem5/gem5_fastpath.py || { echo "ERROR: $C has no STAGE3_gem5/gem5_fastpath.py (sync + pull first)"; exit 2; }
export TMPDIR=/tmp
for R in $ROWS; do
  CFG=$B/configs/${R}_time1.jsonc; FCFG=$B/configs/${R}_time1_fast.jsonc
  python3 - "$CFG" "$FCFG" <<'PY'
import json, re, sys
src, dst = sys.argv[1:3]
txt = re.sub(r"/\*.*?\*/", "", open(src).read(), flags=re.S)
cfg = json.loads(re.sub(r"//[^\n]*", "", txt))
cfg["gem5"]["fast_path"] = True          # the only change
open(dst, "w").write(json.dumps(cfg, indent=1) + "\n")
PY
  for V in prod2 fast; do
    OUT=$B/simspect/${R}_p${P}_$V; USE=$CFG; [ $V = fast ] && USE=$FCFG
    if [ -s $OUT/results.jsonl ] && [ "$(wc -l < $OUT/results.jsonl)" -ge 1000 ]; then echo "--- $R $V already done"; continue; fi
    mkdir -p $OUT
    bash $B/scripts/snap.sh "before $R $V"
    echo "--- $R $V START $(date -u '+%F %T') config=$USE out=$OUT"
    (cd $C && taskset -c 0-31 python3 STAGE3_gem5/timing/firstdet_stream.py --code-root $C --config $USE \
        --model $MODEL --out $OUT --seed 20261109 --parallel $P $SEL --poll 30 > $OUT/stream.stdout 2>&1)
    echo "--- $R $V END $(date -u '+%F %T') rc=$? rows=$(wc -l < $OUT/results.jsonl)"
    bash $B/scripts/snap.sh "after $R $V"
  done
done
python3 $C/STAGE3_gem5/timing/time1_20261115/retime_fast_summary.py $B --rows "$ROWS" --parallel $P \
    --json $B/retime_fast/summary.json --md $B/retime_fast/summary.md
echo "=== retime_fast END $(date -u '+%F %T') rc=$? uptime: $(uptime)"
