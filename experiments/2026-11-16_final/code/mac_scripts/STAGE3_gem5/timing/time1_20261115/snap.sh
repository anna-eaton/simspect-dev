#!/bin/bash
# TIME-1: one load snapshot (inside gem5_dev): uptime, top -bn1 header, and the non-zombie gem5/java/python processes.
# Usage: snap.sh <label>   (prints to stdout; the runners tee it into their run.log)
echo "=== SNAPSHOT $1 $(date -u '+%F %T') ==="
uptime
top -bn1 | head -5
echo "--- running gem5/java/python (non-zombie, container view) ---"
ps -eo pid,stat,pcpu,etime,args | awk 'NR==1 || ($2 !~ /^Z/ && /gem5|java|python/ && !/awk/)' | cut -c1-200 | head -40
echo "=== END SNAPSHOT ==="
