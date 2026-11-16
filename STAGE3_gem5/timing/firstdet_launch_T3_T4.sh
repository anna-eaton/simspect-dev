#!/bin/bash
# firstdet-simspect (2026-11-09): SimSpect first detection at AMuLeT parity on the shared corpus
# STT_6_fv2fp_rmw. Waits for the corpus READY file (written by firstdet-cleanupspec), then runs
# T3 (SpecLFB warm), T3c (SpecLFB cold), T4 (amulet-STT warm) with timing_driver.py (seed 20261109),
# then classify_hits.py (H-PAD exclusion + STT S1_xmm4). Log: launch.log next to this script.
# XMIT_KINDS (env, fanoutgaps 2026-11-09): passed to timing_driver --xmit-kinds; default all (every transmitter kind, as every
# earlier row ran: the configs' "filter": {"xmit_kind": "ld"} key was never read). XMIT_KINDS=ld keeps load transmitters only.
set -u
B=/tests/simspect_alloy_20261108
C=$B/code_20261109
TS=$B/testsets_twostage/STT_6_fv2fp_rmw
R=$B/results_fv2
LOG=$R/firstdet/launch.log
N=${N:-3000}; P=${P:-10}
export TMPDIR=/tmp   # H-STK: same TMPDIR path length as the campaigns
log(){ echo "[$(date -u '+%F %T')] $*" >> $LOG; }
log "START pid=$$ N=$N P=$P"
t0=$(date +%s)
while [ ! -e $TS/READY ]; do
  if [ $(( $(date +%s) - t0 )) -gt 28800 ]; then log "GAVE UP: no READY after 8 h"; exit 2; fi
  sleep 120
done
log "READY found: $(head -c 400 $TS/READY | tr '\n' ' ')"
run(){ # row defense
  local row=$1 def=$2 out=$R/${1}_STT_6_fv2fp_rmw__firstdet
  log "launch $row -> $out"
  ( cd $C && python3 STAGE3_gem5/timing/timing_driver.py --code-root $C \
      --config runconfigs/amulet_parity_fv2fp_rmw/${row}_STT_6_fv2fp_rmw.jsonc --model STT_6_fv2fp_rmw \
      --out $out --seed 20261109 --n $N --parallel $P --xmit-kinds ${XMIT_KINDS:-all} > $out.driver.stdout 2>&1 ; echo "rc=$?" >> $out.driver.stdout )
  log "$row driver done: $(tail -1 $out.driver.stdout)"
  ( cd $C && python3 STAGE3_gem5/timing/classify_hits.py $out --defense $def --stage3 $C/STAGE3_gem5 --testset $TS \
      > $out/classify.stdout 2>&1 ; echo "rc=$?" >> $out/classify.stdout )
  log "$row classify done: $(tail -1 $out/classify.stdout)"
}
mkdir -p $R
run T3 speclfb &
run T3c speclfb &
run T4 stt &
wait
log "END"
