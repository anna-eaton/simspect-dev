#!/bin/bash
# census of the loosepin runs on cafe1; log $WS/logs/lp_census.log
WS=/tests/simspect_alloy_20261108/loosepin; mkdir -p $WS/census
echo "$(date -Is) START" >> $WS/logs/lp_census.log
for d in $WS/out/*/; do m=$(basename $d)
  dirs=$(for s in default 1 2 3; do [ -d $d/$s ] && echo $d/$s; done)
  [ -z "$dirs" ] && continue
  python3 $WS/lp/census_lp.py --jobs 16 --json $WS/census/$m.json $dirs > /dev/null 2>> $WS/logs/lp_census.err && echo "$(date -Is) ok $m" >> $WS/logs/lp_census.log || echo "$(date -Is) FAIL $m" >> $WS/logs/lp_census.log
done
echo "$(date -Is) END" >> $WS/logs/lp_census.log
