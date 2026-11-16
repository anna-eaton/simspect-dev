#!/usr/bin/env bash
# uv5_rounds.sh -- repeated random re-concretization rounds of the main Footprint programs for A-UV5 (agent bigcorpus, 2026-11-16).
# Anna 2026-11-16: "just keep concretizing randomly until we get it". Pre-registered stopping rule (EVAL_MANIFEST): keep launching rounds
# until the cumulative UV5 count over the pool (main 50,232 + extra-new 90,932 + every round) reaches K >= 4, or Anna says stop.
# The rule is applied by whoever reads the round summaries; this loop stops when <O>/uv5_rounds/STOP exists (checked between rounds).
#
# A round = all 25,116 Stage-1b XMLs of the main corpus (read-only source) linked under new stem names inst-NNNNNN_c<r>.xml (every
# concretization draw, cache setup and timing point is seeded from the stem, so a new name = an independent random concretization; no
# code change), Stage 2 with recipe A (runconfigs/bigcorpus_20261115/stage2_final_A.jsonc, unchanged) by nov10_stream.py, streamed into
# the CleanupSpec T2g row only (exact firstdet protocol: parity config, random_all, 3x3 timing grid, TMPDIR=/tmp, all kinds) by
# footprint_launch.sh, then classify_hits.py + classify_cs_rmw.py and a one-line summary.
# Usage (inside gem5_dev, from <O>/code): bash scripts/bigcorpus_20261115/uv5_rounds.sh <first round> <step> [P]
#   e.g. cafe1: uv5_rounds.sh 1 2 54  (rounds 1,3,5,...);  cafe2: uv5_rounds.sh 2 2 54  (rounds 2,4,6,...)
# Logs: <O>/uv5_rounds/rounds_<host>.log (every step + rc), per round <O>/uv5_rounds/c<r>/summary.json; disk guard: no new round below 40 GB.
set -u
O=/tests/bigcorpus_20261115; U=$O/uv5_rounds; SRC=/tests/simspect_alloy_20261108/testsets_twostage/Footprint_6_u_core_lpP_fv3/xml
R=${1:?first round}; STEP=${2:?step}; P=${3:-54}; H=$(hostname)
# 2026-11-16 fast path (Anna): CODE=<snapshot> (default <O>/code), FAST=1 adds "fast_path": true to the round's gem5 block,
# STOPFILE (default <U>/STOP), WAIT_PID: wait until that pid (the previous loop on this node) has exited before the first round.
CODE=${CODE:-$O/code}; FAST=${FAST:-0}; STOPFILE=${STOPFILE:-$U/STOP}
mkdir -p $U; L=$U/rounds_$H.log; cd $CODE || exit 1
export CODE
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900
log(){ echo "[$(date -u '+%F %T')] [$H] $*" >> $L; }
log "START loop first=$R step=$STEP P=$P code=$CODE fast_path=$FAST stopfile=$STOPFILE"
if [ -n "${WAIT_PID:-}" ]; then log "waiting for pid $WAIT_PID (previous loop)"; while [ -d /proc/$WAIT_PID ]; do sleep 60; done; log "pid $WAIT_PID gone"; fi
while :; do
  [ -f $STOPFILE ] && { log "STOP file $STOPFILE present; loop ends before round $R"; break; }
  free=$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); [ "$free" -lt 40 ] && { log "disk ${free}G < 40G; loop ends before round $R"; break; }
  C=c$R; MODEL=Footprint_6_u_nov10_${C}_s2A; RD=$U/$C; mkdir -p $RD/src
  log "ROUND $R begin: corpus $MODEL, disk ${free}G"
  if [ ! -f $RD/src/LINKED ]; then
    for f in $SRC/inst-*.xml; do b=$(basename $f .xml); ln -sf $f $RD/src/${b}_$C.xml; [ -f $SRC/$b.txt ] && ln -sf $SRC/$b.txt $RD/src/${b}_$C.txt; done
    echo "$(ls $RD/src/*.xml | wc -l) xml linked $(date -u)" > $RD/src/LINKED
  fi
  log "ROUND $R: $(cat $RD/src/LINKED)"
  # Stage 2 (background) and the T2g consumer (streams as tests land)
  python3 -u scripts/bigcorpus_20261115/nov10_stream.py --src $RD/src --cfg runconfigs/bigcorpus_20261115/stage2_final_A.jsonc --ts $O/testsets \
      --final $MODEL --ws $RD/ws --jobs 24 --chunk 2000 >> $RD/stage2.out 2>&1 &
  S2=$!
  # config for this round: the T2g parity config with ONLY results_name changed (written next to the round)
  sed "s#\"results_name\": *\"[^\"]*\"#\"results_name\": \"bc_T2g_$MODEL\"#" runconfigs/bigcorpus_20261115/T2g_Footprint_6_u_nov10_s2A.jsonc > runconfigs/bigcorpus_20261115/T2g_$MODEL.jsonc
  if [ "$FAST" = 1 ]; then python3 - runconfigs/bigcorpus_20261115/T2g_$MODEL.jsonc <<'PY'
import re, sys
p = sys.argv[1]; t = open(p).read()
t = re.sub(r'("cache_setup":\s*"random_all",)', r'\1\n    "fast_path": true,', t, count=1)
t = "// uv5_rounds.sh FAST=1: + gem5.fast_path true (harness-only speed-up, wiki/state/COMMANDS.md 'Fast path (opt-in, 2026-11-16)')\n" + t
open(p, "w").write(t)
PY
  fi
  log "ROUND $R: config runconfigs/bigcorpus_20261115/T2g_$MODEL.jsonc fast_path=$(grep -c '"fast_path": true' runconfigs/bigcorpus_20261115/T2g_$MODEL.jsonc)"
  MODEL=$MODEL ONLY=T2g P_T2g=$P bash scripts/bigcorpus_20261115/footprint_launch.sh start
  OUT=$O/firstdet/T2g_$MODEL
  sleep 60
  # zombie-aware wait (2026-11-16 fix): the stream's subshell is a child of this loop and stays a zombie (/proc/<pid> exists) after it
  # exits, which hung rounds 1-3 here; a pid counts as running only while its state is not Z. Also stop on the driver's STREAM END line.
  alive(){ local s; s=$(ps -o stat= -p "$1" 2>/dev/null); [ -n "$s" ] && [ "${s#Z}" = "$s" ]; }
  while alive "$(cat $OUT/stream.pid 2>/dev/null || echo 0)" && ! grep -q "STREAM END" $OUT/driver.log 2>/dev/null; do sleep 120; done
  wait 2>/dev/null
  wait $S2; log "ROUND $R: stage2 rc=$? $(tail -1 $RD/ws/nov10_stream.log | cut -c1-160)"
  log "ROUND $R: gem5 $(grep 'STREAM END' $OUT/driver.log | tail -1 | cut -c1-160)"
  TS=$O/testsets/$MODEL
  python3 STAGE3_gem5/timing/classify_hits.py $OUT --defense cleanupspec --stage3 $O/code/STAGE3_gem5 --testset $TS --jobs 16 > $OUT/classify.stdout 2>&1; c1=$?
  python3 STAGE3_gem5/timing/classify_cs_rmw.py $OUT --rmw-stems $TS/rmw_stems.tsv --testset $TS > $OUT/classify_cs_rmw.stdout 2>&1; c2=$?
  FASTFLAG=$FAST python3 - $OUT $RD/summary.json $R <<'PY'
import json, sys, collections
out, dst, r = sys.argv[1], sys.argv[2], int(sys.argv[3])
rows = [json.loads(l) for l in open(out + "/results.jsonl")]
sig = collections.Counter(); uv5 = []
try:
    for l in open(out + "/classes.jsonl"):
        c = json.loads(l)
        for s in c.get("sigs", []):
            sig[s] += 1
        if "UV5" in c.get("sigs", []):
            uv5.append(f"{c['mode']}/{c['stem']}")
except FileNotFoundError:
    pass
s = dict(round=r, code=__import__("os").getcwd(), fast_path_config=__import__("os").environ.get("FASTFLAG") == "1",
         exec_path=dict(collections.Counter(x.get("exec_path", "production") for x in rows)), N=len(rows), status=dict(collections.Counter(x.get("status") for x in rows)), hits=sum(bool(x.get("hit")) for x in rows),
         UV5=len(uv5), UV5_stems=uv5, sigs=dict(sig))
json.dump(s, open(dst, "w"), indent=1); print(json.dumps(s))
PY
  log "ROUND $R DONE classify rc=$c1/$c2 summary $(cat $RD/summary.json | tr -d '\n' | cut -c1-300)"
  R=$((R + STEP))
done
log "END loop"
