#!/usr/bin/env bash
# stage1a.sh (agent invisispec-fut 2026-11-16) -- run INSIDE gem5_dev on a cafe node: Stage 1a (RI cores) of a Futuristic core model to UNSAT,
# exactly as twostage_lp.py's stage1_and_rest does it (partition_stage1.py, then launch_stage1.py over every partition), but with the
# launcher at nice 19 and a 24 h per-partition timeout so every partition can reach EXHAUSTED (UNSAT) at the 6-instruction bound.
# Usage: bash scripts/futuristic_20261116/stage1a.sh <core model stem> [jobs]   e.g. Footprint_6_u_core_ri_fut 8
# Layout: /tests/futuristic_20261116/stage1/{parts/<stem>, out/<stem>/<part>/stage1_xml, logs/<stem>__<part>.log, status/}; this script logs to
# /tests/futuristic_20261116/logs/stage1a_<stem>.log (start, end, rc). Resume: rerun; finished partitions are skipped by run_stage1.py
# (output dir not empty -> NOT_STARTED), so delete an unfinished partition's out dir before rerunning it.
# Optional env: FUT_CODE (code dir, default $B/code), FUT_WS (workspace, default $B/stage1), FUT_TAG (log suffix). The FUT-1 (a) rerun uses
# FUT_CODE=$B/code_fut2 FUT_WS=$B/stage1_fut2 FUT_TAG=fut2 (models with the [fut-2] fact; the first enumeration stays in $B/stage1).
set -u
B=/tests/futuristic_20261116; C=${FUT_CODE:-$B/code}; S=${FUT_WS:-$B/stage1}; STEM=$1; J=${2:-8}
mkdir -p $B/logs $S; LOG=$B/logs/stage1a_$STEM${FUT_TAG:+_$FUT_TAG}.log; log(){ echo "$(date -u '+%F %T') $*" >> $LOG; }
log "START stem=$STEM jobs=$J model=$C/STAGE1_alloy/models/$STEM.als sha256=$(sha256sum $C/STAGE1_alloy/models/$STEM.als | cut -c1-64)"
[ -e $S/STAGE1_alloy ] || ln -s $C/STAGE1_alloy $S/STAGE1_alloy
if [ ! -f $S/parts/$STEM/partitions.json ]; then
  python3 $C/STAGE1_alloy/models/proposed_twophase/partition_stage1.py $C/STAGE1_alloy/models/$STEM.als $S/parts/$STEM >> $LOG 2>&1 || { log "partition_stage1 FAILED rc=$?"; exit 1; }
fi
nice -n 19 python3 -u $C/STAGE1_alloy/models/proposed_twophase/launch_stage1.py --ws $S --families $STEM --jobs $J --cap 200000 \
  --timeout 86400 --xmx 8g --min-disk-gb 30 >> $LOG 2>&1
log "END rc=$?"
