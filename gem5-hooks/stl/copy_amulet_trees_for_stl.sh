#!/bin/bash
# stl-port (2026-11-09): copy the three AMuLeT trees for the STL hook port (run inside gem5_dev on cafe2;
# the copies are what apply_stl_hooks_amulet.py and build_stl_amulet.sh work on). Doc: wiki/design/STL_SPECULATION.md
# "Port to the AMuLeT builds (2026-11-09)".
# The in-place trees are only read. Backup binaries (build/*/gem5.opt.<suffix>) are skipped.
# Log: /work/amulet/hooks_stl_work/copy_trees.log
set -u
W=/work/amulet/hooks_stl_work
mkdir -p $W
LOG=$W/copy_trees.log
exec >> $LOG 2>&1
echo "[$(date -Iseconds)] START copy_trees (df before:)"; df -h /work | tail -1
for b in SpecLFB InvisiSpec CleanupSpec; do
  SRC=/work/amulet/amulet-gem5-${b}_AE-v1.1
  DST=$W/$b
  if [ -e $DST ]; then echo "[$(date -Iseconds)] $DST exists, skipping"; continue; fi
  mkdir -p $DST.partial
  echo "[$(date -Iseconds)] copy $SRC -> $DST"
  tar -C $SRC -cf - --exclude='./build/*/gem5.opt.*' . | tar -C $DST.partial -xpf -
  rc=$?
  if [ $rc -ne 0 ]; then echo "[$(date -Iseconds)] FAILED $b rc=$rc"; continue; fi
  mv $DST.partial $DST
  echo "[$(date -Iseconds)] done $b rc=$rc size=$(du -sh $DST | cut -f1)"
done
echo "[$(date -Iseconds)] END copy_trees (df after:)"; df -h /work | tail -1
