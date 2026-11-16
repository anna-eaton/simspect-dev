#!/usr/bin/env bash
# guard.sh (agent sptrace 2026-11-16, coordinator request) -- disk guard for the sptrace shards on cafe2 (/tmp in gem5_dev = host /scr overlay).
# Every 60 s: free < 40 GB -> PAUSE (SIGSTOP every sptrace check_ld.py/testrun.py, so no new gem5 tests start; running gem5 finish or hit the
# timeout) and log; free >= 45 GB -> RESUME (SIGCONT). free < 25 GB -> STOP: kill sptrace_sh shard windows + their testrun/check_ld/gem5, log, exit.
# Also kills any sptrace-owned gem5 whose workdir trace exceeds 3 GB (runaway; the checker records it as an error). Log: logs/guard.log
O=/tests/sptrace_20261116; L=$O/logs/guard.log; paused=0
log(){ echo "$(date -u +%FT%TZ) $*" >> $L; }
pids(){ pgrep -f "sptrace_20261116/code/(STAGE3_gem5/check_ld.py|testrun.py)|testrun.py --config runconfigs/sptrace_20261116" ; }
log "START guard pid $$"
while :; do
  free=$(df -BG --output=avail /tmp | tail -1 | tr -dc 0-9)
  if [ "$free" -lt 25 ]; then
    log "STOP: /tmp free ${free}G < 25G: killing shards"
    tmux list-windows -t sptrace_sh -F '#W' | grep -E '^d[0-9]s[0-9]+$' | xargs -r -I{} tmux kill-window -t sptrace_sh:{}
    pkill -CONT -f "sptrace_20261116/code" ; pkill -f "testrun.py --config runconfigs/sptrace_20261116"; pkill -f "sptrace_20261116/code/STAGE3_gem5/check_ld.py"
    touch $O/logs/GUARD_STOPPED; exit 2
  elif [ "$free" -lt 40 ] && [ $paused = 0 ]; then
    for p in $(pids); do kill -STOP $p; done; paused=1; log "PAUSE: /tmp free ${free}G < 40G (SIGSTOP $(pids | wc -l) procs)"
  elif [ "$free" -ge 45 ] && [ $paused = 1 ]; then
    for p in $(pids); do kill -CONT $p; done; paused=0; log "RESUME: /tmp free ${free}G"
  fi
  for d in $(find /tmp -maxdepth 1 -name "gem5_inst-*" -mmin -60 2>/dev/null); do
    [ -d "$d" ] || continue
    s=$(du -sm "$d" 2>/dev/null | cut -f1); [ "${s:-0}" -gt 3072 ] || continue
    p=$(pgrep -f -- "--outdir=$d/m5out"); [ -n "$p" ] && { kill $p; log "RUNAWAY: killed gem5 $p ($d ${s} MB)"; }
  done
  echo "$(date -u +%FT%TZ) free=${free}G paused=$paused load=$(cut -d' ' -f1 /proc/loadavg)" > $O/logs/guard.last
  sleep 60
done
