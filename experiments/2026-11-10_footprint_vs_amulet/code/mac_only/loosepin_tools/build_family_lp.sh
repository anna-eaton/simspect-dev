#!/usr/bin/env bash
# build_family_lp.sh -- regen-lp (2026-11-10): everything after the Alloy phase for ONE family, on a cafe node in gem5_dev.
#   1. wait until every draft's pipeline.py xml has EXITed (launch_regen_lp.log)
#   2. merge_lp.py: drafts in the order given, fingerprint dedup  -> $WS/<family>/xml/   (+ SOLVER_ORDER.json provenance)
#   3. census_lp.py on the merged corpus and on each draft         -> $WS/census/<family>{,__<draft>}.json
#   4. Stage 2 fv2fp (stage2_sharded.py, config stage2_<family>_lp_fv2fp.jsonc, both branch modes)
#                                                                  -> $TS/<family>_lp_fv2fp/
#   5. make_rmw_corpus.py --select eligible --fraction 0.5 --seed 20261109 --complete -> $TS/<family>_lp_fv2fp_rmw/
#   6. make_jmp_corpus.py --p 0.5 --seed 20261109                  -> $TS/<family>_lp_fv2fp_rmw_jmp/  + READY (summary)
# Log: $WS/logs/build_<family>.log (timestamps, rc of every step, counts); each tool also writes its own log in its dst.
# Usage: build_family_lp.sh <family> <draft> [<draft> ...]     e.g. build_family_lp.sh STT_6_u STT_6_u_lpP STT_6_u_lpA_b2
set -u
FAM=$1; shift; DRAFTS=("$@")
B=/tests/simspect_alloy_20261108; WS=$B/loosepin_regen; C=$WS/code; TS=$B/testsets_twostage
L=$WS/logs/build_$FAM.log; J=${JOBS:-48}; REV=${REV:-264adea+uncommitted}
export TMPDIR=/tmp
log(){ echo "[$(date -u '+%F %T')] $*" >> "$L"; }
log "START family=$FAM drafts=${DRAFTS[*]} jobs=$J"
for d in "${DRAFTS[@]}"; do
  until grep -q " EXIT $d " "$WS/logs/launch_regen_lp.log"; do sleep 60; done
  log "xml phase done: $(grep " EXIT $d " "$WS/logs/launch_regen_lp.log" | tail -1)"
done
ins=(); for d in "${DRAFTS[@]}"; do ins+=("$WS/runs/$d/xml"); done
python3 "$WS/lp/merge_lp.py" --family "$FAM" --out "$WS/$FAM/xml" "${ins[@]}" >> "$L" 2>&1; rc=$?
log "merge rc=$rc kept=$(ls "$WS/$FAM/xml" | grep -c '^inst-.*\.xml$')"; [ $rc -ne 0 ] && { log "ABORT merge failed"; exit 1; }
mkdir -p "$WS/census"
python3 "$WS/lp/census_lp.py" --jobs 16 --json "$WS/census/$FAM.json" "$WS/$FAM/xml" > "$WS/census/$FAM.txt" 2>> "$L"; log "census merged rc=$?"
( for d in "${DRAFTS[@]}"; do python3 "$WS/lp/census_lp.py" --jobs 8 --json "$WS/census/${FAM}__$d.json" "$WS/runs/$d/xml" > "$WS/census/${FAM}__$d.txt" 2>> "$L"; echo "[$(date -u '+%F %T')] census $d rc=$?" >> "$L"; done ) &
M=${FAM}_lp_fv2fp
if ls "$TS/$M/xml"/inst-*.xml >/dev/null 2>&1; then log "ABORT $TS/$M/xml already populated"; exit 1; fi
mkdir -p "$TS/$M" && cp -r "$WS/$FAM/xml" "$TS/$M/xml"
( cd "$C" && python3 STAGE1_alloy/models/proposed_twophase/stage2_sharded.py --config runconfigs/regen_lp_20261110/stage2_${M}.jsonc \
    --model "$M" --jobs "$J" --first-fraction 0.02 ) > "$WS/logs/stage2_$M.out" 2>&1; rc=$?
nt=$(ls "$TS/$M/mispredict_not_taken/asm" 2>/dev/null | grep -c '\.s$'); tk=$(ls "$TS/$M/mispredict_taken/asm" 2>/dev/null | grep -c '\.s$')
log "stage2 rc=$rc asm not_taken=$nt taken=$tk"; [ $rc -ne 0 ] && { log "ABORT stage2 failed"; exit 1; }
python3 "$C/STAGE2_compilation/make_rmw_corpus.py" --repo-root "$C" --src "$TS/$M" --dst "$TS/${M}_rmw" --fraction 0.5 --seed 20261109 \
    --select eligible --complete --jobs "$J" --git-rev "$REV" > "$WS/logs/rmw_$M.out" 2>&1; rc=$?
log "rmw rc=$rc"; [ $rc -ne 0 ] && { log "ABORT rmw failed"; exit 1; }
python3 "$C/STAGE2_compilation/make_jmp_corpus.py" --repo-root "$C" --src "$TS/${M}_rmw" --dst "$TS/${M}_rmw_jmp" --p 0.5 --seed 20261109 \
    --jobs "$J" --git-rev "$REV" > "$WS/logs/jmp_$M.out" 2>&1; rc=$?
log "jmp rc=$rc"; [ $rc -ne 0 ] && { log "ABORT jmp failed"; exit 1; }
D=$TS/${M}_rmw_jmp
n_nt=$(ls "$D/mispredict_not_taken/asm" | grep -c '\.s$'); n_t=$(ls "$D/mispredict_taken/asm" | grep -c '\.s$')
n_x=$(ls "$WS/$FAM/xml" | grep -c '^inst-.*\.xml$'); n_rmw=$(( $(wc -l < "$D/rmw_stems.tsv") )); n_jmp=$(( $(wc -l < "$D/jmp_stems.tsv") ))
{ echo "READY $(date -u +%FT%TZ) regen-lp: ${M}_rmw_jmp = merged loose-pin corpus $WS/$FAM/xml (${DRAFTS[*]}, fingerprint-deduped; provenance $WS/$FAM/xml/SOLVER_ORDER.json) -> Stage 2 runconfigs/regen_lp_20261110/stage2_${M}.jsonc (= E3_STT_6_fv2fp options) -> make_rmw_corpus --select eligible p0.5 seed 20261109 --complete -> make_jmp_corpus p0.5 seed 20261109"
  echo "xml programs $n_x; tests not_taken $n_nt, taken $n_t; rmw_stems.tsv lines $n_rmw; jmp_stems.tsv lines $n_jmp (header lines included); code $C (CODE_SNAPSHOT.txt, SHA256SUMS)"; } > "$D/READY"
log "READY $D ($n_x programs, $n_nt + $n_t tests)"
wait
log "END"
