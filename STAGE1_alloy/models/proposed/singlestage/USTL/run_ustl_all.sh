#!/usr/bin/env bash
# run_ustl_all.sh — USTL real runs on cafe2 (agent singlestage-ustl, 2026-11-09). UNAPPROVED DRAFT TOOLING.
# Runs V0..V3 for STT_6_u_stl then Recon_6_u_stl, two models at a time (2 x 4 seeds = 8 JVMs max),
# waiting while the node load average is > 56. Every step is logged to logs/USTL__driver.log.
# Launch (inside gem5_dev): docker exec -d gem5_dev bash -lc 'cd /tests/singlestage_20261109 && nohup bash models/USTL/run_ustl_all.sh > logs/USTL__driver.nohup.txt 2>&1'
cd /tests/singlestage_20261109 || exit 1
LOG=logs/USTL__driver.log
say() { echo "$(date -Is) $*" | tee -a "$LOG"; }
waitload() { while :; do l=$(cut -d' ' -f1 /proc/loadavg); awk -v l="$l" 'BEGIN{exit !(l>56)}' || break; say "load $l > 56, waiting"; sleep 60; done; }
run() {  # $1 = model path, $2 = out stem
  python3 tools/run_flat.py --model "$1" --out "out/USTL/$2" --alloy-dir /tests/simspect_alloy_20261108/STAGE1_alloy \
    --classes /tests/singlestage_20261109/classes --seeds default,1,2,3 --cap 10000 --timeout 1500 --jobs 4 \
    > "logs/USTL__$2.nohup.txt" 2>&1
  say "finished $2 rc=$? :: $(tail -n 1 out/USTL/$2/run_flat.log)"
}
say "START driver pid=$$"
for B in STT_6_u_stl Recon_6_u_stl; do
  waitload; say "pair 1 for $B: V0 base + V1"
  run models/USTL/base/$B.als $B & run models/USTL/${B}_flat_n8_prod.als ${B}_flat_n8_prod & wait
  waitload; say "pair 2 for $B: V2 + V3"
  run models/USTL/${B}_flat_n8_prod_nospacer.als ${B}_flat_n8_prod_nospacer & run models/USTL/${B}_flat_n8_leakrs_nospacer.als ${B}_flat_n8_leakrs_nospacer & wait
done
say "END driver"
