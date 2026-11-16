#!/usr/bin/env bash
# node_run.sh (agent sptrace 2026-11-16) -- SPT-specific VP/squash race run on SPT-Fence. Runs INSIDE gem5_dev on cafe2 from tmux `sptrace`.
# 1. corpus: make_corpus.py (flat SPT_6_oneLP_v2 enumeration -> distinct ld-transmitter XML, no Alloy) -> testsets/$T/xml + corpus_manifest.tsv
# 2. Stage 2 (window s2): testsetgen.py with stage2_final_A_spt copy (both branch modes), then touch testsets/$T/READY
# 3. gem5 (windows d1, d4 concurrently; then d3 in the d4 window after d1 ends): scripts/bigcorpus_20261115/gem5_row.sh (testrun.py passes,
#    SIMSPECT_COMMIT_IEW_DELAY from race_knobs, race_scan after each pass), all streaming on the asm as it lands.
# 4. post.sh: final paired race_scan (d4 vs d1, d3 vs d1) -> race/*.json/txt.  Logs: $O/logs/*.  Disk guard: diskwatch kills the session < 30 GB.
set -u
O=/tests/sptrace_20261116; T=SPT_6_oneLP_v2_flat_ld_s2Aspt; R=runconfigs/sptrace_20261116
cd $O/code || exit 1; export TMPDIR=/tmp; mkdir -p $O/logs $O/race; [ -L results ] && { echo "code/results must be a real dir (testrun --resume does relative_to(ROOT) on the campaign realpath)"; exit 1; }; mkdir -p results
L=$O/logs/main.log; log(){ echo "$(date -u +%FT%TZ) $*" | tee -a $L; }
log "START node_run.sh (code $(cat SNAPSHOT.txt | head -1))"
if [ ! -f $O/testsets/$T/xml/.done ]; then
  python3 scripts/sptrace_20261116/make_corpus.py $O/testsets/$T/xml $O/testsets/$T/corpus_manifest.tsv >> $L 2>&1 || { log "ERROR make_corpus rc=$?"; exit 1; }
  touch $O/testsets/$T/xml/.done
fi
log "corpus: $(ls $O/testsets/$T/xml | grep -c xml$) XML; manifest sha256 $(sha256sum $O/testsets/$T/corpus_manifest.tsv | cut -c1-16)"
S2=$R/stage2_final_A_spt_$T.jsonc
tmux new-window -d -t sptrace -n s2 "cd $O/code && export TMPDIR=/tmp && nice -n 5 python3 -u testsetgen.py --model $T --config $S2 --interval 60 >> $O/logs/s2.log 2>&1; echo EXIT rc=\$? \$(date -u) >> $O/logs/s2.log; touch $O/testsets/$T/READY"
log "launched s2"
[ -f $O/testsets/$T/READY ] || sleep 240   # let the first llvm/asm land
G="nice -n 5 bash scripts/bigcorpus_20261115/gem5_row.sh $O"
tmux new-window -d -t sptrace -n d1 "cd $O/code && $G d1 $R/race_sptfence_d1_$T.jsonc $T; touch $O/logs/d1.DONE"
tmux new-window -d -t sptrace -n d4 "cd $O/code && $G d4 $R/race_sptfence_d4_$T.jsonc $T; while [ ! -f $O/logs/d1.DONE ]; do sleep 60; done; $G d3 $R/race_sptfence_d3_$T.jsonc $T; bash scripts/sptrace_20261116/post.sh >> $O/logs/post.log 2>&1; touch $O/logs/ALL.DONE"
log "launched d1, d4 (d3 + post.sh follow in d4)"
while [ ! -f $O/logs/ALL.DONE ]; do
  free=$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); echo "$(date -u +%FT%TZ) free=${free}G load=$(cut -d' ' -f1 /proc/loadavg)" >> $O/logs/diskwatch.log
  if [ "$free" -lt 30 ]; then log "DISK GUARD: ${free}G < 30G, killing windows s2 d1 d4"; for w in s2 d1 d4; do tmux kill-window -t sptrace:$w; done; exit 2; fi
  sleep 600
done
log "END all done"
