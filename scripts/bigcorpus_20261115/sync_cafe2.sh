#!/usr/bin/env bash
# sync_cafe2.sh -- big corpus 2026-11-15 (agent bigcorpus): give cafe2 (the only node with /work/gem5-recon-ruby3 and /work/gem5-spt)
# the code snapshot and a finished corpus from cafe3, streamed through the Mac (node->node ssh is not assumed).
# Run FROM THE MAC:  scripts/bigcorpus_20261115/sync_cafe2.sh code            (once: cafe3 <OUT>/code -> cafe2 <OUT>/code)
#                    scripts/bigcorpus_20261115/sync_cafe2.sh corpus <model>  (e.g. STT_6_u_core_lpP_s2A; copies everything but READY,
#                                                                             then READY last, so gem5_row.sh on cafe2 starts only on a full copy)
# Refuses when cafe2 /tests has < MIN_FREE_GB (default 40) free or the corpus is not READY on cafe3. Log ~/Library/Logs/simspect/bigcorpus_sync_cafe2.log
set -euo pipefail
O=${OUT:-/tests/bigcorpus_20261115}; MIN=${MIN_FREE_GB:-40}
LOG=~/Library/Logs/simspect/bigcorpus_sync_cafe2.log; mkdir -p ~/Library/Logs/simspect
log(){ echo "$(date -u '+%F %T') $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
r3(){ $SSH cafe3 "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
r2(){ $SSH cafe2 "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
free=$(r2 "df -BG --output=avail /tests | tail -1 | tr -dc 0-9"); log "cafe2 /tests free ${free}G (min $MIN)"
[ "$free" -ge "$MIN" ] || { log "ABORT low disk on cafe2"; exit 1; }
case "${1:?code|corpus}" in
code)
  r3 "tar -C $O -czf - --exclude=code/results code" | r2 "mkdir -p $O/logs && tar -xzf - -C $O"
  r2 "echo synced from cafe3 \$(date -u) >> $O/code/SNAPSHOT.txt"; log "code synced" ;;
corpus)
  M=${2:?model}
  r3 "test -f $O/testsets/$M/READY" || { log "ABORT: $M not READY on cafe3"; exit 2; }
  sz=$(r3 "du -sBG $O/testsets/$M | cut -f1 | tr -dc 0-9"); log "$M size ${sz}G"
  [ $((free - sz)) -ge "$MIN" ] || { log "ABORT: copying ${sz}G would leave < ${MIN}G on cafe2"; exit 1; }
  r3 "tar -C $O/testsets -czf - --exclude=$M/READY $M" | r2 "mkdir -p $O/testsets && tar -xzf - -C $O/testsets"
  r3 "cat $O/testsets/$M/READY" | r2 "cat > $O/testsets/$M/READY"
  log "corpus $M synced: cafe3 $(r3 "ls $O/testsets/$M/mispredict_not_taken/asm | wc -l") vs cafe2 $(r2 "ls $O/testsets/$M/mispredict_not_taken/asm | wc -l") not_taken .s files" ;;
esac
