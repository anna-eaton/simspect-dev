#!/bin/bash
# firstdet-final (2026-11-10): copy the cafe1 CleanupSpec consumer's run dir (results.jsonl, order_stream.tsv,
# raw/, traces/, logs; not work/) to cafe3, where firstdet_final_launch.sh classify-loop merges it with cafe3's.
# Runs on the Mac (the cluster has no node-to-node keys; it uses the Mac's forwarded agent via cafe2).
# Log: ~/Library/Logs/simspect/firstdet_sync_cafe1.log
set -u
D=/tests/simspect_alloy_20261108/firstdet_final
R=${ROW:-T2rt}_Footprint_6_u_core_lpP_fv3_cafe1   # ROW=T2g for the final protocol run, ROW=T2u5 for the UV5 batch
L=~/Library/Logs/simspect/firstdet_sync_cafe1.log; mkdir -p "$(dirname $L)"
echo "[$(date -u '+%F %T')] sync start" >> $L
ssh -o ConnectTimeout=20 -A cafe2 "ssh cafe1 docker exec -i gem5_dev tar cf - -C $D --exclude=$R/work $R" 2>>$L \
  | ssh -o ConnectTimeout=20 -A cafe2 "ssh cafe3 docker exec -i gem5_dev tar xf - -C $D" 2>>$L
rc=$?
n=$(ssh -o ConnectTimeout=20 -A cafe2 "ssh cafe3 docker exec -i gem5_dev wc -l $D/$R/results.jsonl" 2>>$L)
echo "[$(date -u '+%F %T')] sync end rc=$rc cafe3 copy: $n" >> $L
echo "rc=$rc $n"
