#!/usr/bin/env bash
# run_inspv8.sh (agent stt-int-fig, 2026-11-16) -- integer version of STT_6_u_core_lpP_fv3 inst-023734 (the running example of ISCA-27
# Figs. 2, 4 and 5) and its single-test gem5 reruns. Runs INSIDE cafe3 gem5_dev, nice 19, one process at a time.
# Why it builds the twin itself: inst-023734 is a test of STT_6_u_core_lpP_fv3 (recipe v3, parsexml 6e5c5238), not of the big corpus
# STT_6_u_core_lpP_s2A, so the inttwin corpus STT_6_u_core_lpP_s2Aint has no twin of it (its inst-023734 does not exist: s2A has 15,184
# stems, and no s2A program has this program's Stage-1.5 fingerprint, checked with alloy_solver_order.make_fingerprinter).
# Steps (argument: code | s2 | gem5 | all):
#  code  copy the two code snapshots into $W, results/ excluded: code_s2 = loosepin_regen/code_eval (parsexml 6e5c5238 and batch_generate
#        3fc8a94f = the code_hashes in STT_6_u_core_lpP_fv3/PROVENANCE.json), code_s3 = /tests/inttwin_20261116/code (the code that scored
#        E3_STT_6_u_core_lpP_s2A_int; gem5_common 9f67f809, no resolved gate).
#  s2    Stage 2 of xml/inst-023734 with fv3's recipe runconfigs/regen_lp_20261110/stage2_fv3.jsonc (sha256 1c24c5e8...) through
#        pipeline.py llvm + asm, both modes (as the corpus): vec = recipe with only paths.testset_dir changed (must reproduce the corpus
#        .ll/.s/.ann.json byte for byte), int = the same with ONLY fpr.enabled false (the inttwin rule). Neither fv3 post-pass touches this
#        stem (not in rmw_stems.tsv / jmp_stems.tsv). Then cmp vs corpus and pairdiff.py vec vs int.
#  gem5  four single-test runs, mode mispredict_not_taken, through pipeline.py gem5 (what testrun.py runs per batch), with run_queue.py's env
#        (TMPDIR=/tmp, SIMSPECT_GEM5_TIMEOUT_S=900, SIMSPECT_GEM5_MAX_TICK=2e9): {int, vec} x {E3 = runconfigs/inttwin_20261116/
#        E3_STT_6_u_core_lpP_s2A_int.jsonc, E1 = the same with E1's gem5.binary/config_script/cpu_type/scheme from
#        runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc}; only paths, pipeline.keep_tmp=true, branch_modes=[not_taken], gem5.jobs=1
#        changed. Timing = the campaign's per-test grid draw, cache setup = random_all's per-test draw (both seeded by the stem).
# Log: /tests/inspector_v8_20261116/logs/run.log
set -uo pipefail
W=/tests/inspector_v8_20261116; STEM=inst-023734; MODE=mispredict_not_taken
FV3=/tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3
MV=STT_INSPV8_fv3vec; MI=STT_INSPV8_fv3int
mkdir -p $W/logs $W/configs $W/results $W/s2check $W/raw
exec > >(tee -a $W/logs/run.log) 2>&1
STEP=${1:-all}
echo "=== START step=$STEP $(date -u +%FT%TZ) host=$(hostname) pid=$$"
if [ "$STEP" = code ] || [ "$STEP" = all ]; then
  for P in "code_s2 /tests/simspect_alloy_20261108/loosepin_regen/code_eval" "code_s3 /tests/inttwin_20261116/code"; do
    set -- $P; rm -rf $W/$1; mkdir -p $W/$1
    (cd $2 && tar cf - --exclude=./results --exclude=./logs --exclude=__pycache__ .) | (cd $W/$1 && tar xf -); echo "copied $2 -> $W/$1 rc=$?"
  done
  sha256sum $W/code_s2/STAGE2_compilation/parsexml.py $W/code_s2/STAGE2_compilation/batch_generate.py $W/code_s2/STAGE2_compilation/compile_annotate.py \
    $W/code_s2/pipeline.py $W/code_s3/pipeline.py $W/code_s3/testrun.py $W/code_s3/STAGE3_gem5/gem5_common.py $W/code_s3/STAGE3_gem5/check_ld.py \
    $W/code_s3/STAGE3_gem5/cache_setup.py $W/code_s3/runconfigs/regen_lp_20261110/stage2_fv3.jsonc \
    $W/code_s3/runconfigs/inttwin_20261116/E3_STT_6_u_core_lpP_s2A_int.jsonc $W/code_s3/runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc
  md5sum /work/stt-master/build/X86/gem5.opt /work/gem5-recon-modded/build/X86/gem5.opt
fi
if [ "$STEP" = s2 ] || [ "$STEP" = all ]; then
  for M in $MV $MI; do T=$W/ts_${M##*_}; rm -rf $T; mkdir -p $T/$M/xml; cp -p $FV3/xml/$STEM.xml $FV3/xml/$STEM.txt $T/$M/xml/; done
  sha256sum $FV3/xml/$STEM.xml
  grep -c "^$STEM\b" $FV3/rmw_stems.tsv $FV3/jmp_stems.tsv
  cd $W/code_s2 || exit 1
  python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "."); import pipeline
W = "/tests/inspector_v8_20261116"
c = pipeline.load_config(Path(f"{W}/code_s3/runconfigs/regen_lp_20261110/stage2_fv3.jsonc"))
c["paths"]["testset_dir"] = f"{W}/ts_fv3vec"; json.dump(c, open(f"{W}/configs/S2_vec.json", "w"), indent=1)
c["paths"]["testset_dir"] = f"{W}/ts_fv3int"; c["fpr"]["enabled"] = False; json.dump(c, open(f"{W}/configs/S2_int.json", "w"), indent=1)
print("S2 configs written; int differs from vec only in testset_dir and fpr.enabled")
PY
  export TMPDIR=/tmp
  for V in vec int; do M=STT_INSPV8_fv3$V
    for PH in llvm asm; do echo "--- s2 $V $PH $(date -u +%FT%TZ)"; nice -n 19 python3 pipeline.py $PH --model $M --config $W/configs/S2_$V.json --force; echo "s2 $V $PH rc=$?"; done
  done
  for MO in mispredict_not_taken mispredict_taken; do
    for D in "llvm .ll" "asm .s" "ann .ann.json"; do set -- $D
      F=$FV3/$MO/$1/$STEM$2; G=$W/ts_fv3vec/$MV/$MO/$1/$STEM$2
      if [ -e "$F" ]; then cmp -s "$F" "$G" && echo "IDENTICAL vec-vs-corpus $MO/$1" || { echo "DIFFERENT vec-vs-corpus $MO/$1"; diff "$F" "$G" | head -20; }; else echo "corpus has no $MO/$1/$STEM$2"; fi
    done
  done
  python3 $W/code_s3/scripts/inttwin_20261116/pairdiff.py $W/ts_fv3vec/$MV $W/ts_fv3int/$MI --json $W/s2check/pairdiff.json --show 5; echo "pairdiff rc=$?"
  for MO in mispredict_not_taken mispredict_taken; do echo "--- diff vec int $MO/asm"; diff $W/ts_fv3vec/$MV/$MO/asm/$STEM.s $W/ts_fv3int/$MI/$MO/asm/$STEM.s; done
  grep -n "xmm" $W/ts_fv3int/$MI/*/asm/$STEM.s || echo "int version: no xmm anywhere"
  sha256sum $W/ts_fv3*/*/*/{asm,ann,llvm}/$STEM.* 2>/dev/null
fi
if [ "$STEP" = gem5 ] || [ "$STEP" = all ]; then
  cd $W/code_s3 || exit 1
  python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "."); import pipeline
W = "/tests/inspector_v8_20261116"
base = pipeline.load_config(Path("runconfigs/inttwin_20261116/E3_STT_6_u_core_lpP_s2A_int.jsonc"))
e1 = pipeline.load_config(Path("runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc"))["gem5"]
for v in ("int", "vec"):
    for e in ("E3", "E1"):
        c = json.loads(json.dumps(base))
        c["paths"].update(testset_dir=f"{W}/ts_fv3{v}", results_dir=f"{W}/results", results_name=f"INSPV8_{e}_{v}")
        c["pipeline"]["keep_tmp"] = True; c["speculation"]["branch_modes"] = ["mispredict_not_taken"]; c["gem5"]["jobs"] = 1
        if e == "E1":
            c["gem5"].update({k: e1[k] for k in ("binary", "config_script", "cpu_type", "scheme")})
        json.dump(c, open(f"{W}/configs/INSPV8_{e}_{v}.json", "w"), indent=1)
print("timing-grid draw (unresolved, resolved):", pipeline._timing_grid_point("inst-023734", base["sweep"]))
sys.path.insert(0, "STAGE3_gem5"); import cache_setup as cs
for b in ("/work/stt-master/build/X86/gem5.opt", "/work/gem5-recon-modded/build/X86/gem5.opt"):
    print("random_all draw on", b, ":", cs.resolve("random_all", "inst-023734", None, b), "of", cs.allowed_setups(b), "seed", cs.current_seed())
PY
  export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 SIMSPECT_GEM5_MAX_TICK=2000000000
  for RUN in E3_int E1_int E3_vec E1_vec; do V=${RUN#*_}; M=STT_INSPV8_fv3$V
    echo "=== gem5 $RUN $(date -u +%FT%TZ)"; ls -d /tmp/gem5_${STEM}_* 2>/dev/null > $W/logs/tmp_before_$RUN.txt
    SIMSPECT_FAST_PATH_LOG=$W/logs/fastpath_$RUN.log nice -n 19 python3 pipeline.py gem5 --model $M --config $W/configs/INSPV8_$RUN.json --force; echo "$RUN rc=$?"
    ls -d /tmp/gem5_${STEM}_* 2>/dev/null | sort | comm -13 <(sort $W/logs/tmp_before_$RUN.txt) - > $W/logs/tmp_new_$RUN.txt; echo "kept workdir(s): $(cat $W/logs/tmp_new_$RUN.txt)"
    R=$W/results/INSPV8_$RUN/$MODE; cat $R/window-results.json; cat $R/sweep/manifest.json 2>/dev/null
    for D in $(cat $W/logs/tmp_new_$RUN.txt); do tar czf $W/raw/${RUN}_$(basename $D).tgz -C /tmp $(basename $D) && echo "saved $W/raw/${RUN}_$(basename $D).tgz"; done
  done
fi
echo "=== END step=$STEP $(date -u +%FT%TZ)"
