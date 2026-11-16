#!/bin/bash
# testcost (agent testcost, 2026-11-16): prototype fast path vs unpatched production functions, same process,
# same 20 tests per build (A/B per test, interleaved, so node load hits both alike). Waits for run_profile.sh.
# Usage (inside the container): bash run_fast.sh [N=20]
set -u
N=${1:-20}; B=/tests/testcost_20261116; T=/tests/timing_20261115; C=$T/code; MODEL=Footprint_6_u_core_lpP_s2A
exec > >(tee -a $B/logs/run_fast.log) 2>&1
while pgrep -f run_profile.sh > /dev/null; do sleep 20; done
echo "=== fast START $(date -u '+%F %T') uptime: $(uptime)"
export TMPDIR=/tmp
for R in T1g T2g T3g; do
  nice -n 19 python3 $B/fast_worker.py --code-root $C --config $T/configs/${R}_time1.jsonc \
    --testset-model $T/testsets/$MODEL --sample $B/sample_n$N.tsv --n $N --out $B/fast_$R --compare-orig \
    > $B/logs/fast_$R.out 2>&1 || echo "fast $R rc=$?"
done
echo "=== fast END $(date -u '+%F %T') uptime: $(uptime)"
