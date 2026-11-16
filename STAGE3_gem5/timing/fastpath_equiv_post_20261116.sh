#!/bin/bash
# fastpath_equiv_post_20261116.sh (agent fastpath, 2026-11-16): after a `fastpath_equiv.py driver` check finished, on cafe3:
#  (1) `stored`: its prod/ and fast/ results vs the big-corpus campaign that ran the same config with the pre-fast-path code;
#  (2) hit attribution: STAGE3_gem5/bugs/classify.py footprint on prod/ and on fast/, then _regress.py classes (exit 1 on a
#      changed label).
#   bash fastpath_equiv_post_20261116.sh <row> <defense> <stored run dir or -> <testset model dir>
set -u
R=$1; D=$2; ST=$3; TS=$4
B=/tests/fastpath_20261116; C=$B/code; E=$B/eq_$R
cd $C && export TMPDIR=/tmp
{
echo "=== post $R START $(date -u '+%F %T')"
if [ "$ST" != "-" ]; then
  nice -n 19 python3 STAGE3_gem5/timing/fastpath_equiv.py stored --run $E --stored $ST --out $E/stored --code-roots $C,/tests/bigcorpus_20261115/code > $E/stored.out 2>&1
  echo "stored rc=$?: $(grep 'END stored' $E/stored.out)"
fi
for S in prod fast; do
  nice -n 19 python3 STAGE3_gem5/bugs/classify.py footprint --run $E/$S --defense $D --out $E/cls_$S --testset $TS \
      --stage3 $C/STAGE3_gem5 --jobs 4 > $E/cls_$S.out 2>&1
  echo "classify $S rc=$? classes=$(wc -l < $E/cls_$S/classes.jsonl 2>/dev/null)"
done
python3 STAGE3_gem5/bugs/_regress.py classes $E/cls_prod/classes.jsonl $E/cls_fast/classes.jsonl > $E/regress.out 2>&1
echo "regress classes rc=$? (0 = no changed label)"; cat $E/regress.out | head -30
echo "=== post $R END $(date -u '+%F %T')"
} >> $B/logs/post_$R.log 2>&1
