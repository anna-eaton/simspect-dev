#!/usr/bin/env bash
# analyze_pilot.sh (agent invisispec-fut 2026-11-16) -- run INSIDE gem5_dev on cafe2: classify (bugs/classify.py footprint, as the reported
# InvisiSpec rows) + pilot_fidelity.py + blocker.py on one finished pilot run. Read-only on the run; outputs under
# /tests/futuristic_20261116/{classify,analysis}/; log /tests/futuristic_20261116/logs/analyze_<name>.log
# Usage: bash scripts/futuristic_20261116/analyze_pilot.sh <run name e.g. T1g_fut_pilot> <corpus> <defense invisispec|stt|none> <tag>
set -u
B=/tests/futuristic_20261116; C=$B/code; N=$1; TS=$B/testsets/$2; DEF=$3; TAG=$4; LOG=$B/logs/analyze_${N}_$TAG.log
log(){ echo "$(date -u '+%F %T') $*" >> $LOG; }
cd $C; log "START run=$N corpus=$2 defense=$DEF"
if [ "$DEF" != none ]; then
  nice -n 10 python3 STAGE3_gem5/bugs/classify.py footprint --run $B/firstdet/$N --defense $DEF --out $B/classify/${N}_$TAG \
     --testset $TS --stage3 $C/STAGE3_gem5 --jobs 12 >> $LOG 2>&1; log "classify rc=$?"
fi
nice -n 10 python3 scripts/futuristic_20261116/pilot_fidelity.py --run $B/firstdet/$N --testset $TS --code $C \
   --json $B/analysis/fidelity_${N}_$TAG.json --jobs 12 >> $LOG 2>&1; log "fidelity rc=$?"
nice -n 10 python3 scripts/futuristic_20261116/blocker.py --run $B/firstdet/$N --fid $B/analysis/fidelity_${N}_$TAG.json --code $C \
   --testset $TS --json $B/analysis/blocker_${N}_$TAG.json >> $LOG 2>&1; log "blocker rc=$?"
log "END"
