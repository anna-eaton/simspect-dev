#!/usr/bin/env bash
# footprint_waiter.sh -- node-side (cafe3 gem5_dev, tmux bc_gem5 window fp_wait) waiter for the Footprint first-detection rows (agent bigcorpus 2026-11-15).
# Anna 2026-11-15: replicate the 2026-11-10 firstdet-final protocol EXACTLY on the big corpus: InvisiSpec T1g and SpecLFB T3g run the first 4,000
# of the seed-20261109 order (`--seed-prefix 4000`, sample-frac 1), which is only defined once the corpus is READY, so they start then (T2g, the
# whole corpus, streams from the start). Then recipe B (reported separately): T1g/T3g/T2g on Footprint_6_u_core_lpP_s2B when its READY exists.
# Log: /tests/bigcorpus_20261115/logs/fp_waiter.log
B=/tests/bigcorpus_20261115; L=$B/logs/fp_waiter.log; cd $B/code || exit 1
log(){ echo "[$(date -u '+%F %T')] $*" >> $L; }
log "START waiter"
until [ -f $B/testsets/Footprint_6_u_core_lpP_s2A/READY ]; do sleep 300; done
log "Footprint A READY -> start T1g T3g with --seed-prefix 4000"
ONLY="T1g T3g" P_T1g=12 P_T3g=12 X_T1g="--seed-prefix 4000" X_T3g="--seed-prefix 4000" nice -n 15 bash scripts/bigcorpus_20261115/footprint_launch.sh start
[ "${NO_B:-0}" = 1 ] && { log "NO_B=1: recipe B deferred (Anna 2026-11-15: B waits until the nov10 A rows are done); waiter ends"; exit 0; }
until [ -f $B/testsets/Footprint_6_u_core_lpP_s2B/READY ]; do sleep 300; done
log "Footprint B READY -> start recipe B rows (T2g whole corpus, T1g/T3g seed prefix 4000), nice 19"
MODEL=Footprint_6_u_core_lpP_s2B P=8 X_T1g="--seed-prefix 4000" X_T3g="--seed-prefix 4000" nice -n 19 bash scripts/bigcorpus_20261115/footprint_launch.sh start
log "B classify loop"
MODEL=Footprint_6_u_core_lpP_s2B CLS_JOBS=4 nice -n 19 bash scripts/bigcorpus_20261115/footprint_launch.sh classify-loop
