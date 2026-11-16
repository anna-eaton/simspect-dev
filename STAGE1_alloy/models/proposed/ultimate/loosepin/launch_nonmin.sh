#!/usr/bin/env bash
# launch_nonmin.sh -- the NON-MINIMAL footprint corpus, streamed like the production twostage_lp run.
# Stage 1 REUSED (Footprint_6_u_core_ri cores of regen-lp, 363 distinct at the pin level) -> stage15lp.py with
# Footprint_6_u_lpN.als (leak + no-junk + committed region + path-style core pin + brcap 2 + lp_flagcanon; no RR/RS)
# -> stream_fp.py (Stage 2 recipe v3 + RMW eligible p0.5 + jmp uniform p0.5), deduplicated against the minimal corpus
# (--seen-from = nonmin_fp.py normalized fingerprints of Footprint_6_u_core_lpP_fv3), stems numbered from inst-3000001.
# Runs inside gem5_dev on cafe1. Layout: $WS/code (code snapshot from the Mac), $WS/cfg, $WS/runs15, $WS/logs, $WS/pids.
# Logs: $WS/logs/launch_nonmin.log (start/stop/exit), $WS/logs/stage15lp.out, $WS/runs15/<model>/stage15lp.log,
#       $WS/logs/stream_<corpus>.log + stream_fp.out. Stop: touch $WS/STOP (the watcher TERMs both process groups by PID).
set -u
WS=${WS:-/tests/simspect_alloy_20261108/nonmin}
C=$WS/code; LP=$C/STAGE1_alloy/models/proposed/ultimate/loosepin
TS=/tests/simspect_alloy_20261108/testsets_twostage
MODEL=$LP/Footprint_6_u_lpN.als
CORPUS=Footprint_6_u_core_lpN_fv3
S1=/tests/simspect_alloy_20261108/loosepin_regen/stage1/out/Footprint_6_u_core_ri
SLOTS=${SLOTS:-32}; TARGET=${TARGET:-26500}; SJOBS=${SJOBS:-24}
LOG=$WS/logs/launch_nonmin.log
mkdir -p "$WS/logs" "$WS/pids" "$WS/cfg" "$WS/runs15"
log() { echo "$(date -Is) $*" >> "$LOG"; }
[ -e "$WS/stage1" ] || ln -s /tests/simspect_alloy_20261108/loosepin_regen/stage1 "$WS/stage1"   # Stage-1 logs for the CPU-s record
# Stage 2 stream config = recipe v3 with only testset_dir and the asm thread count changed (as twostage_lp.py does)
SRC=$C/runconfigs/regen_lp_20261110/stage2_fv3.jsonc
SCFG=$WS/cfg/stage2_fv3_stream.jsonc
{ echo "// launch_nonmin.sh $(date -Is): copy of $SRC with only paths.testset_dir and gem5.jobs changed"
  sed -e "0,/\"testset_dir\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/s##\"testset_dir\": \"$TS\"#" -e "0,/\"jobs\"[[:space:]]*:[[:space:]]*[0-9]*/s##\"jobs\": $SJOBS#" "$SRC"; } > "$SCFG"
log "START ws=$WS model=$MODEL sha256=$(sha256sum "$MODEL" | cut -c1-64) corpus=$CORPUS slots=$SLOTS target=$TARGET host=$(hostname)"
log "stream cfg diff vs recipe: $(diff <(sed 1d "$SCFG") "$SRC" | tr '\n' ' ')"
cd "$WS"
setsid python3 -u "$LP/stage15lp.py" --base "$MODEL" --cores "$S1"/*/stage1_xml --out "$WS/runs15/Footprint_6_u_lpN" --code "$C" \
  --slots "$SLOTS" --job-timeout 300 --budget-s 5400 --cap 25 --walk-p 0.05 --xmx 4g --spread 2 --dedup-level seed \
  --shuffle-seed 20261110 --target-distinct "$TARGET" --relax-nonbranch-resolved >> "$WS/logs/stage15lp.out" 2>&1 &
P15=$!; echo $P15 > "$WS/pids/stage15lp.pid"; log "stage15lp pid=$P15"
sleep 20
setsid python3 -u "$LP/stream_fp.py" --s15 "$WS/runs15/Footprint_6_u_lpN" --base-name "${CORPUS}_base" --final-name "$CORPUS" \
  --cfg "$SCFG" --code "$C" --ts-dir "$TS" --ws "$WS" --stage1-logs "stage1/logs/Footprint_6_u_core_ri__*.log" \
  --family-label Footprint_6_u_lpN --start-n 3000000 --seen-from "$WS/seen/minimal_norm_seen.json" \
  --interval 120 --jobs "$SJOBS" --min-batch 50 --max-batch 150 --git-rev "264adea+uncommitted(nonmin)" >> "$WS/logs/stream_fp.out" 2>&1 &
PS=$!; echo $PS > "$WS/pids/stream_fp.pid"; log "stream_fp pid=$PS"
# watcher: STOP file -> TERM both process groups (by recorded PID; no pkill -f)
while kill -0 $P15 2>/dev/null || kill -0 $PS 2>/dev/null; do
  if [ -e "$WS/STOP" ]; then log "STOP file seen: TERM pgid $P15 $PS"; kill -TERM -- -$P15 -$PS 2>/dev/null; rm -f "$WS/STOP"; fi
  sleep 15
done
wait $P15; log "stage15lp exited rc=$?"
wait $PS; log "stream_fp exited rc=$? READY=$([ -e "$TS/$CORPUS/READY" ] && echo yes || echo no)"
log "END"
