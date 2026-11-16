#!/usr/bin/env bash
# launch_alloy.sh -- big corpus 2026-11-15 (agent bigcorpus), Stage 1b Alloy. Copy of scripts/overnight_20261111/launch_alloy.sh with:
# OUT=/tests/bigcorpus_20261115, configs runconfigs/bigcorpus_20261115, tmux session bc_alloy, families STT_6_u Recon_6_u
# Footprint_6_u (no SPT: DECIDE SPT-BOUND). Footprint cores = the 1,411 regen-lp cores, streamed from the Mac copy in
# experiments/2026-11-10_footprint_vs_amulet/data/footprint_vs_amulet_20261110_corpus.tar.gz (not from cafe1, reserved).
# Run FROM THE MAC: scripts/bigcorpus_20261115/launch_alloy.sh cafe3 Footprint_6_u STT_6_u Recon_6_u
# Logs: node <OUT>/logs/alloy_<F>.out, <OUT>/ws_<F>/logs/, <OUT>/logs/diskwatch.log; Mac ~/Library/Logs/simspect/bigcorpus_alloy_<node>.log
set -euo pipefail
NODE=${1:?node}; shift
REPO=$(cd "$(dirname "$0")/../.." && pwd)
O=${OUT:-/tests/bigcorpus_20261115}; MIN=${MIN_FREE_GB:-80}; D=runconfigs/bigcorpus_20261115
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/bigcorpus_alloy_${NODE}.log
log(){ echo "$(date -u '+%F %T') [$NODE] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
log "START families=$* out=$O"
free=$(rx "df -BG --output=avail /tests | tail -1 | tr -dc 0-9"); log "disk /tests free ${free}G (min $MIN)"
[ "$free" -ge "$MIN" ] || { log "ABORT: low disk"; exit 1; }
if rx "test -f $O/code/SNAPSHOT.txt"; then
  log "code snapshot exists: $(rx "head -1 $O/code/SNAPSHOT.txt")"
else
  COPYFILE_DISABLE=1 tar -C "$REPO" --exclude=./testsets --exclude=./testsets_twostage --exclude=./results --exclude=./experiments \
      --exclude=./build --exclude=./.git --exclude=./archive --exclude=./paper_figures --exclude=./analysis --exclude=./.obsidian \
      --exclude=./oldsimspectstuff --exclude='*/__pycache__' --exclude='*/m5out' -czf - . | rx "mkdir -p $O/code $O/logs && tar -xzf - -C $O/code"
  { echo "snapshot $(date -u '+%F %T') UTC from $(hostname) (Mac HEAD $(git -C "$REPO" rev-parse --short HEAD) + uncommitted working tree)"
    cd "$REPO" && shasum -a 256 STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py twostage_lp.py \
      testrun.py pipeline.py STAGE3_gem5/check_ld.py STAGE3_gem5/gem5_common.py STAGE1_alloy/models/proposed/ultimate/loosepin/{stage15lp.py,stream_fp.py} \
      STAGE1_alloy/models/{STT_6_u_lpP,Recon_6_u_lpP,Footprint_6_u_lpP,STT_6_u_core_ri,Recon_6_u_core_ri,Footprint_6_u_core_ri}.als $D/*.jsonc
  } | rx "cat > $O/code/SNAPSHOT.txt"
  rx "cd $O/code/STAGE1_alloy && ls alloy6.jar a6RandomModels.class a6CountModels.class" | tee -a "$LOG" || log "WARNING: alloy jar/classes missing in snapshot"
  log "snapshot written"
fi
for F in "$@"; do
  case "$F" in STT_6_u|Recon_6_u|Footprint_6_u) ;; *) log "unknown family $F"; exit 1;; esac
  if rx "test -f $O/cores/${F}_core_ri/COPIED"; then log "cores for $F present"
  elif [ "$F" = Footprint_6_u ]; then
    COPYFILE_DISABLE=1 tar -czf - --include='loosepin_regen/stage1/out/Footprint_6_u_core_ri/k[23]/stage1_xml/*' \
      @"$REPO/experiments/2026-11-10_footprint_vs_amulet/data/footprint_vs_amulet_20261110_corpus.tar.gz" \
      | rx "mkdir -p $O/cores/Footprint_6_u_core_ri && tar -xzf - --strip-components=4 -C $O/cores/Footprint_6_u_core_ri"
    n=$(rx "ls $O/cores/Footprint_6_u_core_ri/k*/stage1_xml/*.xml | wc -l")
    rx "echo copied $(date -u '+%F %T') from Mac experiments/2026-11-10_footprint_vs_amulet data tarball, $n core xml > $O/cores/Footprint_6_u_core_ri/COPIED"
    log "Footprint cores copied: $n (expect 1411)"
  else
    $SSH cafe2 "docker exec gem5_dev tar -C /tests/simspect_alloy_20261109u/out -cf - ${F}_core_ri" | rx "mkdir -p $O/cores && tar -xf - -C $O/cores"
    n=$(rx "find $O/cores/${F}_core_ri -name 'inst-*.txt' | wc -l")
    rx "echo copied $(date -u '+%F %T') from cafe2:/tests/simspect_alloy_20261109u/out/${F}_core_ri, $n core .txt files > $O/cores/${F}_core_ri/COPIED"
    log "cores copied for $F: $n"
  fi
  rx "tmux has-session -t bc_alloy 2>/dev/null || tmux new-session -d -s bc_alloy -n ctl"
  if rx "tmux list-windows -t bc_alloy -F '#W' | grep -qx $F"; then log "skip $F (window exists)"; continue; fi
  WS=$O/ws_${F}${WS_SUFFIX:-}
  rx "tmux new-window -d -t bc_alloy -n $F 'cd $O/code && echo START \$(date -u) >> $O/logs/alloy_$F.out && python3 -u twostage_lp.py --config $D/twostage_$F.jsonc --ws $WS --alloy-only >> $O/logs/alloy_$F.out 2>&1; echo EXIT rc=\$? \$(date -u) >> $O/logs/alloy_$F.out'"
  log "LAUNCHED $F ws=$WS"
done
if ! rx "tmux list-windows -t bc_alloy -F '#W' | grep -qx diskwatch"; then
  H=$((MIN / 2))
  rx "tmux new-window -d -t bc_alloy -n diskwatch 'while true; do f=\$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); echo \$(date -u +%FT%T) free=\${f}G >> $O/logs/diskwatch.log; if [ \"\$f\" -lt $H ]; then echo \$(date -u +%FT%T) STOP below ${H}G >> $O/logs/diskwatch.log; pkill -f \"$O/\"; break; fi; sleep 300; done'"
  log "diskwatch started (stop below ${H}G)"
fi
log "END"
