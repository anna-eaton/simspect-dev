#!/usr/bin/env bash
# regen_stt_fpralt.sh -- UV1 regeneration with vector-register routing as an ALTERNATIVE concretization (xmm-fix-agent, 2026-11-16).
# PREPARED, NOT LAUNCHED. Anna runs it FROM THE MAC (agents may not write to the nodes without her go-ahead).
#
# What: re-concretize the 26,954 Stage-1.5 programs of STT_6_u_core_lpP_fv3 (cafe3, read-only source
#   /tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/xml, 26,954 XMLs, checked 2026-11-16) with the new recipe
#   runconfigs/bigcorpus_20261115/stage2_final_A_fpralt.jsonc (= frozen recipe A + fpr.p 0.5: each consumed load is routed through an xmm
#   register with probability 0.5; parsexml.py pass5_emit_llvm docstring "p") into corpus STT_6_u_nov10_s2Afpralt (53,908 tests), then score
#   it with E3 (stt-master, whole corpus) and E4 (AMuLeT STT, 25% sample, as in bigcorpus) and gate it with STAGE3_gem5/bugs/classify.py
#   (UV1 = S1_xmm4: the gated hit's transmitter slice touches %xmm4).
# Where: OUT=/tests/fpralt_20261116 on cafe3 (has the XMLs; 1.4 TB free, idle on 2026-11-16 07:47 PT). cafe1 can take shards after
#   `copy-corpus` (it has no copy of the fv3 XMLs; its /tests was 89% full, 188 GB free, on 2026-11-16).
# Steps (in order; each is idempotent / refuses when its output exists):
#   scripts/fpralt_20261116/regen_stt_fpralt.sh code cafe3        # snapshot of the Mac tree -> $OUT/code (+ SNAPSHOT.txt, parsexml sha check)
#   scripts/fpralt_20261116/regen_stt_fpralt.sh s2                # Stage 2 on cafe3 (tmux fa, window s2; ~15-20 min); READY at the end
#   scripts/fpralt_20261116/regen_stt_fpralt.sh gem5 cafe3 E3 12 0-11   # E3 whole corpus, 12 shards x 4 jobs (tmux fa_shards)
#   scripts/fpralt_20261116/regen_stt_fpralt.sh gem5 cafe3 E4 4 0-3     # E4 25%, 4 shards x 4 jobs
#   scripts/fpralt_20261116/regen_stt_fpralt.sh status cafe3      # progress (EXIT lines per shard)
#   scripts/fpralt_20261116/regen_stt_fpralt.sh gate              # after every shard logged EXIT: gate JSONs $OUT/gate_E{3,4}_fpralt.json
# Optional cafe1 split (faster): `code cafe1`, then after READY `copy-corpus`, then e.g. E3 with --k 24: `gem5 cafe3 E3 24 0-11` and
#   `gem5 cafe1 E3 24 12-23`, E4 on cafe1 `gem5 cafe1 E4 4 0-3`; when cafe1's shards are done `collect` (copies cafe1's results to cafe3), then `gate`.
# Runtime estimate (2026-11-16): Stage 2 ~20k CPU-s (0.73 CPU-s/program, bigcorpus STT PROVENANCE) = ~15-20 min at 48 jobs. gem5: the configs
#   leave gem5.fast_path unset, which is the fast path since 2026-11-16 (COMMANDS.md "Fast path"; verdict-identical, 200/200 on STT E3), at about
#   1.3-1.7 CPU-s/test on an idle node (paper results.tex): E3 53,908 tests ~20-25 CPU-h, E4 13,477 tests ~5-6 CPU-h (production path ~2-3.5
#   CPU-s/test, about 2x that). cafe3 alone (64 workers): ~30-40 min of gem5 after Stage 2, ~1 h end to end (up to ~1.5 h on the production path).
#   With cafe1 helping: ~45 min end to end.
# Logs: Mac ~/Library/Logs/simspect/fpralt_regen.log (every step); node $OUT/logs/{s2.out,shard_<row>_sh<s>.log,gate.log,diskwatch.log},
#   $OUT/ws_stt/nov10_stream.log (Stage 2 per chunk, stderr of failures).
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
O=${OUT:-/tests/fpralt_20261116}; MIN=${MIN_FREE_GB:-80}
CORPUS=STT_6_u_nov10_s2Afpralt
SRC=/tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/xml
RECIPE=runconfigs/bigcorpus_20261115/stage2_final_A_fpralt.jsonc
D=runconfigs/fpralt_20261116
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/fpralt_regen.log
log(){ echo "$(date -u '+%F %T') [${STEP:-?}] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ local n=$1; shift; $SSH "$n" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
disk(){ local n=$1 f; f=$(rx "$n" "df -BG --output=avail /tests | tail -1 | tr -dc 0-9"); log "$n /tests free ${f}G (min $MIN)"
        [ "$f" -ge "$MIN" ] || { log "ABORT: low disk on $n"; exit 1; }; }
STEP=${1:?step: code|s2|copy-corpus|gem5|status|collect|gate}; shift || true
MAC_PX=$(shasum -a 256 "$REPO/STAGE2_compilation/parsexml.py" | cut -d' ' -f1)
case "$STEP" in
code)
  N=${1:?node}; disk "$N"
  grep -q 'fpr_p:' "$REPO/STAGE2_compilation/parsexml.py" || { log "ABORT: Mac parsexml.py has no fpr.p"; exit 1; }
  if rx "$N" "test -f $O/code/SNAPSHOT.txt"; then
    NP=$(rx "$N" "sha256sum $O/code/STAGE2_compilation/parsexml.py | cut -d' ' -f1")
    [ "$NP" = "$MAC_PX" ] && { log "$N snapshot exists, parsexml sha matches ($NP)"; exit 0; }
    log "ABORT: $N $O/code exists with parsexml $NP != Mac $MAC_PX (move it aside by hand)"; exit 1
  fi
  COPYFILE_DISABLE=1 tar -C "$REPO" --exclude=./testsets --exclude=./testsets_twostage --exclude=./results --exclude=./experiments \
      --exclude=./build --exclude=./.git --exclude=./archive --exclude=./paper_figures --exclude=./analysis --exclude=./.obsidian \
      --exclude=./oldsimspectstuff --exclude='*/__pycache__' --exclude='*/m5out' -czf - . | rx "$N" "mkdir -p $O/code $O/logs $O/testsets && tar -xzf - -C $O/code"
  { echo "snapshot $(date -u '+%F %T') UTC from $(hostname) (Mac HEAD $(git -C "$REPO" rev-parse --short HEAD) + uncommitted working tree) for the fpralt UV1 regen"
    cd "$REPO" && shasum -a 256 STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py \
      STAGE1_alloy/models/proposed_twophase/stage2_sharded.py scripts/bigcorpus_20261115/nov10_stream.py scripts/fpralt_20261116/shard_fpralt.py \
      testrun.py pipeline.py STAGE3_gem5/check_ld.py STAGE3_gem5/check_br.py STAGE3_gem5/gem5_common.py STAGE3_gem5/bugs/classify.py \
      "$RECIPE" $D/*.jsonc
  } | rx "$N" "cat > $O/code/SNAPSHOT.txt"
  NP=$(rx "$N" "sha256sum $O/code/STAGE2_compilation/parsexml.py | cut -d' ' -f1")
  [ "$NP" = "$MAC_PX" ] || { log "ABORT: copied parsexml sha $NP != Mac $MAC_PX"; exit 1; }
  log "$N snapshot written ($O/code, parsexml $NP)"
  ;;
s2)
  N=cafe3; disk "$N"
  rx "$N" "test -f $O/code/SNAPSHOT.txt" || { log "ABORT: run 'code cafe3' first"; exit 1; }
  rx "$N" "test \$(ls $SRC | grep -c 'xml\$') -eq 26954" || { log "ABORT: $SRC does not have 26,954 XMLs"; exit 1; }
  rx "$N" "test ! -e $O/testsets/$CORPUS/READY" || { log "corpus already READY"; exit 0; }
  rx "$N" "tmux has-session -t fa 2>/dev/null || tmux new-session -d -s fa -n ctl"
  rx "$N" "tmux list-windows -t fa -F '#W' | grep -qx s2" && { log "window fa:s2 exists (running?)"; exit 0; }
  rx "$N" "mkdir -p $O/testsets/$CORPUS && echo 'corpus $CORPUS = the STT_6_u_core_lpP_fv3 Stage-1.5 programs ($SRC, read-only) re-concretized with $RECIPE (recipe A + fpr.p 0.5) by scripts/bigcorpus_20261115/nov10_stream.py (its READY line says Footprint: hard-coded text, ignore). xmm-fix-agent 2026-11-16.' > $O/testsets/$CORPUS/PROVENANCE_fpralt.txt"
  rx "$N" "tmux new-window -d -t fa -n s2 'cd $O/code && echo START \$(date -u) >> $O/logs/s2.out && nice -n 5 python3 -u scripts/bigcorpus_20261115/nov10_stream.py --src $SRC --cfg $RECIPE --ts $O/testsets --final $CORPUS --ws $O/ws_stt --jobs 48 >> $O/logs/s2.out 2>&1; echo EXIT rc=\$? \$(date -u) >> $O/logs/s2.out'"
  if ! rx "$N" "tmux list-windows -t fa -F '#W' | grep -qx diskwatch"; then
    H=$((MIN / 2))
    rx "$N" "tmux new-window -d -t fa -n diskwatch 'while true; do f=\$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); echo \$(date -u +%FT%T) free=\${f}G >> $O/logs/diskwatch.log; if [ \"\$f\" -lt $H ]; then echo \$(date -u +%FT%T) STOP below ${H}G >> $O/logs/diskwatch.log; pkill -f \"$O/\"; break; fi; sleep 300; done'"
  fi
  log "LAUNCHED Stage 2 on $N (tmux fa:s2, log $O/logs/s2.out)"
  ;;
copy-corpus)
  F=${1:-cafe3}; T=${2:-cafe1}; disk "$T"
  rx "$F" "test -f $O/testsets/$CORPUS/READY" || { log "ABORT: $CORPUS not READY on $F"; exit 1; }
  rx "$F" "tar -C $O/testsets -cf - $CORPUS" | rx "$T" "mkdir -p $O/testsets $O/logs && tar -xf - -C $O/testsets"
  a=$(rx "$F" "find $O/testsets/$CORPUS -type f | wc -l"); b=$(rx "$T" "find $O/testsets/$CORPUS -type f | wc -l")
  log "copied $CORPUS $F -> $T: files $a vs $b"; [ "$a" = "$b" ] || { log "ABORT: file counts differ"; exit 1; }
  ;;
gem5)
  N=${1:?node}; R=${2:?row E3|E4}; K=${3:?k}; MINE=${4:?mine e.g. 0-11}; disk "$N"
  rx "$N" "test -f $O/testsets/$CORPUS/READY" || [ "${FORCE:-0}" = 1 ] || { log "ABORT: $CORPUS not READY on $N (FORCE=1 shards only the stems published so far)"; exit 1; }
  NP=$(rx "$N" "sha256sum $O/code/STAGE2_compilation/parsexml.py | cut -d' ' -f1")
  [ "$NP" = "$MAC_PX" ] || log "WARNING: node parsexml $NP != Mac $MAC_PX (only matters for Stage 2, which ran on cafe3)"
  rx "$N" "cd $O/code && python3 scripts/fpralt_20261116/shard_fpralt.py --corpus $CORPUS --config $D/${R}_$CORPUS.jsonc --name ${R}_$CORPUS --k $K --mine $MINE --nice ${NICE:-5}" | tee -a "$LOG"
  log "LAUNCHED $R shards $MINE of $K on $N (tmux fa_shards, logs $O/logs/shard_${R}_${CORPUS}_sh*.log)"
  ;;
status)
  N=${1:-cafe3}
  rx "$N" "cd $O; tail -2 logs/s2.out 2>/dev/null; tail -1 ws_stt/nov10_stream.log 2>/dev/null; ls testsets/$CORPUS/READY 2>/dev/null; for f in logs/shard_*.log; do [ -f \$f ] && echo \"\$f: \$(grep -c ' new (of ' \$f) passes, \$(tail -1 \$f | cut -c1-120)\"; done; uptime; df -h /tests | tail -1" | tee -a "$LOG"
  ;;
collect)
  F=${1:-cafe1}; T=${2:-cafe3}
  rx "$F" "cd $O/code/results && tar -cf - E3_${CORPUS}_sh* E4_${CORPUS}_sh* 2>/dev/null" | rx "$T" "mkdir -p $O/code/results && tar -xf - -C $O/code/results"
  log "collected $F shard results into $T:$O/code/results"
  ;;
gate)
  N=cafe3
  rx "$N" "cd $O/code && python3 STAGE3_gem5/bugs/classify.py gate --code-root $O/code --campaigns $D/campaigns.json --testsets-root $O/testsets --names E3_$CORPUS --fraction 1.0 --examples 1000000 --json $O/gate_E3_fpralt.json >> $O/logs/gate.log 2>&1 && python3 STAGE3_gem5/bugs/classify.py gate --code-root $O/code --campaigns $D/campaigns.json --testsets-root $O/testsets --names E4_$CORPUS --fraction 0.25 --examples 1000000 --json $O/gate_E4_fpralt.json >> $O/logs/gate.log 2>&1; tail -40 $O/logs/gate.log" | tee -a "$LOG"
  log "gate done: $N:$O/gate_E{3,4}_fpralt.json (S1_xmm4 = UV1); check _merge lines for MISSING / DUPLICATES"
  ;;
*) log "unknown step $STEP"; exit 1;;
esac
