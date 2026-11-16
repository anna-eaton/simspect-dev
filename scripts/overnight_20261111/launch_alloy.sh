#!/usr/bin/env bash
# launch_alloy.sh -- X2a of the overnight 2026-11-11 plan (Anna 2026-11-12: "start doing alloy but wait for the monolithic
# insertion passes ... before doing the concretization phase"). Run FROM THE MAC. For each family it starts Stage 1b
# (Stage 1.5 loose-pin Alloy, twostage_lp.py --alloy-only) inside the node's gem5_dev container, in tmux session ovn_alloy.
#
# Usage: scripts/overnight_20261111/launch_alloy.sh <node> <family> [<family> ...]     family in STT_6_u Recon_6_u SPT_6_u
#   e.g. launch_alloy.sh cafe3 STT_6_u SPT_6_u ;  launch_alloy.sh cafe1 Recon_6_u
# Env: MIN_FREE_GB (default 80; refuse to start below, the watcher stops the run below MIN_FREE_GB/2), OUT (/tests/overnight_20261111).
#
# Steps (each idempotent, so rerunning is safe):
#  1. disk check on the node's /scr.
#  2. code snapshot: the Mac working tree (code only; no testsets/results/experiments/build/.git) -> <OUT>/code on the node,
#     once; SNAPSHOT.txt records time, Mac HEAD and sha256 of the key files. A second run reuses it.
#  3. SPT only: installs proposed/ultimate/SPT_6_u_core_ri.als and loosepin/SPT_6_u_lpPc.als as models/SPT_6_u_core_ri.als and
#     models/SPT_6_u_lpP.als IN THE NODE SNAPSHOT (never in the repo; pending DECIDE 'approve SPT_6_u_lpP').
#  4. Stage-1 cores: cafe2 /tests/simspect_alloy_20261109u/out/<family>_core_ri -> <OUT>/cores/ on the node (tar stream via the Mac), once.
#  5. tmux window <family> runs twostage_lp.py --config runconfigs/overnight_20261111/twostage_<family>.jsonc --ws <OUT>/ws_<family>
#     --alloy-only (log <OUT>/ws_<family>/logs/twostage_lp.log + <OUT>/logs/alloy_<family>.out), and window diskwatch stops every
#     run of this plan when /scr free < MIN_FREE_GB/2 (log <OUT>/logs/diskwatch.log). Skips a family whose window exists.
# Resume: stage15lp.py itself does not resume; after a crash start a NEW ws (WS_SUFFIX=_r2) and give stream_fp.py both
#   runs15 dirs (--s15 a b), which dedups by fingerprint. Launcher log: ~/Library/Logs/simspect/overnight_alloy_<node>.log.
set -euo pipefail
NODE=${1:?node}; shift
REPO=$(cd "$(dirname "$0")/../.." && pwd)
O=${OUT:-/tests/overnight_20261111}; MIN=${MIN_FREE_GB:-80}
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/overnight_alloy_${NODE}.log
log(){ echo "$(date -u '+%F %T') [$NODE] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
log "START families=$* out=$O repo=$REPO"

free=$($SSH "$NODE" "df -BG --output=avail /scr | tail -1 | tr -dc 0-9")
log "disk /scr free ${free}G (min $MIN)"
[ "$free" -ge "$MIN" ] || { log "ABORT: /scr free ${free}G < ${MIN}G"; exit 1; }

if rx "test -f $O/code/SNAPSHOT.txt"; then
  log "code snapshot exists: $(rx "head -1 $O/code/SNAPSHOT.txt")"
else
  log "copying code snapshot"
  COPYFILE_DISABLE=1 tar -C "$REPO" --exclude=./testsets --exclude=./testsets_twostage --exclude=./results --exclude=./experiments \
      --exclude=./build --exclude=./.git --exclude=./archive --exclude=./paper_figures --exclude=./analysis --exclude=./.obsidian \
      --exclude='*/__pycache__' --exclude='*/m5out' -czf - . | rx "mkdir -p $O/code $O/logs && tar -xzf - -C $O/code"
  {
    echo "snapshot $(date -u '+%F %T') UTC from $(hostname) $REPO (Mac HEAD $(git -C "$REPO" rev-parse --short HEAD) + uncommitted working tree)"
    cd "$REPO" && shasum -a 256 STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py \
      twostage_lp.py STAGE1_alloy/models/proposed/ultimate/loosepin/{stage15lp.py,stream_fp.py,SPT_6_u_lpPc.als} \
      STAGE1_alloy/models/{STT_6_u_lpP,Recon_6_u_lpP,STT_6_u_core_ri,Recon_6_u_core_ri}.als STAGE1_alloy/models/proposed/ultimate/SPT_6_u_core_ri.als \
      runconfigs/overnight_20261111/*.jsonc
  } | rx "cat > $O/code/SNAPSHOT.txt"
  log "snapshot written"
fi

for F in "$@"; do
  case "$F" in STT_6_u|Recon_6_u|SPT_6_u) ;; *) log "unknown family $F"; exit 1;; esac
  if [ "$F" = SPT_6_u ] && [ "${SPT_LPP_OK:-0}" != 1 ]; then
    log "SKIP SPT_6_u: the but-8 lpP model is not to be used until Anna decides SPT-BOUND (protcheck 2026-11-12: 6-step untaint fixpoint, false hits at 8); SPT_LPP_OK=1 overrides"; continue
  fi
  if [ "$F" = SPT_6_u ] && ! rx "test -f $O/code/STAGE1_alloy/models/SPT_6_u_lpP.als"; then
    rx "cd $O/code/STAGE1_alloy/models && cp proposed/ultimate/SPT_6_u_core_ri.als SPT_6_u_core_ri.als && \
        { printf '%s\n' '// NOT APPROVED (overnight-exp 2026-11-11): installed in this node snapshot only, from proposed/ultimate/loosepin/SPT_6_u_lpPc.als (make_loosepin.py --base SPT_6_u.als --n 8 --operands 16 --intbits 6 --minimality prod --committed required --brcap 0 --pin core; defense block byte-identical).' \
        '// Pending DECIDEs in URGENT_TODO.md: approve SPT_6_u_lpP; SPT-BOUND (6-step untaint fixpoint at but 8).' '// ============================================================================='; \
          cat proposed/ultimate/loosepin/SPT_6_u_lpPc.als; } > SPT_6_u_lpP.als"
    log "SPT models installed in the node snapshot"
  fi
  if rx "test -f $O/cores/${F}_core_ri/COPIED"; then
    log "cores for $F present"
  else
    log "copying cores ${F}_core_ri from cafe2"
    $SSH cafe2 "docker exec gem5_dev tar -C /tests/simspect_alloy_20261109u/out -cf - ${F}_core_ri" | rx "mkdir -p $O/cores && tar -xf - -C $O/cores"
    n=$(rx "find $O/cores/${F}_core_ri -name 'inst-*.txt' | wc -l")
    rx "echo copied $(date -u '+%F %T') from cafe2:/tests/simspect_alloy_20261109u/out/${F}_core_ri, $n core .txt files > $O/cores/${F}_core_ri/COPIED"
    log "cores copied: $n"
  fi
  rx "tmux has-session -t ovn_alloy 2>/dev/null || tmux new-session -d -s ovn_alloy -n ctl"
  if rx "tmux list-windows -t ovn_alloy -F '#W' | grep -qx $F"; then log "skip $F (window exists)"; continue; fi
  WS=$O/ws_${F}${WS_SUFFIX:-}
  rx "tmux new-window -d -t ovn_alloy -n $F 'cd $O/code && echo START \$(date -u) >> $O/logs/alloy_$F.out && python3 -u twostage_lp.py --config runconfigs/overnight_20261111/twostage_$F.jsonc --ws $WS --alloy-only >> $O/logs/alloy_$F.out 2>&1; echo EXIT rc=\$? \$(date -u) >> $O/logs/alloy_$F.out'"
  log "LAUNCHED $F ws=$WS"
done

if ! rx "tmux list-windows -t ovn_alloy -F '#W' | grep -qx diskwatch"; then
  H=$((MIN / 2))
  rx "tmux new-window -d -t ovn_alloy -n diskwatch 'while true; do f=\$(df -BG --output=avail /scr 2>/dev/null | tail -1 | tr -dc 0-9); [ -z \"\$f\" ] && f=\$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); echo \$(date -u +%FT%T) free=\${f}G >> $O/logs/diskwatch.log; if [ \"\$f\" -lt $H ]; then echo \$(date -u +%FT%T) STOP below ${H}G: killing twostage_lp/stage15lp/a6 of $O >> $O/logs/diskwatch.log; pkill -f \"$O/ws_\" ; break; fi; sleep 300; done'"
  log "diskwatch started (stop below ${H}G)"
fi
rx "tmux list-windows -t ovn_alloy -F '#W'" | tee -a "$LOG"
log "END"
