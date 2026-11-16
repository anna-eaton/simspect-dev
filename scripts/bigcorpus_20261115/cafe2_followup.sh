#!/usr/bin/env bash
# cafe2_followup.sh -- unattended Mac-side waiter (agent bigcorpus 2026-11-15). Polls cafe3 every 10 min; when STT_6_u_core_lpP_s2A is READY it
# syncs it to cafe2 and launches the SPT-Fence race rows there; when Recon_6_u_core_lpP_s2A is READY it syncs it and launches E6 (recipe A; B is
# synced/launched the same way when its READY appears). Each step runs once (marker files in ~/Library/Logs/simspect/bigcorpus_followup/).
# Run: nohup scripts/bigcorpus_20261115/cafe2_followup.sh >> ~/Library/Logs/simspect/bigcorpus_followup.log 2>&1 &
# Stops after all steps are done or after 40 h. Every step and error is logged with a UTC timestamp.
REPO=$(cd "$(dirname "$0")/../.." && pwd); cd "$REPO" || exit 1
M=~/Library/Logs/simspect/bigcorpus_followup; mkdir -p $M
log(){ echo "$(date -u '+%F %T') $*"; }
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
ready(){ $SSH cafe3 "docker exec gem5_dev test -f /tests/bigcorpus_20261115/testsets/$1/READY"; }
step(){ # name model rows...
  local n=$1 m=$2; shift 2
  [ -f $M/$n.done ] && return 0
  ready $m || return 1
  log "STEP $n: $m READY on cafe3 -> sync + launch rows [$*] on cafe2"
  if scripts/bigcorpus_20261115/sync_cafe2.sh corpus $m && scripts/bigcorpus_20261115/launch_gem5.sh cafe2 "$@"; then
    touch $M/$n.done; log "STEP $n DONE"
  else log "STEP $n FAILED (rc=$?); will retry next poll"; return 1; fi
}
log "START followup pid $$"
end=$(( $(date +%s) + 40*3600 ))
while [ $(date +%s) -lt $end ]; do
  step spt_race STT_6_u_core_lpP_s2A race_sptfence_d1 race_sptfence_d4
  step e6_A Recon_6_u_core_lpP_s2A E6
  step e6_B Recon_6_u_core_lpP_s2B E6
  [ -f $M/spt_race.done ] && [ -f $M/e6_A.done ] && [ -f $M/e6_B.done ] && { log "ALL STEPS DONE"; exit 0; }
  sleep 600
done
log "TIMEOUT after 40 h"
