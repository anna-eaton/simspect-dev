#!/usr/bin/env bash
# run_evidence.sh <row> <corpus> <keys file> <evidence json> [jobs] -- rerun_hits_evidence.py --analyzer recon_stlf over the
# main campaign AND every shard run of <row> (each run only reruns the keys it holds), TMPDIR under /tmp/ev_<row> (short,
# like the campaign's /tmp), logs copied next to the evidence JSON. Run from the eval code root. (regen-lp, 2026-11-10)
set -u
ROW=$1; CORPUS=$2; KEYS=$3; OUT=$4; J=${5:-12}; W=/tmp/ev_${ROW%%_*}
for d in results/${ROW}__latest results/${ROW}_sh*__latest; do
  [ -e "$d" ] || continue; C=$(readlink -f $d); mkdir -p $W
  timeout 3600 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src /tests/simspect_alloy_20261108/testsets_twostage/$CORPUS \
     --code . --work $W --analyzer recon_stlf --out $OUT --kinds ld --keys-file $KEYS --batch 64 --jobs $J --extra-debug Commit 2>&1 | grep -E "hit keys|end"
  cp $W/logs/*.log $(dirname $OUT)/ 2>/dev/null; rm -rf $W
done
