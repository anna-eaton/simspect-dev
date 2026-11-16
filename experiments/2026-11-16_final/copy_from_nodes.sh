#!/bin/bash
# Pull the final (2026-11-15/16) experiment outputs from cafe1/cafe2/cafe3 into this snapshot.
# Read-only on the nodes: every node command is `tar -cf -` to stdout (nothing written on the node).
# Skips bulk regenerable artifacts: raw/, traces/, work/ (per-test gem5 records and pipeview traces), *_base testsets (.ll),
# discard_* dirs, AMuLeT violation dirs (config0results*), the stopped STT/Recon rows. The UV5 traces are pulled separately.
# Run from the Mac:  bash copy_from_nodes.sh [step ...]   (steps: results timing uv5 data code; default all)
# Log: copy_from_nodes.log in this directory.
set -uo pipefail
S=$(cd "$(dirname "$0")" && pwd); LOG=$S/copy_from_nodes.log
exec > >(tee -a "$LOG") 2>&1
log() { echo "[$(date -u '+%F %T')] $*"; }
B=/tests/bigcorpus_20261115; T=/tests/timing_20261115
EX=(--exclude='*/raw' --exclude='*/traces' --exclude='*/work' --exclude='*.pid' --exclude='discard_*'
    --exclude='*/cs_evidence/diagnostics/traces' --exclude='__pycache__')
# pull <node> <base dir> <dest dir> <paths...>: stream a tar of paths (relative to base) into dest
pull() {
  local n=$1 base=$2 dest=$3; shift 3
  mkdir -p "$dest"
  local q; q=$(printf "%q " "${EX[@]}" "$@")
  log "pull $n:$base [$*] -> ${dest#$S/}"
  ssh -o ConnectTimeout=20 "$n" "docker exec gem5_dev bash -c 'cd $base && tar --ignore-failed-read -cf - $q'" | tar -xf - -C "$dest" \
    || log "ERROR: pull $n:$base [$*] failed (rc ${PIPESTATUS[*]})"
}
# xzpull <node> <base> <out.tar.xz> <tar args...>: compressed tarball streamed to the Mac (node-side xz into the pipe)
xzpull() {
  local n=$1 base=$2 out=$3; shift 3
  local q; q=$(printf "%q " "$@")
  log "xzpull $n:$base [$*] -> ${out#$S/}"
  ssh -o ConnectTimeout=20 "$n" "docker exec gem5_dev bash -c 'cd $base && tar -cf - $q | xz -T32 -6'" > "$out.part" \
    && mv "$out.part" "$out" || log "ERROR: xzpull $out failed"
  ls -la "$out" 2>/dev/null
}
steps=${*:-results timing uv5 data code}
log "start: steps = $steps"
for step in $steps; do case $step in
results)
  R=$S/results/bigcorpus
  # dirs whose traces ARE the evidence (UV5 verification reruns, uv5why reruns, E2w R-SA-8 traces, fast-path equivalence): full copy
  EXB=("${EX[@]}"); EX=(--exclude='*.pid' --exclude='__pycache__')
  pull cafe3 $B "$R/cafe3" uv5verify uv5why e2w
  pull cafe1 $B "$R/cafe1" uv5verify fp_equiv
  pull cafe2 $B "$R/cafe2" uv5verify
  EX=("${EXB[@]}")
  pull cafe3 $B "$R/cafe3" firstdet logs ws_nov10 race --exclude='uv5_rounds/c*/src' uv5_rounds \
       code/SNAPSHOT.txt code_fp/SNAPSHOT.txt ws_Footprint_6_u/cfg ws_Footprint_6_u/logs ws_Footprint_6_u/runs15/Footprint_6_u_lpP/MERGE_INPUTS.txt \
       ws_Footprint_6_u/runs15/Footprint_6_u_lpP/QUEUE_ORDER.json ws_Footprint_6_u/runs15/Footprint_6_u_lpP/SUMMARY.json ws_Footprint_6_u/runs15/Footprint_6_u_lpP/cores.json \
       ws_Footprint_6_u/runs15/Footprint_6_u_lpP/jobs.jsonl ws_Footprint_6_u/runs15/Footprint_6_u_lpP/stage15lp.log
  pull cafe3 $B/code "$R/cafe3/code_results_E2w" --exclude='_tmp_*' $(ssh cafe3 "docker exec gem5_dev bash -c 'cd $B/code && ls -d results/bc_E2w_*__2026*'")
  pull cafe1 $B "$R/cafe1" firstdet logs ws_nov10 ws_nov10B --exclude='uv5_rounds/c*/src' uv5_rounds code/SNAPSHOT.txt code_fp/SNAPSHOT.txt
  pull cafe2 $B "$R/cafe2" firstdet logs race ws_nov10B --exclude='uv5_rounds/c*/src' uv5_rounds code/SNAPSHOT.txt STOPPED.txt
  ;;
timing)
  for n in cafe3 cafe2; do
    D=$S/results/timing/$n
    pull $n $T "$D" --exclude='amulet/amulet-repo' --exclude='simspect_fast' --exclude='code' --exclude='*/config0results*' \
         --exclude='gen/*/*/xml' --exclude='testsets' .
    # the sampled corpus dir is only manifests + symlinks: keep its metadata files
    pull $n $T "$D/sample_corpus_meta" testsets/Footprint_6_u_core_lpP_s2A/MANIFEST.tsv testsets/Footprint_6_u_core_lpP_s2A/PROVENANCE.json testsets/Footprint_6_u_core_lpP_s2A/READY
    ssh $n "docker exec gem5_dev bash -c 'cd $T/amulet/amulet-repo && git rev-parse HEAD && git status --short && git diff --stat'" > "$D/amulet_repo_state.txt" 2>&1
  done
  ;;
uv5)
  # original first-detection traces + raw records of the 5 UV5 detections (3 programs)
  U=$S/results/uv5_traces
  EX=(--exclude='__pycache__'); pull cafe1 $B/firstdet "$U/cafe1" T2g_Footprint_6_u_core_lpP_s2A_cafe1/raw/mispredict_not_taken/inst-061878.json \
      T2g_Footprint_6_u_core_lpP_s2A_cafe1/traces/mispredict_not_taken/inst-061878.pipeview.txt.gz
  for m in mispredict_not_taken mispredict_taken; do
    EX=(--exclude='__pycache__'); pull cafe1 $B/firstdet "$U/cafe1" T2g_Footprint_6_u_nov10_c1_s2A/raw/$m/inst-023088_c1.json T2g_Footprint_6_u_nov10_c1_s2A/traces/$m/inst-023088_c1.pipeview.txt.gz
    EX=(--exclude='__pycache__'); pull cafe2 $B/firstdet "$U/cafe2" T2g_Footprint_6_u_nov10_c2_s2A/raw/$m/inst-023722_c2.json T2g_Footprint_6_u_nov10_c2_s2A/traces/$m/inst-023722_c2.pipeview.txt.gz
  done
  ;;
data)
  mkdir -p "$S/data"
  xzpull cafe3 $B/testsets "$S/data/corpus_main_Footprint_6_u_nov10_s2A.tar.xz" Footprint_6_u_nov10_s2A
  xzpull cafe3 $B/testsets "$S/data/corpus_extra_Footprint_6_u_core_lpP_s2A.tar.xz" Footprint_6_u_core_lpP_s2A
  xzpull cafe3 $B/testsets "$S/data/corpus_round_c3_compiled.tar.xz" --exclude=xml Footprint_6_u_nov10_c3_s2A
  xzpull cafe1 $B/testsets "$S/data/corpus_round_c1_compiled.tar.xz" --exclude=xml Footprint_6_u_nov10_c1_s2A
  xzpull cafe2 $B/testsets "$S/data/corpus_round_c2_compiled.tar.xz" --exclude=xml Footprint_6_u_nov10_c2_s2A
  xzpull cafe3 $B/testsets "$S/data/corpus_e2w_STT_6_u_core_lpP_s2A_and_gprtwin.tar.xz" STT_6_u_core_lpP_s2A STT_6_u_core_lpP_s2A_gprtwin
  xzpull cafe3 $B "$S/data/generation_extra_corpus_stage1_cores_stage15.tar.xz" cores/Footprint_6_u_core_ri ws_Footprint_6_u/runs15 ws_Footprint_6_u/stage1 ws_Footprint_6_u/cfg ws_Footprint_6_u/logs
  ;;
code)
  mkdir -p "$S/data"
  CX=(--exclude=code/results --exclude=code_fp/results --exclude=simspect_fast/results --exclude=code/generated --exclude=code_fp/generated --exclude=simspect_fast/generated --exclude=__pycache__ --exclude='*.pyc')
  xzpull cafe3 $B "$S/data/code_cafe3_bigcorpus_code.tar.xz" "${CX[@]}" code
  xzpull cafe3 $B "$S/data/code_cafe3_bigcorpus_code_fp.tar.xz" "${CX[@]}" code_fp
  xzpull cafe3 $T "$S/data/code_cafe3_timing_simspect_fast.tar.xz" "${CX[@]}" simspect_fast
  xzpull cafe2 $T "$S/data/code_cafe2_timing_code.tar.xz" "${CX[@]}" code
  for n in cafe3 cafe1 cafe2; do
    for d in $B/code $B/code_fp $T/code $T/simspect_fast; do
      ssh $n "docker exec gem5_dev bash -c 'test -d $d && cd $d && find . -path ./results -prune -o -path ./generated -prune -o -name __pycache__ -prune -o -type f ! -name \"*.pyc\" -print0 | sort -z | xargs -0 sha256sum'" \
        > "$S/code/sha256_${n}_$(echo $d | tr / _ | sed 's/^_tests_//').txt" 2>/dev/null
    done
  done
  find "$S/code" -name 'sha256_*.txt' -size 0 -delete
  ;;
esac; done
log "done: steps = $steps"
