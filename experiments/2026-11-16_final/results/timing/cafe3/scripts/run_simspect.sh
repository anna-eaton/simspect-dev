#!/bin/bash
# TIME-1 (agent timing, 2026-11-15): dedicated SimSpect CPU timing for one AMuLeT-parity row on cafe2.
# Same harness as diligence check 6 (firstdet_stream.py -> timing_driver.run_one: per-test wait4 rusage of the whole
# pipeline.py gem5 process tree = build + gem5 + checker; gem5-only from TIMING_GEM5_LOG), on a fixed 1,000-pair random
# sample of the big corpus (sample/sample.tsv), 16 workers, pinned to CPUs 0-31 (one hardware thread per physical core).
# Usage (cafe2 gem5_dev): bash run_simspect.sh <T1g|T2g|T3g> [parallel=16] [corpus=bc|v3]
#   bc = big corpus Footprint_6_u_core_lpP_s2A, the 1,000-pair random sample (--only-file sample/sample.tsv), configs/<row>_time1.jsonc
#   v3 = the 2026-11-10 corpus Footprint_6_u_core_lpP_fv3 on cafe2, the first 1,000 of the seed-20261109 order (--seed-prefix 1000,
#        exactly diligence check 6's selection), configs/<row>_time1v3.jsonc
set -u
R=$1; P=${2:-16}; CORP=${3:-bc}; B=/tests/timing_20261115; C=$B/code
if [ "$CORP" = v3 ]; then MODEL=Footprint_6_u_core_lpP_fv3; CFG=$B/configs/${R}_time1v3.jsonc; SEL="--seed-prefix 1000"; OUT=$B/simspect/${R}_v3_p${P}
else MODEL=Footprint_6_u_core_lpP_s2A; CFG=$B/configs/${R}_time1.jsonc; SEL="--only-file $B/sample/sample.tsv --n-max 1000"; OUT=$B/simspect/${R}_p${P}; fi
mkdir -p $OUT
LOG=$OUT/run.log; exec > >(tee -a $LOG) 2>&1
export TMPDIR=/tmp
echo "=== TIME-1 SimSpect START $(date -u '+%F %T') row=$R corpus=$CORP model=$MODEL parallel=$P taskset=0-31 config=$CFG sel=[$SEL]"
md5sum $(python3 -c "import json,re,sys;t=open('$CFG').read();print(json.loads('\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('//')))['gem5']['binary'])")
bash $B/scripts/snap.sh "before $R"
cd $C && taskset -c 0-31 python3 STAGE3_gem5/timing/firstdet_stream.py --code-root $C --config $CFG \
   --model $MODEL --out $OUT --seed 20261109 --parallel $P $SEL --poll 30 > $OUT/stream.stdout 2>&1
rc=$?
bash $B/scripts/snap.sh "after $R"
echo "=== TIME-1 SimSpect END $(date -u '+%F %T') row=$R rc=$rc rows=$(wc -l < $OUT/results.jsonl)"
