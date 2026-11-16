#!/usr/bin/env bash
# gem5_row.sh -- BIGCORPUS COPY (agent bigcorpus 2026-11-15) of scripts/overnight_20261111/gem5_row.sh. Runs INSIDE gem5_dev, from tmux.
# Usage: gem5_row.sh <OUT> <ROW> <cfgA> <modelA> [<cfgB> <modelB> ...]
# Each recipe: `testrun.py --once --resume` passes until a pass finds nothing new AND <OUT>/testsets/<model>/READY exists.
# Additions vs the overnight copy: (1) if the config has race_knobs.commitToIEWDelay, export SIMSPECT_COMMIT_IEW_DELAY=<it> (read by
# the tree's configs/example/se_exp.py, which the race configs name as config_script); (2) after a recipe drains, race rows run
# scripts/bigcorpus_20261115/race_scan.py on the campaign -> <OUT>/race/<results_name>.json (+ .txt).
# Log: <OUT>/logs/gem5_<ROW>.out
O=${1:?OUT}; ROW=${2:?ROW}; shift 2
L=$O/logs/gem5_$ROW.out; LAST=$O/logs/.gem5_$ROW.last
cd "$O/code" || exit 1
export TMPDIR=/tmp
# bigcorpus: gem5 wall-timeout safety net raised 120 -> 900 s (gem5_common GEM5_TIMEOUT_S): cafe3 is oversubscribed while Alloy runs and niced
# gem5 runs were killed at 120 s wall with ~2.5 s of CPU (3 of the first 7 CleanupSpec tests). Runaways are still killed; no verdict logic changes.
export SIMSPECT_GEM5_TIMEOUT_S=${SIMSPECT_GEM5_TIMEOUT_S:-900}
mkdir -p "$O/race"
scan(){  # race rows: strict race signature + wrong-path data-obtained count, paired against the delay-1 row of the same build (if present)
  local CTL=$(echo "$RN" | sed 's/_d[0-9]_/_d1_/'); local X=""
  [ "$CTL" != "$RN" ] && [ -d "results/${CTL}__latest" ] && X="--control results/${CTL}__latest"
  python3 scripts/bigcorpus_20261115/race_scan.py "results/${RN}__latest" $X --json "$O/race/$RN.json" > "$O/race/$RN.txt" 2>&1
}
while [ $# -ge 2 ]; do
  C=$1; M=$2; shift 2
  DLY=$(python3 -c "import json,re,sys;c=json.loads(re.sub(r'//[^\n]*','',open('$C').read()));print(c.get('race_knobs',{}).get('commitToIEWDelay',''))")
  RN=$(python3 -c "import json,re,sys;c=json.loads(re.sub(r'//[^\n]*','',open('$C').read()));print(c['paths']['results_name'])")
  if [ -n "$DLY" ]; then export SIMSPECT_COMMIT_IEW_DELAY=$DLY; else unset SIMSPECT_COMMIT_IEW_DELAY; fi
  echo "START $C $M commitToIEWDelay=${DLY:-default} $(date -u)" >> "$L"
  while :; do
    python3 -u testrun.py --config "$C" --model "$M" --max-new 2000 --once --resume 2>&1 | tee -a "$L" > "$LAST"
    rc=${PIPESTATUS[0]}
    [ "$rc" -eq 0 ] || echo "testrun pass rc=$rc $(date -u)" >> "$L"
    if grep -q ' new (of ' "$LAST"; then
      [ -n "$DLY" ] && scan
      continue
    fi
    if [ -f "$O/testsets/$M/READY" ]; then break; fi
    sleep 300
  done
  [ -n "$DLY" ] && scan
  echo "EXIT $C: $M READY and drained $(date -u)" >> "$L"
done
echo "ROW $ROW DONE $(date -u)" >> "$L"
