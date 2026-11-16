#!/usr/bin/env bash
# watch_done.sh (agent inttwin2 2026-11-16) -- Mac-side watcher for the inttwin runs: every INTERVAL s (default 900) runs status_node.py on
# cafe1/2/3 (read-only) and appends one JSON line per node to experiments/2026-11-16_inttwin/watch.log. Exits 0 when every node reports
# finished, exits 3 as soon as any node reports a stall (so the caller can re-arm the dead loop), exits 4 at the deadline (default
# 2026-11-17 18:00Z). ssh errors are logged and retried (3 consecutive failures on a node count as a stall).
cd "$(dirname "$0")/../.."; D=experiments/2026-11-16_inttwin; mkdir -p $D; L=$D/watch.log
INT=${INTERVAL:-900}; DL=${DEADLINE:-$(date -j -u -f '%F %T' '2026-11-17 18:00:00' +%s 2>/dev/null || echo 1795456800)}
echo "$(date -u '+%F %T')Z START watch_done.sh interval=$INT" >> $L
while :; do
  all=1; stall=""
  for n in cafe1 cafe2 cafe3; do
    out=$(timeout 120 ssh -o ConnectTimeout=20 $n "docker exec -i gem5_dev python3 - $n" < scripts/inttwin_20261116/status_node.py 2>&1 | tail -1)
    if echo "$out" | python3 -c 'import json,sys; json.loads(sys.stdin.read())' 2>/dev/null; then
      eval FAIL_$n=0; echo "$out" >> $L
      echo "$out" | python3 -c 'import json,sys; s=json.loads(sys.stdin.read()); sys.exit(0 if s["finished"] else 1)' || all=0
      s=$(echo "$out" | python3 -c 'import json,sys; print("; ".join(json.loads(sys.stdin.read())["stalls"]))')
      [ -n "$s" ] && stall="$stall $n: $s;"
    else
      all=0; eval "FAIL_$n=\$(( \${FAIL_$n:-0} + 1 ))"; echo "$(date -u '+%F %T')Z ERROR $n status: $out" >> $L
      [ $(eval echo \${FAIL_$n}) -ge 3 ] && stall="$stall $n: status unreachable 3x;"
    fi
  done
  if [ $all = 1 ]; then echo "$(date -u '+%F %T')Z END all finished" >> $L; exit 0; fi
  if [ -n "$stall" ]; then echo "$(date -u '+%F %T')Z END STALL$stall" >> $L; echo "STALL$stall"; exit 3; fi
  if [ $(date +%s) -ge $DL ]; then echo "$(date -u '+%F %T')Z END deadline" >> $L; exit 4; fi
  sleep $INT
done
