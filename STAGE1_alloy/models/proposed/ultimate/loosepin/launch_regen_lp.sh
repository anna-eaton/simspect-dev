#!/usr/bin/env bash
# launch_regen_lp.sh -- XML phase for loose-pin drafts on a cafe node, through the real pipeline
# (pipeline.py xml + alloy.solver_order: 16 random seeds + default, parallel, per-seed timeout from the config).
# Runs inside gem5_dev. Layout (copied from the Mac repo):
#   $WS/code/      code snapshot (pipeline.py, alloy_solver_order.py, STAGE1_alloy, STAGE2_compilation, STAGE3_gem5, specs, runconfigs)
#   $WS/models/    the drafts (<draft>.als)
#   $WS/runs/<draft>/xml/   output: inst-*.xml + SOLVER_ORDER.json + _dedup_map.jsonl + _dedup_dups.jsonl + _solver_order.log
# Logs: $WS/logs/launch_regen_lp.log (start/launch/exit per draft), $WS/logs/xml_<draft>.out (pipeline stdout+stderr).
# Usage: launch_regen_lp.sh <draft> [<draft> ...]     (refuses a draft whose xml dir already has instances)
set -u
WS=${WS:-/tests/simspect_alloy_20261108/loosepin_regen}
LOG=$WS/logs/launch_regen_lp.log
mkdir -p "$WS/logs" "$WS/runs"
for d in "$@"; do
  cfg=$WS/code/runconfigs/regen_lp_20261110/xml_$d.jsonc
  if [ ! -f "$WS/models/$d.als" ] || [ ! -f "$cfg" ]; then echo "$(date -Is) REFUSE $d: model or config missing" | tee -a "$LOG"; continue; fi
  if ls "$WS/runs/$d/xml"/inst-*.xml >/dev/null 2>&1; then echo "$(date -Is) REFUSE $d: $WS/runs/$d/xml already has instances" | tee -a "$LOG"; continue; fi
  ( cd "$WS/code" && echo "$(date -Is) START $d sha256=$(sha256sum "$WS/models/$d.als" | cut -c1-64) host=$(hostname)" >> "$LOG" \
    && python3 -u pipeline.py xml --model "$d" --config "$cfg" > "$WS/logs/xml_$d.out" 2>&1; \
    echo "$(date -Is) EXIT $d rc=$? kept=$(ls "$WS/runs/$d/xml" 2>/dev/null | grep -c '^inst-.*\.xml$')" >> "$LOG" ) &
  echo "$(date -Is) launched $d subshell pid=$!" >> "$LOG"
done
wait
echo "$(date -Is) ALL EXITED: $*" >> "$LOG"
