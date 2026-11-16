#!/bin/bash
# TIME-1 fast-path re-time chain (agent timing, 2026-11-16), cafe2 gem5_dev, in tmux. Strictly sequential:
#   0. wait until cafe2 is idle of SimSpect work (no uv5_rounds.sh / firstdet_stream / gem5.opt alive), record a snapshot
#   1. equivalence check (COMMANDS.md 'Fast path'): fastpath_equiv.py driver, 300 of the TIME-1 sample per defense, nice 19, 8 parallel;
#      every END line must read N/N identical, 0 different, harness errors 0 -> otherwise STOP (no re-time)
#   2. idle gate (whole-node busy < 3% for 2 min, max 2 h), then retime_fast.sh (production rerun + fast path, 16 workers pinned 0-31, the full 1,000-pair sample, T1g T2g T3g)
# Log: /tests/timing_20261115/logs/fast_chain.log. Code: /tests/timing_20261115/simspect_fast (new copy; FASTPATH_COPY.txt).
B=/tests/timing_20261115; C=$B/simspect_fast; S=$B/scripts
log(){ echo "[$(date -u '+%F %T')] fast_chain: $*"; }
log START
while pgrep -f "uv5_rounds.sh|firstdet_stream.py|classify_hits.py|classify_cs_rmw.py" >/dev/null || [ -n "$(ps -eo stat,comm | awk '$1 !~ /^Z/ && $2=="gem5.opt"')" ]; do sleep 30; done
log "node idle of SimSpect work"; bash $S/snap.sh "before equiv"
export TMPDIR=/tmp
ok=1
for R in T1g T2g T3g; do
  log "equiv $R"
  (cd $C && nice -n 19 python3 STAGE3_gem5/timing/fastpath_equiv.py driver --code-root $C --config $B/configs/${R}_time1.jsonc \
      --model Footprint_6_u_core_lpP_s2A --out $B/eq_fast/eq_$R --sample 300 --parallel 8)
  rc=$?; last=$(ls $B/eq_fast/eq_$R/*.log 2>/dev/null | head -1); endl=$(grep -h "END driver" $B/eq_fast/eq_$R/*.log 2>/dev/null | tail -1)
  log "equiv $R rc=$rc: $endl"
  if [ $rc -ne 0 ] || ! echo "$endl" | grep -qE "END driver: ([0-9]+)/\1 identical, 0 different, harness errors 0"; then ok=0; log "equiv $R FAILED -> stopping, no re-time"; break; fi
  sleep 30
done
[ $ok = 1 ] || { log END_FAILED; exit 1; }
sleep 60
# idle gate for the measurement: whole-node busy CPU (top us+sy+ni, all users incl. other Slurm jobs) below IDLE_PCT (default 3%)
# on 4 consecutive checks 30 s apart; wait at most IDLE_MAX_S (default 7200 s), then run anyway and log NOT_IDLE.
IDLE_PCT=${IDLE_PCT:-3}; IDLE_MAX_S=${IDLE_MAX_S:-7200}; t0=$(date +%s); n=0
while :; do
  b=$(top -bn1 | awk '/^%Cpu/{print $2+$4+$6; exit}')
  if awk -v b="$b" -v t="$IDLE_PCT" 'BEGIN{exit !(b<t)}'; then n=$((n+1)); else n=0; fi
  [ $n -ge 4 ] && { log "idle gate passed (busy ${b}%)"; break; }
  [ $(( $(date +%s) - t0 )) -ge $IDLE_MAX_S ] && { log "NOT_IDLE: gate timed out after ${IDLE_MAX_S}s (busy ${b}%); measuring anyway, flag the result"; break; }
  sleep 30
done
log "retime_fast start"
CODE=$C bash $C/STAGE3_gem5/timing/time1_20261115/retime_fast.sh "T1g T2g T3g" 16
log "retime_fast rc=$?"
log END
