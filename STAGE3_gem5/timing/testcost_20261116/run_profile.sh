#!/bin/bash
# testcost (agent testcost, 2026-11-16): per-test cost breakdown on cafe2 gem5_dev, nice 19, read-only on the code.
# Uses the TIME-1 code snapshot + testset + configs (/tests/timing_20261115/{code,testsets,configs}) unchanged.
# For each of T1g/T2g/T3g: (1) profile_test.py on the first N pairs of TIME-1's sample (in-process, per-function
# rusage, gem5 variants), (2) the production harness (firstdet_stream.py -> timing_driver.run_one, --parallel 1)
# on the same pairs, for the total per-test CPU incl. both Python interpreters.
# Usage (inside the container): bash run_profile.sh [N=20]
set -u
N=${1:-20}; B=/tests/testcost_20261116; T=/tests/timing_20261115; C=$T/code
MODEL=Footprint_6_u_core_lpP_s2A
mkdir -p $B/logs
exec > >(tee -a $B/logs/run_profile.log) 2>&1
echo "=== testcost START $(date -u '+%F %T') N=$N uptime: $(uptime)"
head -n $N $T/sample/sample.tsv > $B/sample_n$N.tsv
export TMPDIR=/tmp
for R in T1g T2g T3g; do
  CFG=$T/configs/${R}_time1.jsonc
  echo "--- $R profile $(date -u '+%T')"
  nice -n 19 python3 $B/profile_test.py --code-root $C --config $CFG --testset-model $T/testsets/$MODEL \
     --sample $B/sample_n$N.tsv --n $N --out $B/prof_$R --gem5-variants $( [ $R = T1g ] && echo --startup ) \
     > $B/logs/prof_$R.out 2>&1 || echo "profile $R rc=$?"
  echo "--- $R production harness $(date -u '+%T')"
  ( cd $C && nice -n 19 python3 STAGE3_gem5/timing/firstdet_stream.py --code-root $C --config $CFG \
     --model $MODEL --out $B/prod_$R --seed 20261109 --parallel 1 --only-file $B/sample_n$N.tsv --n-max $N --poll 5 \
     > $B/logs/prod_$R.out 2>&1 ) || echo "prod $R rc=$?"
done
echo "=== testcost END $(date -u '+%F %T') uptime: $(uptime)"
