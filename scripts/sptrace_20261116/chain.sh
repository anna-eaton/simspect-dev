#!/usr/bin/env bash
# chain.sh (agent sptrace 2026-11-16) -- unattended driver after the switch to shards (runs in tmux sptrace_sh window chain, gem5_dev, code root).
# 1) wait for all 28 d1/d4 shard DONE files, merge, paired race_scan d4 vs d1  2) launch d3 shards (k 20, jobs 2), wait, merge, d3 vs d1
# 3) write race/FINAL.txt. Disk guard: guard.sh (separate window). Log: logs/chain.log
O=/tests/sptrace_20261116; T=SPT_6_oneLP_v2_flat_ld_s2Aspt; cd $O/code; L=$O/logs/chain.log
log(){ echo "$(date -u +%FT%TZ) $*" >> $L; }
guard(){ :; }   # disk guard moved to guard.sh (window guard), /tmp-based, 60 s
waitfor(){ while [ $(ls $O/logs/shard_d$1_sh*.DONE 2>/dev/null | wc -l) -lt $2 ]; do guard; sleep 300; done; }
scan(){ python3 scripts/sptrace_20261116/merge.py "$@" >> $L 2>&1
  python3 scripts/bigcorpus_20261115/race_scan.py results/sptrace_fence_d1_${T}_merged --json $O/race/d1_merged.json > $O/race/d1_merged.txt 2>&1
  for d in 3 4; do [ -d results/sptrace_fence_d${d}_${T}_merged ] && python3 scripts/bigcorpus_20261115/race_scan.py results/sptrace_fence_d${d}_${T}_merged \
     --control results/sptrace_fence_d1_${T}_merged --examples 50 --json $O/race/d${d}_vs_d1_merged.json > $O/race/d${d}_vs_d1_merged.txt 2>&1; done
  cat $O/race/d1_merged.txt $O/race/d*_vs_d1_merged.txt >> $L; }
log "START chain"
waitfor 1 14; waitfor 4 14; log "d1+d4 shards done: $(cat $O/logs/shard_d[14]_sh*.DONE | sort | uniq -c | tr '\n' ' ')"
scan 1 4
python3 scripts/sptrace_20261116/shard_run.py --delays 3 --k 20 --jobs 2 >> $L 2>&1; log "launched d3 shards"
waitfor 3 20; log "d3 shards done: $(cat $O/logs/shard_d3_sh*.DONE | sort | uniq -c | tr '\n' ' ')"
scan 1 4 3
{ date -u; cat $O/race/d1_merged.txt; for d in 4 3; do echo "== d$d vs d1"; cat $O/race/d${d}_vs_d1_merged.txt; done; } > $O/race/FINAL.txt
log "END chain"
