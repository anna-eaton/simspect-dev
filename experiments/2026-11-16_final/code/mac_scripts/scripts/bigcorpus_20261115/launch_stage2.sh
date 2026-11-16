#!/usr/bin/env bash
# BIGCORPUS COPY (agent bigcorpus 2026-11-15) of scripts/overnight_20261111/launch_stage2.sh: OUT /tests/bigcorpus_20261115, configs runconfigs/bigcorpus_20261115,
# tmux bc_s2, disk check on /tests, Footprint_6_u allowed (uses the non-SPT stage2_final_{A,B}). The vocab-agent gate is kept (both DONE lines exist).
# Run: scripts/bigcorpus_20261115/launch_stage2.sh cafe3 Footprint_6_u STT_6_u Recon_6_u
# launch_stage2.sh -- X2b of the overnight plan: Stage-2 concretization of the X2a Alloy output, recipe A (fillers only) and then
# recipe B (A + chain interleaving, NEW never-evaluated), with stream_fp.py --no-postpasses. Run FROM THE MAC.
# Usage: scripts/overnight_20261111/launch_stage2.sh <node> <family> [<family> ...]      (FORCE=1 skips the vocab-agent gate)
# Gate (Anna 2026-11-12): refuses unless claudenotes.md has a DONE line from both ilv-vocab and abs-vocab and
#   runconfigs/overnight_20261111/stage2_final_{A,B}.jsonc exist (make_stage2_final.py --keys ...).
# Refreshes STAGE2_compilation/, runconfigs/overnight_20261111/ and the loosepin stream_fp.py in the node snapshot (<OUT>/code;
#   old copies kept as <OUT>/code_pre_s2_<ts>.tgz; SNAPSHOT.txt gets a line with the new sha256s), then tmux session bc_s2,
#   window <family>: stream_fp A (corpus <family>_core_lpP_s2A) then stream_fp B (<family>_core_lpP_s2B) over the same
#   <OUT>/ws_<family>/runs15/<family>_lpP (same merge order, so A and B have the same stems). stream_fp resumes from its state.json.
# Logs: <OUT>/logs/s2_<family>.out, <OUT>/ws_<family>/logs/stream_<corpus>.log, ~/Library/Logs/simspect/bigcorpus_s2_<node>.log.
set -euo pipefail
NODE=${1:?node}; shift
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=${OUT:-/tests/bigcorpus_20261115}; D=runconfigs/bigcorpus_20261115
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/bigcorpus_s2_${NODE}.log
log(){ echo "$(date -u '+%F %T') [$NODE] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
log "START families=$*"
if [ "${FORCE:-0}" != 1 ]; then
  grep -Eq '^[0-9-]+[^—]*— ilv-vocab .*— DONE' "$REPO/claudenotes.md" || { log "GATE: ilv-vocab not DONE in claudenotes.md"; exit 2; }
  grep -Eq '^[0-9-]+[^—]*— abs-vocab .*— DONE' "$REPO/claudenotes.md" || { log "GATE: abs-vocab not DONE in claudenotes.md"; exit 2; }
fi
for R in A B; do [ -f "$REPO/$D/stage2_final_$R.jsonc" ] || { log "GATE: $D/stage2_final_$R.jsonc missing (run make_stage2_final.py)"; exit 2; }; done
# verify-x1 2026-11-12: SPT_6_u uses the _spt variants make_stage2_final.py writes (splices off, no invertible forms; DECIDE SPT-VOCAB)
case " $* " in *" SPT_6_u "*) for R in A B; do [ -f "$REPO/$D/stage2_final_${R}_spt.jsonc" ] || { log "GATE: $D/stage2_final_${R}_spt.jsonc missing"; exit 2; }; done;; esac
free=$(rx "df -BG --output=avail /tests | tail -1 | tr -dc 0-9"); log "disk /tests free ${free}G"
[ "$free" -ge "${MIN_FREE_GB:-80}" ] || { log "ABORT: low disk"; exit 1; }
ts=$(date -u +%Y%m%d_%H%M%S)
# verify-x1 2026-11-12: never overwrite the node's Stage-2 / STAGE3_gem5 code under a running bc_s2 or bc_gem5 window (stream_fp starts a
# new stage2_sharded per batch and testrun re-imports the checkers, so a refresh mid-run mixes old and new code in one corpus/campaign).
busy=$(rx "for s in bc_s2 bc_gem5; do tmux list-windows -t \$s -F \"\$s:#W\" 2>/dev/null; done | grep -v ':ctl\$' || true")
if [ -n "$busy" ]; then
  key="STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py $D/stage2_final_A.jsonc $D/stage2_final_B.jsonc"
  here=$(cd "$REPO" && shasum -a 256 $key | awk '{print $1}' | tr '\n' ' ')
  there=$(rx "cd $O/code && sha256sum $key | awk '{print \$1}' | tr '\n' ' '" || true)
  if [ "$here" != "$there" ]; then
    log "ABORT: running windows [$(echo $busy)] and the Mac Stage-2 code/configs differ from the node snapshot; a refresh now would contaminate them. Start the new family after they end, or use OUT=<new dir>."
    exit 3
  fi
  log "running windows [$(echo $busy)]; node snapshot already matches the Mac Stage-2 code/configs, no refresh"
else
rx "cd $O && tar -czf code_pre_s2_$ts.tgz code/STAGE2_compilation code/$D code/STAGE1_alloy/models/proposed/ultimate/loosepin/stream_fp.py"
COPYFILE_DISABLE=1 tar -C "$REPO" --exclude='*/__pycache__' --exclude='*/m5out' --exclude='./STAGE2_compilation/proposed/pre_vocab_fv4_20261111' \
  -czf - ./STAGE2_compilation ./$D ./STAGE1_alloy/models/proposed/ultimate/loosepin/stream_fp.py ./STAGE1_alloy/models/proposed_twophase/stage2_sharded.py \
  ./pipeline.py ./STAGE3_gem5 | rx "tar -xzf - -C $O/code"
( cd "$REPO" && echo "s2 refresh $ts UTC (Mac HEAD $(git rev-parse --short HEAD) + working tree)" && shasum -a 256 STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py $D/stage2_final_*.jsonc ) | rx "cat >> $O/code/SNAPSHOT.txt"
log "snapshot refreshed ($ts)"
fi
rx "tmux has-session -t bc_s2 2>/dev/null || tmux new-session -d -s bc_s2 -n ctl"
for F in "$@"; do
  rx "test -f $O/ws_$F/runs15/${F}_lpP/SUMMARY.json" || log "note: Stage 1.5 for $F not finished yet; stream_fp merges as jobs end and writes READY after SUMMARY.json"
  if rx "tmux list-windows -t bc_s2 -F '#W' | grep -qx $F"; then log "skip $F (window exists)"; continue; fi
  CMD=""; SFX=""; [ "$F" = SPT_6_u ] && SFX=_spt
  for R in A B; do
    C=$O/ws_$F/cfg/stage2_final_${R}${SFX}_stream.jsonc
    rx "mkdir -p $O/ws_$F/cfg && sed -e 's#\"testset_dir\": *\"[^\"]*\"#\"testset_dir\": \"$O/testsets\"#' -e '0,/\"jobs\": *[0-9]*/s//\"jobs\": 24/' $O/code/$D/stage2_final_${R}${SFX}.jsonc > $C"
    CMD="$CMD python3 -u STAGE1_alloy/models/proposed/ultimate/loosepin/stream_fp.py --s15 $O/ws_$F/runs15/${F}_lpP --base-name ${F}_lp_s2${R}_base --final-name ${F}_core_lpP_s2${R} --cfg $C --code $O/code --ts-dir $O/testsets --ws $O/ws_$F --stage1-logs stage1/logs/${F}_core_ri__x.log --family-label $F --interval 120 --jobs 24 --min-batch 200 --max-batch 1500 --no-postpasses --git-rev bigcorpus_20261115 >> $O/logs/s2_$F.out 2>&1; echo EXIT_$R rc=\$? \$(date -u) >> $O/logs/s2_$F.out;"
  done
  rx "tmux new-window -d -t bc_s2 -n $F 'cd $O/code && export TMPDIR=/tmp && $CMD'"
  log "LAUNCHED Stage 2 A then B for $F"
done
log "END"
