#!/usr/bin/env bash
# launch_eval.sh -- regen-lp (2026-11-10): start one testrun.py per campaign in campaigns.json (E2/E3/E4/E6 on the
# core-pinned v3 STT_6_u / Recon_6_u corpora, 2% sample), each in its own window of tmux session regenlp_eval. Run from
# the code root inside gem5_dev, TMPDIR=/tmp (H-STK). Usage: launch_eval.sh [campaign names...] (default all).
# Skips a campaign whose window exists. Logs:
# <results_dir>/../logs/eval_<name>.log (testrun stdout+stderr), launcher events in <results_dir>/../logs/launch_eval.log;
# testrun.py writes <results_dir>/<name>__<ts>/ (manifest, per-mode/kind window-results.json).
set -u
C=$(pwd); R=/tests/simspect_alloy_20261108/loosepin_regen; L=$R/logs; mkdir -p $L $R/eval_results
log(){ echo "$(date -u '+%F %T') $*" >> $L/launch_eval.log; }
tmux has-session -t regenlp_eval 2>/dev/null || tmux new-session -d -s regenlp_eval -n ctl
have=$(tmux list-windows -t regenlp_eval -F '#W')
python3 - <<PY > /tmp/regenlp_camps.tsv
import json; [print(c["results_name"], c["config"], c["model"], sep="\t") for c in json.load(open("runconfigs/twostage_lp/eval_20261110/campaigns.json"))]
PY
while IFS=$'\t' read -r name cfg model; do
  if [ $# -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$name"; then continue; fi   # optional: only the named campaigns
  echo "$have" | grep -qx "$name" && { log "skip $name (window exists)"; continue; }
  tmux new-window -d -t regenlp_eval -n "$name" "cd $C && export TMPDIR=/tmp && python3 -u testrun.py --config $cfg --model $model --interval ${INTERVAL:-120} --max-new ${MAXNEW:-300} ${RESUME:+--resume} >> $L/eval_$name.log 2>&1; echo EXIT rc=\$? >> $L/eval_$name.log"
  log "LAUNCH $name $cfg model=$model"
done < /tmp/regenlp_camps.tsv
tmux list-windows -t regenlp_eval -F '#W'
