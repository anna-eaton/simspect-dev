#!/bin/bash
# firstdet_full_launch.sh: first detection with cache_setup `full` (cache-full, 2026-11-09) on the shared
# fanout corpus STT_6_fv2fp_rmw, cafe3 gem5_dev. Rows: T1f InvisiSpec-Futuristic, T2f CleanupSpec, T3f SpecLFB
# (runconfigs/amulet_parity_fv2fp_rmw/T{1,2,3}f_STT_6_fv2fp_rmw.jsonc). Same method as the other firstdet rows:
# timing_driver.py --seed 20261109 (same order), then classify_hits.py --testset (H-PAD + SETUP exclusion),
# then classify_cs_rmw.py for CleanupSpec.
#   MODE=smoke bash firstdet_full_launch.sh   # N=20 per row, every trace kept, + full_smoke_check.py
#   bash firstdet_full_launch.sh              # N=3000 (T2f: N_T2F, default 4000), real runs
# Env: ROWS (default "T1f:invisispec T2f:cleanupspec T3f:speclfb"), N, N_T2F, P (workers per row, default 16).
# Resumable (timing_driver skips finished idx). Logs: $R/firstdet_full/launch_<mode>.log, and per run dir
# driver.log, classify.log/classify.stdout, classify_cs_rmw.log, full_smoke_check.json (smoke).
# TMPDIR=/tmp: gem5 SE copies the --cmd path onto the stack, so its length changes stack lines (BUGS.md H-STK).
# XMIT_KINDS (env, fanoutgaps 2026-11-09): passed to timing_driver --xmit-kinds; default all (every transmitter kind, as every
# earlier row ran: the configs' "filter": {"xmit_kind": "ld"} key was never read). XMIT_KINDS=ld keeps load transmitters only.
set -u
B=/tests/simspect_alloy_20261108
C=$B/code_20261109
TS=$B/testsets_twostage/STT_6_fv2fp_rmw
R=$B/results_fv2
MODE=${MODE:-real}
P=${P:-16}
if [ "$MODE" = smoke ]; then N=${N:-20}; N_T2F=${N_T2F:-$N}; SUF=__fullsmoke; EXTRA=--keep-all-traces
else N=${N:-3000}; N_T2F=${N_T2F:-4000}; SUF=__firstdet; EXTRA=; fi
export TMPDIR=/tmp
mkdir -p $R/firstdet_full
LOG=$R/firstdet_full/launch_${MODE}.log
log(){ echo "[$(date -u '+%F %T')] $*" >> $LOG; }
log "START pid=$$ MODE=$MODE N=$N N_T2F=$N_T2F P=$P ROWS=${ROWS:-default}"
[ -e $TS/READY ] || { log "no READY in $TS"; exit 2; }
run(){ # row defense
  local row=$1 def=$2 out=$R/${1}_STT_6_fv2fp_rmw$SUF n=$N
  [ "$row" = T2f ] && n=$N_T2F
  log "launch $row n=$n -> $out"
  ( cd $C && python3 STAGE3_gem5/timing/timing_driver.py --code-root $C \
      --config runconfigs/amulet_parity_fv2fp_rmw/${row}_STT_6_fv2fp_rmw.jsonc --model STT_6_fv2fp_rmw \
      --out $out --seed 20261109 --n $n --parallel $P --xmit-kinds ${XMIT_KINDS:-all} $EXTRA > $out.driver.stdout 2>&1 ; echo "rc=$?" >> $out.driver.stdout )
  log "$row driver done: $(tail -1 $out.driver.stdout)"
  ( cd $C && python3 STAGE3_gem5/timing/classify_hits.py $out --defense $def --stage3 $C/STAGE3_gem5 --testset $TS \
      > $out/classify.stdout 2>&1 ; echo "rc=$?" >> $out/classify.stdout )
  log "$row classify_hits done: $(tail -1 $out/classify.stdout)"
  if [ "$def" = cleanupspec ]; then
    ( cd $C && python3 STAGE3_gem5/timing/classify_cs_rmw.py $out --rmw-stems $TS/rmw_stems.tsv --testset $TS \
        > $out/classify_cs_rmw.out 2>&1 ; echo "rc=$?" >> $out/classify_cs_rmw.out )
    log "$row classify_cs_rmw done: $(tail -1 $out/classify_cs_rmw.out)"
  fi
  if [ "$MODE" = smoke ]; then
    ( cd $C && python3 STAGE3_gem5/timing/full_smoke_check.py $out --stage3 $C/STAGE3_gem5 \
        --json $out/full_smoke_check.json > $out/full_smoke_check.out 2>&1 ; echo "rc=$?" >> $out/full_smoke_check.out )
    log "$row full_smoke_check: $(grep SUMMARY $out/full_smoke_check.out)"
  fi
}
for rd in ${ROWS:-T1f:invisispec T2f:cleanupspec T3f:speclfb}; do run ${rd%%:*} ${rd##*:} & done
wait
log "END"
