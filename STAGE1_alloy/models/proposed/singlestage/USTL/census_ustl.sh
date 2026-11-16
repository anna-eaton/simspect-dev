#!/usr/bin/env bash
# census_ustl.sh STEM [CORE_DIR] — census_flat.py + ustl_store_hist.py for one USTL run (agent singlestage-ustl,
# 2026-11-09). Read-only on the run outputs; writes census.json / store_hist.json into out/USTL/STEM; logs to
# logs/USTL__census.log. CORE_DIR only for the exactly-6 V0 runs.
cd /tests/singlestage_20261109 || exit 1
S=$1; C=$2; O=out/USTL/$S; LOG=logs/USTL__census.log
say() { echo "$(date -Is) $*" >> "$LOG"; }
dirs="$O/default $O/1 $O/2 $O/3"
say "START census $S cores=${C:-none}"
t=$(date +%s)
nice -n 10 python3 tools/census_flat.py --jobs 8 --json $O/census.json ${C:+--cores $C} $dirs > /dev/null 2>> "$LOG" || say "ERROR census $S rc=$?"
nice -n 10 python3 models/USTL/ustl_store_hist.py --tools tools --jobs 8 --json $O/store_hist.json $dirs > /dev/null 2>> "$LOG" || say "ERROR store_hist $S rc=$?"
say "END census $S secs=$(( $(date +%s) - t ))"
