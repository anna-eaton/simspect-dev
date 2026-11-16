#!/usr/bin/env bash
# relay_jobs.sh -- copy finished Stage-1.5 jobs of a stage15lp run on cafe2 to the SAME absolute path
# on cafe1, so cafe1's stream_fp.py can merge them (no direct cafe2->cafe1 ssh; runs on the Mac). Every cycle: snapshot
# cafe2 <OUT>/jobs.jsonl, tar the job dirs not yet copied (Mac-side list), untar on cafe1, then replace cafe1's jobs.jsonl by
# the snapshot (rename), so a row appears on cafe1 only after its job dir is there. When cafe2 has SUMMARY.json and
# everything is copied, copy cores.json / QUEUE_ORDER.json / stage15lp.log / SUMMARY.json and stop.
# Log ~/Library/Logs/simspect/relay_jobs_<name>.log. Usage: relay_jobs.sh <OUT dir (absolute, same on both nodes)> [interval_s]
set -u
OUT=${1:?}; IV=${2:-90}; N=$(basename "$OUT"); LOG=~/Library/Logs/simspect/relay_jobs_$N.log; DONE=~/Library/Logs/simspect/relay_jobs_$N.copied
mkdir -p "$(dirname "$LOG")"; touch "$DONE"; log(){ echo "$(date -u '+%F %T') $*" >> "$LOG"; }
log "START $OUT"
while true; do
  snap=$(ssh cafe2 "docker exec -i gem5_dev bash -lc 'cat $OUT/jobs.jsonl 2>/dev/null'" 2>>"$LOG")
  dirs=$(echo "$snap" | python3 -c "import sys,json
for l in sys.stdin:
    l=l.strip()
    if l:
        d=json.loads(l).get('xml_dir')
        if d: print(d)")
  new=$(comm -23 <(echo "$dirs" | sort -u | grep . ) <(sort -u "$DONE"))
  if [ -n "$new" ]; then
    rel=$(echo "$new" | sed "s|^$OUT/||; s|/xml\$||" | tr '\n' ' ')
    if ssh cafe2 "docker exec -i gem5_dev bash -lc 'cd $OUT && tar cf - $rel'" 2>>"$LOG" | ssh cafe1 "docker exec -i gem5_dev bash -lc 'mkdir -p $OUT && tar xf - -C $OUT && echo ok'" 2>>"$LOG" | grep -q ok; then
      echo "$new" >> "$DONE"
      log "copied $(echo "$new" | wc -l) job dirs"
    else
      log "ERROR copying job dirs (retry)"; sleep "$IV"; continue
    fi
  fi
  have=$(sort -u "$DONE")
  echo "$snap" | python3 -c "import sys,json
have=set(open('$DONE').read().split())
for l in sys.stdin:
    l=l.strip()
    if l and (not json.loads(l).get('xml_dir') or json.loads(l)['xml_dir'] in have): print(l)" | ssh cafe1 "docker exec -i gem5_dev bash -lc 'cat > $OUT/.jobs.jsonl.tmp && mv -f $OUT/.jobs.jsonl.tmp $OUT/jobs.jsonl'" 2>>"$LOG"
  if ssh cafe2 "docker exec -i gem5_dev bash -lc 'test -e $OUT/SUMMARY.json'" 2>/dev/null && [ -z "$(comm -23 <(echo "$dirs" | sort -u | grep .) <(sort -u "$DONE"))" ]; then
    ssh cafe2 "docker exec -i gem5_dev bash -lc 'cd $OUT && tar cf - cores.json QUEUE_ORDER.json stage15lp.log MERGE_INPUTS.txt SUMMARY.json'" | ssh cafe1 "docker exec -i gem5_dev bash -lc 'cd $OUT && tar xf -'"
    log "SUMMARY copied; END"; break
  fi
  sleep "$IV"
done
