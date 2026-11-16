#!/bin/bash
# Read-only environment capture inside gem5_dev (run via: ssh <node> "docker exec -i gem5_dev bash -s" < collect_env.sh)
echo "## host $(hostname) $(date -u '+%F %T UTC')"
lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Socket|MHz' ; free -g | head -2
echo "## gem5 binaries: md5 sha256 mtime size"
for b in /work/amulet/amulet-gem5-InvisiSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt /work/amulet/amulet-gem5-CleanupSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt \
         /work/amulet/amulet-gem5-SpecLFB_AE-v1.1/build/X86/gem5.opt /work/gem5-recon-modded/build/X86/gem5.opt /work/stt/build/X86/gem5.opt \
         /work/stt-master/build/X86/gem5.opt /work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt; do
  [ -f "$b" ] || { echo "MISSING $b"; continue; }
  echo "$b $(md5sum < $b | cut -d' ' -f1) $(sha256sum < $b | cut -d' ' -f1) $(stat -c '%y %s' $b)"
done
echo "## hook sources (md5) and META ver line"
for t in /work/amulet/amulet-gem5-InvisiSpec_AE-v1.1 /work/amulet/amulet-gem5-CleanupSpec_AE-v1.1 /work/amulet/amulet-gem5-SpecLFB_AE-v1.1 /work/gem5-recon-modded /work/stt /work/stt-master /work/gem5-spt; do
  for f in $(find $t/src -name 'simspect_hooks.cc' 2>/dev/null); do echo "$f $(md5sum < $f | cut -d' ' -f1) $(grep -o 'ver=[0-9]*' $f | head -1)"; done
  [ -d $t/.git ] && echo "$t git $(cd $t && git rev-parse HEAD 2>/dev/null)"
done
echo "## alloy jar"; sha256sum /tests/bigcorpus_20261115/code/STAGE1_alloy/alloy6.jar 2>/dev/null
echo "## java"; java -version 2>&1
echo "## python"; python3 --version
echo "## llvm/clang"; for x in clang clang-15 llc llc-15 llvm-objdump-15 gcc as; do command -v $x >/dev/null && echo "$x: $($x --version 2>&1 | head -1)"; done
echo "## amulet"; /opt/amulet-venv/bin/python --version; /opt/amulet-venv/bin/pip freeze 2>/dev/null
for r in /tests/timing_20261115/amulet/amulet-repo /work/amulet-repo; do [ -d $r ] && echo "$r $(cd $r && git rev-parse HEAD)"; done
md5sum /tests/timing_20261115/amulet/benchmark_t5.py 2>/dev/null
