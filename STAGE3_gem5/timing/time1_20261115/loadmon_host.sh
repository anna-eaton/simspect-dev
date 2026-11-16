#!/bin/bash
# TIME-1 (agent timing, 2026-11-15): HOST-level load monitor for cafe2 (runs on the host, outside docker, as the ssh user).
# Every INTERVAL s (default 30) appends one line: UTC time, loadavg, top's %Cpu line, #running (R) tasks, and the
# top 6 non-zombie processes by %CPU (user, comm, %cpu). Stops after MAXH hours (default 10) or when ~/time1_loadmon.STOP exists.
# Usage: nohup bash loadmon_host.sh > ~/time1_loadmon.log 2>&1 &     Log: ~/time1_loadmon.log (copied to /tests/timing_20261115/logs at the end)
INTERVAL=${INTERVAL:-30}; MAXH=${MAXH:-10}; end=$(( $(date +%s) + MAXH*3600 ))
echo "$(date -u '+%F %T') loadmon START pid $$ host $(hostname) interval ${INTERVAL}s maxh ${MAXH}"
while [ $(date +%s) -lt $end ] && [ ! -e ~/time1_loadmon.STOP ]; do
  cpu=$(top -bn1 | grep -m1 '^%Cpu' | tr -s ' ')
  nr=$(ps -eo stat= | grep -c '^R')
  topp=$(ps -eo user:10,stat,pcpu,comm --sort=-pcpu | awk '$2 !~ /^Z/' | sed -n '2,7p' | awk '{printf "%s/%s/%s; ", $1,$4,$3}')
  echo "$(date -u '+%F %T') load=$(cut -d' ' -f1-3 /proc/loadavg) R=$nr | $cpu | $topp"
  sleep $INTERVAL
done
echo "$(date -u '+%F %T') loadmon END"
