#!/bin/bash
# firstdet_cs_launch.sh: CleanupSpec first detection on the RMW fanout corpus (firstdet-cleanupspec, 2026-11-09).
# Runs T2 (warm) and T2c (cold = AMuLeT parity) on cafe3 gem5_dev, 12 workers each, then classifies.
#   bash firstdet_cs_launch.sh <N> [rows (default "T2c T2")] [workers per row (default 12)]
#   (inside gem5_dev; resumable: timing_driver skips finished idx). T2r = cache_setup random (added 2026-11-09).
# Logs: <out>/driver.log, <out>/classify.log, <out>/classify_cs_rmw.log, and $LOGDIR/firstdet_cs_launch.log.
# TMPDIR is pinned to /tmp: gem5 SE copies the --cmd path onto the stack, so a different TMPDIR length shifts
# stack lines and changes verdicts (BUGS.md H-STK).
# XMIT_KINDS (env, fanoutgaps 2026-11-09): passed to timing_driver --xmit-kinds; default all (every transmitter kind, as every
# earlier row ran: the configs' "filter": {"xmit_kind": "ld"} key was never read). XMIT_KINDS=ld keeps load transmitters only.
set -u
N=${1:-4000}
ROWS=${2:-"T2c T2"}
PAR=${3:-12}
ROOT=/tests/simspect_alloy_20261108
CODE=$ROOT/code_20261109
TS=$ROOT/testsets_twostage/STT_6_fv2fp_rmw
LOGDIR=$ROOT/bugwork/firstdet_cs
export TMPDIR=/tmp
mkdir -p $LOGDIR
L() { echo "[$(date '+%F %T')] $*" | tee -a $LOGDIR/firstdet_cs_launch.log; }
run() {   # $1 = row (T2 / T2c)
  local row=$1 out=$ROOT/results_fv2/${1}_STT_6_fv2fp_rmw__timing_cafe3
  L "START $row N=$N out=$out"
  python3 $CODE/STAGE3_gem5/timing/timing_driver.py --code-root $CODE \
      --config runconfigs/amulet_parity_fv2/${row}_STT_6_fv2fp_rmw.jsonc --model STT_6_fv2fp_rmw \
      --out $out --seed 20261109 --n $N --parallel $PAR --xmit-kinds ${XMIT_KINDS:-all} >> $LOGDIR/${row}_driver.out 2>&1
  L "$row driver rc=$?"
  python3 $CODE/STAGE3_gem5/timing/classify_hits.py $out --defense cleanupspec --stage3 $CODE/STAGE3_gem5 \
      > $out/classify_hits.out 2>&1
  L "$row classify_hits rc=$?"
  python3 $CODE/STAGE3_gem5/timing/classify_cs_rmw.py $out --rmw-stems $TS/rmw_stems.tsv --testset $TS \
      > $out/classify_cs_rmw.out 2>&1
  L "$row classify_cs_rmw rc=$?"
}
for r in $ROWS; do run $r & done
wait
L "ALL DONE"
