#!/bin/bash
# pin non-vacuity check (regen-lp 2026-11-10): core-pinned Footprint_6_u_lpPc models for cores c326 (A) and c113 (B).
cd "$(dirname "$0")"; A=../../../../../..; J=/opt/homebrew/opt/openjdk@17/bin/java
for q in q_*.als; do s=$(date +%s); gtimeout 1800 $J -Xmx6g -cp $A/alloy6.jar:../.. a6RunAll $q out_${q%.als} > ${q%.als}.log 2>&1; echo "$(date -u +%FT%TZ) $q rc=$? secs=$(( $(date +%s)-s )) $(grep ^CMD ${q%.als}.log)" >> runs.log; done
