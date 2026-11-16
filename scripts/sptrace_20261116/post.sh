#!/usr/bin/env bash
# post.sh (agent sptrace) -- final paired race scans. Run from $O/code.
O=/tests/sptrace_20261116; T=SPT_6_oneLP_v2_flat_ld_s2Aspt; cd $O/code
echo "post START $(date -u)"
python3 scripts/bigcorpus_20261115/race_scan.py results/sptrace_fence_d1_${T}__latest --json $O/race/d1.json > $O/race/d1.txt 2>&1
for d in 3 4; do
  [ -d results/sptrace_fence_d${d}_${T}__latest ] && python3 scripts/bigcorpus_20261115/race_scan.py results/sptrace_fence_d${d}_${T}__latest \
    --control results/sptrace_fence_d1_${T}__latest --examples 50 --json $O/race/d${d}_vs_d1.json > $O/race/d${d}_vs_d1.txt 2>&1
done
cat $O/race/*.txt; echo "post END $(date -u)"
