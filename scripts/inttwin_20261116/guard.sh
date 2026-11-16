#!/usr/bin/env bash
# guard.sh (agent inttwin 2026-11-16; copy of scripts/sptrace_20261116/guard.sh, coordinator's disk rule) -- disk guard for the inttwin
# runs on one node (/tmp in gem5_dev = the host overlay). Every 60 s: free < 40 GB -> PAUSE (SIGSTOP every inttwin testrun/checker, so
# no new gem5 tests start); free >= 45 GB -> RESUME (SIGCONT); free < 25 GB -> STOP: kill the inttwin shard windows + their
# testrun/checker/gem5, touch logs/GUARD_STOPPED, exit. Kills any gem5 whose /tmp workdir passes 3 GB (runaway; recorded as an error).
# Run inside gem5_dev: bash /tests/inttwin_20261116/code/scripts/inttwin_20261116/guard.sh   Log: /tests/inttwin_20261116/logs/guard.log
O=/tests/inttwin_20261116; L=$O/logs/guard.log; paused=0
log(){ echo "$(date -u +%FT%TZ) $*" >> $L; }
pids(){ pgrep -f "inttwin_20261116/code/STAGE3_gem5/check_|testrun.py --config $O/cfg/" ; }
mine(){ local q=$1; while [ -n "$q" ] && [ "$q" -gt 1 ]; do grep -qa "inttwin_20261116" /proc/$q/cmdline 2>/dev/null && return 0; q=$(awk '{print $4}' /proc/$q/stat 2>/dev/null); done; return 1; }  # only our gem5 (an ancestor is an inttwin process)
log "START guard pid $$"
while :; do
  free=$(df -BG --output=avail /tmp | tail -1 | tr -dc 0-9)
  if [ "$free" -lt 25 ]; then
    log "STOP: /tmp free ${free}G < 25G: killing inttwin shards"
    tmux list-windows -t inttwin_sh -F '#W' 2>/dev/null | grep -v '^ctl$' | xargs -r -I{} tmux kill-window -t inttwin_sh:{}
    pkill -CONT -f "inttwin_20261116/code"; pkill -f "testrun.py --config $O/cfg/"; pkill -f "inttwin_20261116/code/STAGE3_gem5/check_"
    touch $O/logs/GUARD_STOPPED; exit 2
  elif [ "$free" -lt 40 ] && [ $paused = 0 ]; then
    for p in $(pids); do kill -STOP $p; done; paused=1; log "PAUSE: /tmp free ${free}G < 40G (SIGSTOP $(pids | wc -l) procs)"
  elif [ "$free" -ge 45 ] && [ $paused = 1 ]; then
    for p in $(pids); do kill -CONT $p; done; paused=0; log "RESUME: /tmp free ${free}G"
  fi
  for d in $(find /tmp -maxdepth 1 -name "gem5_inst-*" -mmin -60 2>/dev/null); do
    [ -d "$d" ] || continue
    s=$(du -sm "$d" 2>/dev/null | cut -f1); [ "${s:-0}" -gt 3072 ] || continue
    p=$(pgrep -f -- "--outdir=$d/m5out"); [ -n "$p" ] && mine $p && { kill $p; log "RUNAWAY: killed gem5 $p ($d ${s} MB; $(ps -o args= -p $p 2>/dev/null | cut -c1-120))"; }
  done
  echo "$(date -u +%FT%TZ) free=${free}G paused=$paused load=$(cut -d' ' -f1 /proc/loadavg)" > $O/logs/guard.last
  sleep 60
done
