#!/usr/bin/env bash
# pilot.sh (agent invisispec-fut 2026-11-16) -- run INSIDE gem5_dev on cafe2: the Futuristic pilot, end to end on the production path.
#   gen   : twostage_lp.py with runconfigs/futuristic_20261116/twostage_<F>_fut_pilot.jsonc (Stage 1.5 + Stage 2 recipe A over reused fut cores)
#   gem5  : firstdet_stream.py over EVERY test of the pilot corpus with the row config (default T1g fut), --keep-all-traces, nice 19
# Usage: bash scripts/futuristic_20261116/pilot.sh gen <family e.g. Footprint_6_u>
#        bash scripts/futuristic_20261116/pilot.sh gem5 <row cfg> <corpus> <out name> [parallel]
# Logs: /tests/futuristic_20261116/logs/pilot_<step>_*.log (start, end, rc); each tool's own logs under its ws/out dir.
set -u
B=/tests/futuristic_20261116; C=$B/code; mkdir -p $B/logs
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=${SIMSPECT_GEM5_TIMEOUT_S:-900}
case "$1" in
gen)
  F=$2; LOG=$B/logs/pilot_gen_$F.log; echo "$(date -u '+%F %T') START gen $F" >> $LOG
  cd $C && nice -n 19 python3 -u twostage_lp.py --config runconfigs/futuristic_20261116/twostage_${F}_fut_pilot.jsonc --ws $B/ws_pilot_$F >> $LOG 2>&1
  echo "$(date -u '+%F %T') END gen rc=$?" >> $LOG ;;
gem5)
  CFG=$2; MODEL=$3; NAME=$4; P=${5:-16}; LOG=$B/logs/pilot_gem5_$NAME.log; OUT=$B/firstdet/$NAME; mkdir -p $OUT
  echo "$(date -u '+%F %T') START gem5 cfg=$CFG model=$MODEL out=$OUT P=$P" >> $LOG
  cd $C && nice -n 19 python3 -u STAGE3_gem5/timing/firstdet_stream.py --code-root $C --config $CFG --model $MODEL --out $OUT \
     --seed 20261109 --parallel $P --sample-frac 1 --poll 60 --max-hours 4 --keep-all-traces >> $OUT/stream.stdout 2>&1
  echo "$(date -u '+%F %T') END gem5 rc=$?" >> $LOG ;;
*) echo "usage: pilot.sh gen <F> | gem5 <cfg> <corpus> <name> [P]"; exit 2 ;;
esac
