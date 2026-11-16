#!/bin/bash
# Stage 2 (unchanged code snapshot code_20261109: parsexml + compile_annotate via pipeline.py llvm/asm, not_taken
# mode) on the loosepin random-seed XMLs, then the uv5-shape static scan. Read-only for the code; log $WS/logs/lp_stage2.log
WS=/tests/simspect_alloy_20261108/loosepin; CODE=/tests/simspect_alloy_20261108/code_20261109
LOG=$WS/logs/lp_stage2.log; echo "$(date -Is) START" >> $LOG
for m in "$@"; do
  T=$WS/stage2/testsets/$m; rm -rf $T; mkdir -p $T/xml
  n=0; for s in 1 2 3 default; do for f in $WS/out/$m/$s/inst-*.xml; do [ -e "$f" ] || continue; n=$((n+1)); [ $n -gt 600 ] && break 2; cp $f $T/xml/$(printf 'inst-%06d.xml' $n); done; done
  cat > $WS/stage2/cfg_$m.jsonc <<CFG
{"paths": {"alloy_stage": "$CODE/STAGE1_alloy", "models_dir": "$WS/models", "stage2_dir": "$CODE/STAGE2_compilation",
  "instruction_tables": "$CODE/STAGE2_compilation/instruction_tables/instructions.jsonc", "stage3_dir": "$CODE/STAGE3_gem5",
  "testset_dir": "$WS/stage2/testsets", "results_dir": "$WS/stage2/results", "results_name": "$m"},
 "alloy": {"max_instances": 1}, "speculation": {"control_flow": true, "data_flow": false, "branch_modes": ["mispredict_not_taken"]}}
CFG
  ( cd $CODE && python3 pipeline.py llvm --model $m --config $WS/stage2/cfg_$m.jsonc && python3 pipeline.py asm --model $m --config $WS/stage2/cfg_$m.jsonc ) > $WS/logs/lp_stage2_$m.out 2>&1
  echo "$(date -Is) $m rc=$? xml=$(ls $T/xml | wc -l) ll=$(ls $T/mispredict_not_taken/llvm/*.ll 2>/dev/null | wc -l) s=$(ls $T/mispredict_not_taken/asm/*.s 2>/dev/null | wc -l) ann=$(ls $T/mispredict_not_taken/ann 2>/dev/null | wc -l)" >> $LOG
  python3 $WS/lp/uv5_timing_scan.py $T mispredict_not_taken 100000 1 > $WS/stage2/uv5scan_$m.txt 2>&1
done
echo "$(date -Is) END" >> $LOG
