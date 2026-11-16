#!/bin/bash
# queue_stl.sh — unattended queue for the STL family runs + censuses on cafe2 (singlestage-stl agent, 2026-11-09).
# Runs inside gem5_dev from /tests/singlestage_20261109. At most 2 models (8 JVMs) at once; waits while load > 56.
# Log: logs/STL__queue.log (start/end, every step, every non-zero exit). Each run_flat call skips finished seeds.
# V0 census with cores gets 20 min; if it times out it is rerun on the default and 1 dirs only (brief rule).
cd /tests/singlestage_20261109 || exit 1
LOG=logs/STL__queue.log
L() { echo "$(date -Is) $*" >> $LOG; }
AD=/tests/simspect_alloy_20261108/STAGE1_alloy; CL=/tests/singlestage_20261109/classes
waitload() { while [ "$(awk '{print int($1)}' /proc/loadavg)" -gt 56 ]; do L "load $(cut -d' ' -f1 /proc/loadavg) > 56, waiting"; sleep 60; done; }
run() { # $1 model path (rel), $2 out stem
  waitload; L "RUN $2 ($1)"
  nice -n 5 python3 tools/run_flat.py --model $1 --out out/STL/$2 --alloy-dir $AD --classes $CL --seeds default,1,2,3 --cap 10000 --timeout 1500 --jobs 4 > logs/STL__$2.nohup.txt 2>&1
  rc=$?; L "RUN-END $2 rc=$rc $(tail -1 out/STL/$2/run_flat.log)"; }
census() { # $1 out stem, $2 optional cores dir
  d=out/STL/$1; dirs="$d/default $d/1 $d/2 $d/3"
  L "STORE-CENSUS $1"; nice -n 10 python3 models/STL/stl_store_census.py --jobs 8 --json $d/stl_store_census.json $dirs > /dev/null 2> $d/stl_store_census.err; L "STORE-CENSUS-END $1 rc=$?"
  if [ -n "$2" ]; then
    L "CENSUS $1 cores=$2 (all 4 dirs, 1200 s limit)"; t0=$(date +%s)
    timeout 1200 nice -n 10 python3 tools/census_flat.py --jobs 8 --json $d/census.json --cores $2 $dirs > /dev/null 2> $d/census.err; rc=$?
    L "CENSUS-END $1 rc=$rc secs=$(( $(date +%s) - t0 ))"
    if [ $rc -eq 124 ]; then
      L "CENSUS $1 timed out -> rerun with cores on default + 1 only, plus no-core census on all 4 dirs"
      nice -n 10 python3 tools/census_flat.py --jobs 8 --json $d/census_cores_default_1.json --cores $2 $d/default $d/1 > /dev/null 2> $d/census_cores.err; L "CENSUS-CORES-D1-END $1 rc=$?"
      nice -n 10 python3 tools/census_flat.py --jobs 8 --json $d/census.json $dirs > /dev/null 2> $d/census.err; L "CENSUS-NOCORE-END $1 rc=$?"
    fi
  else
    L "CENSUS $1"; nice -n 10 python3 tools/census_flat.py --jobs 8 --json $d/census.json $dirs > /dev/null 2> $d/census.err; L "CENSUS-END $1 rc=$?"
  fi; }
L "QUEUE START pid=$$"
SC=/tests/simspect_alloy_20261108/out/STT_6_stl_core; RC=/tests/simspect_alloy_20261108/out/Recon_6_stl_core
# STT_6_stl V0 + V1 were launched by hand at 01:28 UTC (same run_flat command as run()); wait for both to END
for s in STT_6_stl STT_6_stl_flat_n8_prod; do until tail -1 out/STL/$s/run_flat.log | grep -q ' END$'; do sleep 30; done; L "RUN-END $s (hand-launched) $(tail -2 out/STL/$s/run_flat.log | head -1)"; done
run models/STL/STT_6_stl_flat_n8_prod_nospacer.als STT_6_stl_flat_n8_prod_nospacer & run models/STL/STT_6_stl_flat_n8_leakrs_nospacer.als STT_6_stl_flat_n8_leakrs_nospacer &
census STT_6_stl $SC; census STT_6_stl_flat_n8_prod; wait
run models/STL/base/Recon_6_stl.als Recon_6_stl & run models/STL/Recon_6_stl_flat_n8_prod.als Recon_6_stl_flat_n8_prod &
census STT_6_stl_flat_n8_prod_nospacer; census STT_6_stl_flat_n8_leakrs_nospacer; wait
run models/STL/Recon_6_stl_flat_n8_prod_nospacer.als Recon_6_stl_flat_n8_prod_nospacer & run models/STL/Recon_6_stl_flat_n8_leakrs_nospacer.als Recon_6_stl_flat_n8_leakrs_nospacer &
census Recon_6_stl $RC; census Recon_6_stl_flat_n8_prod; wait
census Recon_6_stl_flat_n8_prod_nospacer; census Recon_6_stl_flat_n8_leakrs_nospacer
L "QUEUE END"
