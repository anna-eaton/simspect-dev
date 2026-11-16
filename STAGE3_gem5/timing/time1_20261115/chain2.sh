#!/bin/bash
# TIME-1 (agent timing, 2026-11-15): second chain on cafe2, strictly sequential (one tool at a time, 60 s idle gap between phases):
#   wait for the big-corpus SimSpect chain (logs/simspect_chain.log has the T3g END line), then
#   2. AMuLeT (T5 setup) InvisiSpec, CleanupSpec, SpecLFB: AM_R instances x AM_N programs each (default 14 x 200), + summarize_t5.py
#   3. Stage 1.5 generation re-time: 16 sampled big-corpus jobs, 16 at once (gen_retime.py)
# Usage (cafe2 gem5_dev, in tmux): bash scripts/chain2.sh >> logs/chain2.log 2>&1
B=/tests/timing_20261115; S=$B/scripts; cd $B
AM_R=${AM_R:-14}; AM_N=${AM_N:-200}
log(){ echo "[$(date -u '+%F %T')] chain2: $*"; }
log "START AM_R=$AM_R AM_N=$AM_N"
until grep -q "row=T3g rc" $B/logs/simspect_chain.log 2>/dev/null; do sleep 15; done
sleep 60
for D in ${AM_DEFS:-InvisiSpec CleanupSpec SpecLFB}; do
  log "AMuLeT $D r=$AM_R n=$AM_N"
  bash $S/run_amulet.sh $D $AM_R $AM_N
  run=$(ls -td $B/amulet/runs/${D}_r${AM_R}_n${AM_N}_* | head -1)
  python3 $S/summarize_t5.py $run > $run/summarize.stdout 2>&1; log "summarize $run rc=$? $(grep -E 'cpu_s_per_program|total_programs' $run/summarize.stdout | tr -s ' ' | tr '\n' ' ')"
  sleep 60
done
if [ -z "${SKIP_GEN:-}" ]; then
  log "gen retime"
  bash $S/snap.sh "before gen retime"
  taskset -c 0-31 python3 $S/gen_retime.py --code $B/code --stage15 $B/code/STAGE1_alloy/models/proposed/ultimate/loosepin/stage15lp.py \
     --models $B/gen/s15_inputs/models --jobs-jsonl $B/gen/s15_inputs/jobs.jsonl --n 16 --sample-seed 20261115 --parallel 16 \
     --timeout 600 --cap 100 --walk-p 0.05 --xmx 4g --out $B/gen/retime16
  log "gen retime rc=$?"
  bash $S/snap.sh "after gen retime"
fi
log "END"
