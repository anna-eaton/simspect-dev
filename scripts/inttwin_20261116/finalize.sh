#!/usr/bin/env bash
# finalize.sh (agent inttwin2 2026-11-16) -- after watch_done.sh reports every node finished: (1) on each node, the resolved-gate extract
# (rg_extract.sh, read-only on the records) for every results_name of that node not yet extracted; (2) copy cls/<row>/ (without the
# par_* evidence work dirs), cls/uv6_confirm_*/ (without stage/) and rg/*.jsonl.gz to experiments/2026-11-16_inttwin/{cls,rg}/;
# (3) on the Mac, rescore_resolved_gate.py score per results_name (labels = the row's per_stem_ot_<v>.json if present, else
# per_stem_<v>.json; --race for race rows) -> rgs/<rn>.score.json + <rn>.removed.jsonl; (4) pair_table.py gate off and gate on.
# Usage (repo root): bash scripts/inttwin_20261116/finalize.sh [extract|collect|score|table|all]   Log: experiments/2026-11-16_inttwin/finalize.log
cd "$(dirname "$0")/../.."; E=experiments/2026-11-16_inttwin; mkdir -p $E/cls $E/rg $E/rgs; L=$E/finalize.log
log(){ echo "$(date -u '+%F %T')Z $*" >> $L; }; STEP=${1:-all}; C=runconfigs/inttwin_20261116/campaigns.json
nodes(){ python3 -c "import json;print(' '.join(sorted({c['node'] for c in json.load(open('$C'))})))"; }
rns(){ python3 -c "import json;print(' '.join(c['results_name'] for c in json.load(open('$C')) if c['node'] in '$1'.split()))"; }
phys(){ [ $1 = cafe3ra ] && echo cafe3 || echo $1; }
if [ $STEP = extract -o $STEP = all ]; then
  for q in $(nodes); do n=$(phys $q); todo=""
    for rn in $(rns $q); do ssh $n "docker exec gem5_dev test -s /tests/inttwin_20261116/rg/$rn.jsonl.gz" || todo="$todo $rn"; done
    [ -z "$todo" ] && continue; log "extract $n:$todo"
    ssh $n "docker exec gem5_dev bash -lc 'cd /tests/inttwin_20261116/code && nice -n 5 bash scripts/inttwin_20261116/rg_extract.sh $todo'" >> $L 2>&1; log "extract $n rc=$?"
  done
fi
if [ $STEP = collect -o $STEP = all ]; then
  for n in cafe1 cafe2 cafe3; do
    mkdir -p $E/node_$n; ssh $n "docker exec gem5_dev bash -lc 'cd /tests/inttwin_20261116 && tar czf - --exclude=par_fpr --exclude=par_int --exclude=stage cls rg/*.jsonl.gz logs/*.log logs/*.last 2>/dev/null'" | tar xzf - -C $E/node_$n 2>>$L
    log "collect $n rc=$?"; cp -R $E/node_$n/cls/. $E/cls/; cp $E/node_$n/rg/*.jsonl.gz $E/rg/ 2>/dev/null
  done
fi
if [ $STEP = score -o $STEP = all ]; then
  python3 - $C > $E/score_jobs.txt <<'PY'
import json, sys
for c in json.load(open(sys.argv[1])):
    print(c["row"], c["version"], c["results_name"], "race" if c["row"].startswith("race_") else "eval")
PY
  while read row v rn kind; do
    lab=$E/cls/$row/per_stem_ot_$v.json; [ -f $lab ] || lab=$E/cls/$row/per_stem_$v.json
    [ -f $E/rg/$rn.jsonl.gz ] || { log "SKIP score $rn: no extract"; continue; }
    extra=""; [ $kind = race ] && extra="--race"; [ -f $lab ] && extra="$extra --labels $lab"
    python3 STAGE3_gem5/triage/rescore_resolved_gate.py score $E/rg/$rn.jsonl.gz $extra --json $E/rgs/$rn.score.json --removed $E/rgs/$rn.removed.jsonl > $E/rgs/$rn.stdout 2>&1
    log "score $rn rc=$? labels=$lab"
  done < $E/score_jobs.txt
fi
if [ $STEP = table -o $STEP = all ]; then
  python3 scripts/inttwin_20261116/pair_table.py $E/cls --md $E/pair_table_gateoff.md --json $E/pair_table_gateoff.json > /dev/null 2>>$L; log "table gate off rc=$?"
  python3 scripts/inttwin_20261116/pair_table.py $E/cls --rg $E/rgs --md $E/pair_table_gateon.md --json $E/pair_table_gateon.json > /dev/null 2>>$L; log "table gate on rc=$?"
fi
log "END finalize $STEP"
