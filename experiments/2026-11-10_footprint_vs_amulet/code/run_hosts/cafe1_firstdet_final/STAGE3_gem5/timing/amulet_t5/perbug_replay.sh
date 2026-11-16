#!/bin/bash
# amulet-perbug (2026-11-09): replay EVERY violation of the T5 AMuLeT runs (not only each
# instance's first) with AMuLeT's own analyser under debug flags, via classify_t5.py --all
# (unchanged; it skips violations already replayed). Writes <run>/t5_classes_all.json.
# Usage (inside cafe1 gem5_dev): perbug_replay.sh [jobs_per_defense=18]
set -u
J="${1:-18}"
T5=/tests/simspect_alloy_20261108/timing/amulet_t5
PB=$T5/perbug
mkdir -p "$PB/logs"
export PATH=/opt/amulet-venv/bin:$PATH
cd "$T5/amulet-repo/src" || exit 3
echo "=== perbug_replay START $(date -u +%FT%TZ) host=$(hostname) jobs/defense=$J"; uptime
pids=()
for RD in SpecLFB:SpecLFB_20261110T012205Z CleanupSpec:CleanupSpec_20261110T013433Z InvisiSpec:InvisiSpec_20261110T015013Z; do
  D=${RD%%:*}; R=$T5/runs/${RD#*:}
  ( echo "--- $D START $(date -u +%FT%TZ) run=$R"
    python3 "$T5/classify_t5.py" "$R" "$D" --all --jobs "$J"
    echo "--- $D END $(date -u +%FT%TZ) rc=$?" ) > "$PB/logs/replay_$D.log" 2>&1 &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
echo "=== perbug_replay END $(date -u +%FT%TZ) rc=$rc"; uptime
