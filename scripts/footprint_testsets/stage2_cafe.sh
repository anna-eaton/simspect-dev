#!/usr/bin/env bash
# Stage 2 (llvm + asm) for the footprint-model testsets, run inside cafe2's gem5_dev container from the workspace
# code snapshot (/tests/footprint_20261110/code). Compiles the InvisiSpec member of each family in full, checks
# Stage-2 determinism by recompiling a 200-test sample under the CleanupSpec and SpecLFB names and comparing
# byte for byte, then gives CleanupSpec and SpecLFB their testsets as hard links of the InvisiSpec files.
# Usage: scripts/footprint_testsets/stage2_cafe.sh      Log: <code>/logs/stage2_footprint.log
set -uo pipefail
cd "$(dirname "$0")/../.."
CODE="$(pwd)"; mkdir -p logs; LOG="$CODE/logs/stage2_footprint.log"
log(){ echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') $*" | tee -a "$LOG"; }
log "START host=$(hostname) code=$CODE parsexml_sha256=$(sha256sum STAGE2_compilation/parsexml.py | cut -c1-16)"
stage2(){ # model
  local m="$1" c="runconfigs/footprint_20261110/gen_$1.jsonc"
  for ph in llvm asm; do
    log "RUN $ph $m"
    if python3 pipeline.py "$ph" --model "$m" --config "$c" >>"$CODE/logs/stage2_${m}_${ph}.log" 2>&1; then
      log "DONE $ph $m: $(grep -E '^\[(llvm|asm)\].*Done' "$CODE/logs/stage2_${m}_${ph}.log" | tr '\n' ' ')"
    else
      log "ERROR $ph $m exit=$? (see logs/stage2_${m}_${ph}.log)"; return 1
    fi
  done
}
for fam in "" "_stl"; do
  lead="InvisiSpec_6$fam"
  stage2 "$lead" || continue
  # determinism check on a 200-test sample under the other two names
  for d in CleanupSpec SpecLFB; do
    m="${d}_6$fam"; chk="testsets_detcheck/$m"
    rm -rf "$chk"; mkdir -p "$chk/xml"
    ls testsets/$lead/xml | grep '\.xml$' | awk 'NR%50==1' | head -200 | while read f; do ln "testsets/$lead/xml/$f" "$chk/xml/$f"; done
    sed 's#"testset_dir": "testsets"#"testset_dir": "testsets_detcheck"#' "runconfigs/footprint_20261110/gen_$m.jsonc" > "$chk/gen.jsonc"
    for ph in llvm asm; do python3 pipeline.py "$ph" --model "$m" --config "$chk/gen.jsonc" >>"$CODE/logs/stage2_detcheck_${m}.log" 2>&1; done
    ndiff=0; ncmp=0
    for mode_dir in "$chk"/*/; do
      mode=$(basename "$mode_dir"); [ "$mode" = xml ] && continue
      for sub in llvm asm ann; do
        for f in "$mode_dir/$sub"/*; do
          [ -f "$f" ] || continue; ncmp=$((ncmp+1))
          cmp -s "$f" "testsets/$lead/$mode/$sub/$(basename "$f")" || { ndiff=$((ndiff+1)); [ $ndiff -le 5 ] && log "DIFF $m $mode/$sub/$(basename "$f")"; }
        done
      done
    done
    log "DETCHECK $m vs $lead: compared $ncmp files, $ndiff differ"
    if [ "$ndiff" -eq 0 ] && [ "$ncmp" -gt 0 ]; then
      rm -rf "testsets/$m"; cp -al "testsets/$lead" "testsets/$m"
      log "LINKED testsets/$m -> hard links of testsets/$lead ($(find testsets/$m -name '*.s' | wc -l) .s files)"
    else
      log "NOT LINKED $m (determinism check failed or empty); compile it separately"
    fi
  done
done
log "END"
