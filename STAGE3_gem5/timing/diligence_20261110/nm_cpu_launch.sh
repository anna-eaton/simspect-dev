#!/bin/bash
# nm-diligence 2026-11-10: dedicated-node CPU per test on the NON-MINIMAL corpus, same method as diligence DG-1
# (EVAL_MANIFEST part 8 check 6): first 1,000 tests of the seed-20261109 order per defense, T1g/T2g/T3g nonmin configs,
# 3 rows x 2 workers on an otherwise idle cafe1, TMPDIR=/tmp. Log: $W/cpu/run.log; PIDs: $W/cpu/<row>.pid
set -u
B=/tests/simspect_alloy_20261108; W=$B/bugwork/nm_diligence; C=$B/nonmin/firstdet/code; M=Footprint_6_u_core_lpN_fv3
export TMPDIR=/tmp
mkdir -p $W/cpu
echo "$(date -u '+%F %T') start T1g/T2g/T3g cpu1000 nonmin on cafe1, 3x2 workers, seed-prefix 1000, TMPDIR=/tmp, loadavg=$(cut -d' ' -f1-3 /proc/loadavg)" >> $W/cpu/run.log
for row in T1g T2g T3g; do
  ( cd $C && nohup python3 STAGE3_gem5/timing/firstdet_stream.py --code-root $C \
      --config runconfigs/nonmin_20261110/${row}_$M.jsonc --model $M --out $W/cpu/${row}_cpu1000 \
      --seed 20261109 --parallel 2 --seed-prefix 1000 --poll 10 > $W/cpu/${row}_cpu1000.stdout 2>&1 & echo $! > $W/cpu/$row.pid )
  echo "$(date -u '+%F %T') started $row pid=$(cat $W/cpu/$row.pid)" >> $W/cpu/run.log
done
