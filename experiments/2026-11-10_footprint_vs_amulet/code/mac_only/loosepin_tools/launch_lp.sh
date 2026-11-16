#!/usr/bin/env bash
# launch_lp.sh -- start the loose-pin draft enumerations on a cafe node (loosepin agent, 2026-11-09). UNAPPROVED DRAFTS.
# Runs inside gem5_dev. Workspace layout (copied in from the Mac repo):
#   $WS/alloy/{alloy6.jar,a6CountModels.class}  $WS/tools/{run_flat.py,check_bound_consistency.py,a6RandomModels.class}
#   $WS/models/<Model>_lp<V>.als                 $WS/lp/{make_loosepin.py,census_lp.py,launch_lp.sh}
# Each model: run_flat.py (log $WS/out/<model>/run_flat.log + runs.jsonl; refuses if the bound lint fails), seeds
# default,1,2,3, cap $CAP, timeout $TMO (SPT: $TMO_SPT). Master log: $WS/logs/launch_lp.log. Usage: launch_lp.sh [model ...]
set -u
WS=${WS:-/tests/simspect_alloy_20261108/loosepin}
CAP=${CAP:-10000}; TMO=${TMO:-1500}; TMO_SPT=${TMO_SPT:-3600}; SEEDS=${SEEDS:-default,1,2,3}
mkdir -p "$WS/logs" "$WS/out"
LOG="$WS/logs/launch_lp.log"
models=("$@"); [ ${#models[@]} -eq 0 ] && models=($(cd "$WS/models" && ls *.als | sed 's/\.als$//'))
echo "$(date -Is) START host=$(hostname) cap=$CAP tmo=$TMO tmo_spt=$TMO_SPT seeds=$SEEDS models=${models[*]}" >> "$LOG"
for m in "${models[@]}"; do
  t=$TMO; case "$m" in SPT*) t=$TMO_SPT;; esac
  nohup python3 -u "$WS/tools/run_flat.py" --model "$WS/models/$m.als" --out "$WS/out/$m" --alloy-dir "$WS/alloy" \
      --classes "$WS/tools" --seeds "$SEEDS" --cap "$CAP" --timeout "$t" --jobs 4 --min-disk-gb 60 \
      > "$WS/logs/run_flat_$m.out" 2>&1 &
  echo "$(date -Is) launched $m pid=$! timeout=$t" >> "$LOG"
done
