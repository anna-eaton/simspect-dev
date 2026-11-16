#!/usr/bin/env bash
# rg_extract.sh (agent inttwin 2026-11-16; Anna RG-1 = (b)) -- node side of the offline resolved-branch-gate re-score: for each given
# campaign (results_name), stream STAGE3_gem5/triage/rescore_resolved_gate.py `extract --layout sweep` over every shard campaign dir
# (results/<rn>_sh*__latest, ann from the campaign's corpus) into /tests/inttwin_20261116/rg/<rn>.jsonl.gz. Read-only on the records.
# The Mac then runs `rescore_resolved_gate.py score` (with resolved_gate.py) per campaign; see pair_table.py --rg.
# Run inside gem5_dev from /tests/inttwin_20261116/code:  bash scripts/inttwin_20261116/rg_extract.sh <results_name> [...]   Log: logs/rg_extract.log
O=/tests/inttwin_20261116; cd $O/code; mkdir -p $O/rg; L=$O/logs/rg_extract.log
for RN in "$@"; do
  M=$(python3 -c "import json;print([c['model'] for c in json.load(open('runconfigs/inttwin_20261116/campaigns.json')) if c['results_name']=='$RN'][0])")
  out=$O/rg/$RN.jsonl.gz; : > $out.tmp
  for d in results/${RN}_sh*__latest; do
    python3 - extract --layout sweep --raw $(readlink -f $d) --ann-root $O/testsets/$M --campaign $RN < $O/rg/rescore_resolved_gate.py | gzip >> $out.tmp
  done
  mv $out.tmp $out; echo "[$(date -u '+%F %T')] $RN model $M -> $out ($(zcat $out | wc -l) lines)" >> $L
done
