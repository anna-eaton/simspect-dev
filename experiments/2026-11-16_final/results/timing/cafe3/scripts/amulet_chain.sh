#!/bin/bash
# AMuLeT re-time on a clean node (agent timing, 2026-11-16; Anna: "find a clean node and rerun the amulet timing so that we are fair to them").
# cafe3 gem5_dev, in tmux. Per defense, strictly sequential:
#   1. idle gate: whole-node busy CPU (top us+sy+ni) < 3% on 4 checks 30 s apart (max 2 h, then NOT_IDLE logged)
#   2. start run_amulet.sh <D> <R> 200 (T5/TIME-1 setup, pinned to CPUs 0-31)
#   3. calibration: busy hardware threads = (us+sy+ni)/100 x 64, mean of 6 samples 10 s apart taken 120-180 s after start;
#      target 16 (SimSpect's 16 workers); if outside [14.5, 17.5] the run is killed (its processes: benchmark_t5.py, the
#      AMuLeT cli.py instances under this repo copy, and that defense's AE gem5.opt), its dir moved to amulet/discard_calib/,
#      R := round(R x 16 / busy), and it restarts (at most 4 attempts; the last one is kept whatever it measures)
#   4. wait for the run to end, summarize_t5.py, then the next defense.
# Usage: DEFS="InvisiSpec:14 CleanupSpec:8 SpecLFB:8" bash scripts/amulet_chain.sh >> logs/amulet_chain_cafe3.log 2>&1
B=/tests/timing_20261115; S=$B/scripts; A=$B/amulet
log(){ echo "[$(date -u '+%F %T')] amulet_chain: $*"; }
busy(){ top -bn1 | awk '/^%Cpu/{print ($2+$4+$6)*0.64; exit}'; }
log "START host $(hostname) node=${NODE:-?} cpu=$(lscpu | sed -n 's/^Model name: *//p') nproc=$(nproc) DEFS=[${DEFS}]"
for DR in ${DEFS:-InvisiSpec:14 CleanupSpec:8 SpecLFB:8}; do
  D=${DR%%:*}; R=${DR##*:}
  case $D in InvisiSpec|CleanupSpec) G=/work/amulet/amulet-gem5-${D}_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt;; *) G=/work/amulet/amulet-gem5-${D}_AE-v1.1/build/X86/gem5.opt;; esac
  for att in 1 2 3 4; do
    t0=$(date +%s); n=0
    while :; do b=$(busy); if awk -v b="$b" 'BEGIN{exit !(b<1.92)}'; then n=$((n+1)); else n=0; fi
      [ $n -ge 4 ] && { log "$D idle gate passed (busy threads $b)"; break; }
      [ $(( $(date +%s)-t0 )) -ge 7200 ] && { log "$D NOT_IDLE gate timeout (busy threads $b)"; break; }; sleep 30; done
    log "$D attempt $att: start R=$R"
    bash $S/run_amulet.sh $D $R 200 > /dev/null 2>&1 &
    pid=$!; sleep 5
    run=$(ls -td $A/runs/${D}_r${R}_n200_* | head -1)
    sleep 115; tot=0
    for i in 1 2 3 4 5 6; do b=$(busy); tot=$(awk -v t=$tot -v b=$b 'BEGIN{print t+b}'); sleep 10; done
    m=$(awk -v t=$tot 'BEGIN{printf "%.1f", t/6}')
    log "$D attempt $att R=$R: busy threads 120-180 s = $m (run $run)"
    if [ $att -lt 4 ] && ! awk -v m=$m 'BEGIN{exit !(m>=14.5 && m<=17.5)}'; then
      newR=$(awk -v r=$R -v m=$m 'BEGIN{x=int(r*16/m+0.5); if(x<1)x=1; print x}')
      [ "$newR" = "$R" ] && { log "$D: adjusted R equals R=$R; keeping this run"; wait $pid; break; }
      log "$D: off target -> kill run, discard, restart with R=$newR"
      pkill -f "benchmark_t5.py.*time1$D"; sleep 2; pkill -f "cli.py"; pkill -f "$G"; sleep 5
      pkill -9 -f "benchmark_t5.py.*time1$D"; pkill -9 -f "cli.py"; pkill -9 -f "$G"; wait $pid 2>/dev/null
      mkdir -p $A/discard_calib; mv $run $A/discard_calib/ ; echo "$(date -u) $D R=$R busy=$m off target 16; restarted R=$newR" >> $A/discard_calib/WHY.txt
      R=$newR; sleep 60; continue
    fi
    log "$D: keeping R=$R (busy $m)"; wait $pid; break
  done
  run=$(ls -td $A/runs/${D}_r${R}_n200_* | head -1)
  python3 $S/summarize_t5.py $run > $run/summarize.stdout 2>&1
  log "$D END run=$run rc=$? $(grep -E 'cpu_s_per_program|total_programs' $run/summarize.stdout | tr -s ' ' | tr '\n' ' ')"
  sleep 60
done
log END
