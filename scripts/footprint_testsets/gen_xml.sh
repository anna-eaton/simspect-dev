#!/usr/bin/env bash
# Enumerate the six footprint models on the Mac.
#   branch models  {InvisiSpec,CleanupSpec,SpecLFB}_6.als      (STT_6 skeleton)
#   store models   {InvisiSpec,CleanupSpec,SpecLFB}_6_stl.als  (STT_6_stl skeleton)
# The three models of each family have identical code (only comments differ), so the InvisiSpec model
# is enumerated under 4 solver orders and the other two under the default order only; merge_xml.py then
# checks that the default-order outputs are identical across the three and builds one deduplicated XML set
# per family that all three defenses' testsets use.
# Usage: scripts/footprint_testsets/gen_xml.sh [CAP]   (CAP per solver order, default 5000)
# Log: results/footprint_models_20261109/gen_xml.log ; per-run logs in flat/<Model>/run_flat.log
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
W="$REPO/results/footprint_models_20261109"
TOOLS="$REPO/STAGE1_alloy/models/proposed/singlestage/tools"
CAP="${1:-5000}"
JAVA_HOME_17=/opt/homebrew/opt/openjdk@17
export PATH="$JAVA_HOME_17/bin:$PATH"
mkdir -p "$W/classes" "$W/flat"
LOG="$W/gen_xml.log"
log(){ echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" | tee -a "$LOG"; }
log "START cap=$CAP repo=$REPO java=$(command -v java) ($(java -version 2>&1 | head -1))"
if [ ! -f "$W/classes/a6RandomModels.class" ]; then
  log "compile a6RandomModels.java"
  javac -cp "$REPO/STAGE1_alloy/alloy6.jar" -d "$W/classes" "$TOOLS/a6RandomModels.java" 2>>"$LOG"
fi
run(){ # model seeds
  local m="$1" seeds="$2"
  log "RUN $m seeds=$seeds"
  if python3 "$TOOLS/run_flat.py" --model "$REPO/STAGE1_alloy/models/$m.als" --out "$W/flat/$m" \
       --alloy-dir "$REPO/STAGE1_alloy" --classes "$W/classes" --seeds "$seeds" --cap "$CAP" \
       --timeout 2400 --jobs 4 --min-disk-gb 40 >>"$LOG" 2>&1; then
    log "DONE $m"
  else
    log "ERROR $m exit=$? (see $W/flat/$m/run_flat.log)"
  fi
}
run InvisiSpec_6      default,1,2,3
run InvisiSpec_6_stl  default,1,2,3
run CleanupSpec_6     default
run SpecLFB_6         default
run CleanupSpec_6_stl default
run SpecLFB_6_stl     default
log "END"
