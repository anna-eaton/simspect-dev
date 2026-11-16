#!/bin/bash
# firstdet-final (2026-11-10): unified AMuLeT-comparison first detection, STREAMING (Anna: "stream it").
# Three firstdet_stream.py consumers (InvisiSpec T1rt, CleanupSpec T2rt, SpecLFB T3rt: AMuLeT parity configs +
# cache_setup random_all + per-test random timing) on the Footprint_6_u core lpP fv3 corpus as regen-lp writes it,
# plus a classify loop (classify_hits / classify_cs_rmw / firstdet_report every CLS_EVERY s).
# X_<row> = extra firstdet_stream args (e.g. X_T2rt="--partition 0/2"); HOST_TAG = suffix of the run dir (cafe1 second consumer).
# Usage (cafe3 gem5_dev):  bash firstdet_final_launch.sh start|classify-loop|stop
# Logs: $F/launch.log, $F/<row>/driver.log, $F/<row>/classify.stdout, $F/report/report_<UTC>.{json,md}
set -u
B=/tests/simspect_alloy_20261108
F=$B/firstdet_final
C=$F/code
MODEL=${MODEL:-Footprint_6_u_core_lpP_fv3}
TS=$B/testsets_twostage/$MODEL
P=${P:-16}
CLS_EVERY=${CLS_EVERY:-1500}
GEN=${GEN_CPU_PER_TEST:-}
export TMPDIR=/tmp   # H-STK
LOG=$F/launch.log
log(){ echo "[$(date -u '+%F %T')] $*" >> $LOG; }
ROWS=${ROWS:-"T1rt:invisispec T2rt:cleanupspec T3rt:speclfb"}   # final protocol: ROWS="T1g:invisispec T2g:cleanupspec T3g:speclfb"
R1=$(echo $ROWS | tr " " "\n" | grep invisispec | cut -d: -f1); R2=$(echo $ROWS | tr " " "\n" | grep cleanupspec | cut -d: -f1); R3=$(echo $ROWS | tr " " "\n" | grep speclfb | cut -d: -f1)
dir(){ echo $F/${1}_$MODEL${HOST_TAG:+_$HOST_TAG}; }
case "${1:-start}" in
start)   # env P (default workers), P_T1rt/P_T2rt/P_T3rt and S_T1rt/S_T3rt (sample fraction) per row; ONLY="T2rt" to start a subset
  for rd in $ROWS; do
    case " ${ONLY:-$R1 $R2 $R3} " in *" ${rd%%:*} "*) ;; *) continue ;; esac
    row=${rd%%:*}; out=$(dir $row); mkdir -p $out
    xa=$(eval echo \${X_$row:-}); xa=${xa//\$F/$F}   # expand a literal $F in X_<row> (2026-11-10 resume bug: '$F/...' reached --exclude-file)
    ( cd $C && nohup python3 STAGE3_gem5/timing/firstdet_stream.py --code-root $C \
        --config runconfigs/firstdet_final_20261110/${row}_Footprint_6_u_core_lpP_fv3.jsonc --model $MODEL \
        --out $out --seed 20261109 --parallel $(eval echo \${P_$row:-$P}) --sample-frac $(eval echo \${S_$row:-1}) \
        $xa --poll 180 >> $out/stream.stdout 2>&1 & echo $! > $out/stream.pid )
    log "started $row pid=$(cat $out/stream.pid) P=$(eval echo \${P_$row:-$P}) sample_frac=$(eval echo \${S_$row:-1}) extra=[$xa] out=$out"
  done ;;
classify-once|classify-loop)
  while true; do
    log "classify pass start"
    for rd in $ROWS; do (
      row=${rd%%:*}; def=${rd##*:}; out=$(dir $row)
      if [ -d ${out}_cafe1 ]; then   # split run (cafe1 second consumer, synced here): classify the merged dir
        m=$F/${row}_${MODEL}_merged
        ( cd $C && python3 STAGE3_gem5/timing/firstdet_merge.py $m $out ${out}_cafe1 >> $LOG 2>&1 )
        out=$m
      fi
      [ -s $out/results.jsonl ] || exit 0
      ( cd $C && python3 STAGE3_gem5/timing/classify_hits.py $out --defense $def --stage3 $C/STAGE3_gem5 \
          --testset $TS --jobs ${CLS_JOBS:-12} --incremental > $out/classify.stdout 2>&1; echo "rc=$?" >> $out/classify.stdout )
      log "$row classify: $(tail -1 $out/classify.stdout)"
      if [ $def = cleanupspec ]; then
        if [ -s $TS/rmw_stems.tsv ]; then
          ( cd $C && python3 STAGE3_gem5/timing/classify_cs_rmw.py $out --rmw-stems $TS/rmw_stems.tsv --testset $TS \
              > $out/classify_cs_rmw.stdout 2>&1; echo "rc=$?" >> $out/classify_cs_rmw.stdout )
          log "$row classify_cs_rmw: $(tail -1 $out/classify_cs_rmw.stdout)"
        else
          log "$row: no $TS/rmw_stems.tsv yet; UV3 not credited this pass"
        fi
      fi
    ) & done; wait
    mkdir -p $F/report/$R2; ts=$(date -u +%Y%m%dT%H%M%SZ)
    T2D=$(dir $R2); [ -d $F/${R2}_${MODEL}_merged ] && T2D=$F/${R2}_${MODEL}_merged
    ( cd $C && python3 STAGE3_gem5/timing/firstdet_report.py --invisispec $(dir $R1) --cleanupspec $T2D \
        --speclfb $(dir $R3) --testset $TS ${GEN:+--gen-cpu-per-test $GEN} ${REPORT_ARGS:-} --json $F/report/$R2/report_$ts.json \
        --md $F/report/$R2/report_$ts.md > $F/report/$R2/report_$ts.stdout 2>&1; echo "rc=$?" >> $F/report/$R2/report_$ts.stdout )
    cp -f $F/report/$R2/report_$ts.md $F/report/$R2/latest.md 2>/dev/null; cp -f $F/report/$R2/report_$ts.json $F/report/$R2/latest.json 2>/dev/null
    ( cd $C && python3 STAGE3_gem5/timing/firstdet_report.py --invisispec $(dir $R1) --cleanupspec $T2D \
        --speclfb $(dir $R3) --testset $TS --rows all ${GEN:+--gen-cpu-per-test $GEN} --json $F/report/$R2/all_$ts.json \
        --md $F/report/$R2/all_$ts.md > /dev/null 2>&1; cp -f $F/report/$R2/all_$ts.md $F/report/$R2/all_latest.md; cp -f $F/report/$R2/all_$ts.json $F/report/$R2/all_latest.json )
    log "classify pass end; report $F/report/$R2/report_$ts.md ($(tail -1 $F/report/$R2/report_$ts.stdout))"
    [ "$1" = classify-once ] && break
    [ -e $F/STOP_CLASSIFY ] && { log "STOP_CLASSIFY found"; break; }
    sleep $CLS_EVERY
  done ;;
stop)    # graceful (in-flight tests finish); ONLY="T1rt T3rt" to stop a subset
  for rd in $ROWS; do case " ${ONLY:-$R1 $R2 $R3} " in *" ${rd%%:*} "*) touch $(dir ${rd%%:*})/STOP ;; esac; done
  log "STOP files written (${ONLY:-all})" ;;
esac
