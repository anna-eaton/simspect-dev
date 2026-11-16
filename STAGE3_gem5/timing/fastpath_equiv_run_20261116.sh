#!/bin/bash
# fastpath_equiv_run_20261116.sh (agent fastpath, 2026-11-16): the fast-path equivalence campaign as run on cafe3
# (container gem5_dev), all at nice 19 beside the running big-corpus work. Results: EVAL_MANIFEST "Per-test cost and
# setup amortization (2026-11-16)" -> "Fast path adopted (opt-in)". Runbook for reruns: wiki/state/COMMANDS.md
# "Fast path (opt-in, 2026-11-16)".
#
# Layout: B=/tests/fastpath_20261116 (fresh dir): code/ = copy of the Mac tree, configs/ = bigcorpus run configs
# copied verbatim (T1g/T2g/T3g InvisiSpec/CleanupSpec/SpecLFB footprint, E2w ReCon-STT, E3 STT), pairs/ = known-hit
# pair files from the bigcorpus classes.jsonl / E2w window-hits, eq_<name>/ = one equivalence check each.
# Testsets are read in place from /tests/bigcorpus_20261115/testsets (read-only). Nothing else is touched.
#
#   bash fastpath_equiv_run_20261116.sh [PAR=8] [SAMPLE=300]
set -u
PAR=${1:-8}; SAMPLE=${2:-300}
B=/tests/fastpath_20261116; C=$B/code; CF=$B/configs; P=$B/pairs
EQ="nice -n 19 python3 $C/STAGE3_gem5/timing/fastpath_equiv.py"
export TMPDIR=/tmp
mkdir -p $B/logs
exec > >(tee -a $B/logs/run_all.log) 2>&1
# NB: a bare `wait` would also wait for the tee process substitution above and hang forever; wait on explicit pids.
PIDS=()
w() { wait "${PIDS[@]}"; PIDS=(); }
echo "=== START $(date -u '+%F %T') PAR=$PAR SAMPLE=$SAMPLE uptime: $(uptime)"
cd $C

drv() {  # name config model pairs-file sample [extra env...]
  local name=$1 cfg=$2 model=$3 pf=$4 n=$5; shift 5
  echo "--- driver $name START $(date -u '+%T')"
  env "$@" $EQ driver --code-root $C --config $CF/$cfg --model $model --out $B/eq_$name \
      ${pf:+--pairs-file $pf} --sample $n --seed 20261116 --parallel $PAR > $B/logs/eq_$name.out 2>&1
  echo "--- driver $name rc=$? END $(date -u '+%T'): $(grep 'END driver' $B/logs/eq_$name.out | tail -1)"
}
bat() {  # name config model pairs-file sample
  echo "--- batch $1 START $(date -u '+%T')"
  $EQ batch --code-root $C --config $CF/$2 --model $3 --out $B/eqb_$1 ${4:+--pairs-file $4} --sample $5 \
      --seed 20261117 --jobs $PAR > $B/logs/eqb_$1.out 2>&1
  echo "--- batch $1 rc=$? END $(date -u '+%T'): $(grep 'END batch' $B/logs/eqb_$1.out | tail -1)"
}

# 1. footprint builds (check_footprint), known hits + seeded random sample; two checks at a time
drv T1g T1g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T1g.tsv $SAMPLE & PIDS+=($!)
drv T2g T2g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T2g.tsv $SAMPLE & PIDS+=($!)
w
drv T3g T3g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T3g.tsv $SAMPLE & PIDS+=($!)
# A-UV5: the one big-corpus UV5 test (extra corpus, not_taken inst-061878) + 20 random of that corpus
printf 'mispredict_not_taken\tinst-061878\tUV5\n' > $P/known_T2g_extra.tsv
drv T2gx T2g_Footprint_6_u_core_lpP_s2A.jsonc Footprint_6_u_core_lpP_s2A $P/known_T2g_extra.tsv 20 & PIDS+=($!)
w
# 2. STT-family builds (check_ld + check_br): ReCon-STT (gem5-recon-modded) and STT (stt-master)
drv E2w E2w_STT_6_u_core_lpP_s2A.jsonc STT_6_u_core_lpP_s2A $P/known_E2w.tsv $SAMPLE & PIDS+=($!)
drv E3 E3_STT_6_u_core_lpP_s2A.jsonc STT_6_u_core_lpP_s2A "" 200 & PIDS+=($!)
w
# 3. error cases: synthetic (as failure, no xmit.kind, no xmit PC, gem5 panic) and gem5 timeouts (timeout 0 s)
for R in T2g:T2g_Footprint_6_u_nov10_s2A.jsonc:Footprint_6_u_nov10_s2A E2w:E2w_STT_6_u_core_lpP_s2A.jsonc:STT_6_u_core_lpP_s2A; do
  IFS=: read name cfg model <<< "$R"
  $EQ errcases --code-root $C --config $CF/$cfg --model $model --out $B/err_$name --n 2 > $B/logs/err_$name.out 2>&1
  drv err_$name ../err_$name/config_errcases.jsonc ${model}_errcases $B/err_$name/pairs_errcases.tsv 0 & PIDS+=($!)
  head -7 $P/known_$name.tsv | tail -6 > $P/timeout_$name.tsv
  drv timeout_$name $cfg $model $P/timeout_$name.tsv 0 SIMSPECT_GEM5_TIMEOUT_S=0 & PIDS+=($!)
  w
done
# 4. A/A control (production twice): is a per-test record deterministic run to run?
EQAA="$EQ driver --code-root $C --config $CF/T2g_Footprint_6_u_nov10_s2A.jsonc --model Footprint_6_u_nov10_s2A"
$EQAA --out $B/eq_AA_T2g --pairs-file $P/known_T2g.tsv --sample 20 --seed 7 --parallel $PAR --ab prod,prod \
    > $B/logs/eq_AA_T2g.out 2>&1; echo "--- AA rc=$?: $(grep 'END driver' $B/logs/eq_AA_T2g.out | tail -1)"
# 5. batch path (pipeline.py gem5 / testrun.py: options 1+2 with checker threads)
bat T2g T2g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T2g.tsv 150 & PIDS+=($!)
bat E2w E2w_STT_6_u_core_lpP_s2A.jsonc STT_6_u_core_lpP_s2A $P/known_E2w.tsv 150 & PIDS+=($!)
w
bat T1g T1g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T1g.tsv 100 & PIDS+=($!)
bat T3g T3g_Footprint_6_u_nov10_s2A.jsonc Footprint_6_u_nov10_s2A $P/known_T3g.tsv 100 & PIDS+=($!)
w
echo "=== END $(date -u '+%F %T') uptime: $(uptime)"
