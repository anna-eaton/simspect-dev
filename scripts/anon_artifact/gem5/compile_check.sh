#!/bin/bash
# compile_check.sh -- full scons build of stripped anonymous-artifact gem5 trees in cafe2's gem5_dev container, in
# /tmp/anon_g5check/<build> (never inside /work). Copies only the node's build/variables files (build options) from
# /work read-only. Usage: compile_check.sh <build> [<build> ...]   (J=jobs per build, default 16)
# Log: ~/Library/Logs/simspect/anon_g5check_<build>.log (Mac) + /tmp/anon_g5check/<build>.log (container).
set -u
O=/Users/annaeaton/trippel/simspect-anon/gem5; J=${J:-16}; mkdir -p ~/Library/Logs/simspect
for b in "$@"; do
  L=~/Library/Logs/simspect/anon_g5check_$b.log
  echo "$(date -u +%FT%T) START $b j=$J" >> $L
  ssh -o BatchMode=yes cafe2 "docker exec gem5_dev bash -lc 'rm -rf /tmp/anon_g5check/$b && mkdir -p /tmp/anon_g5check/$b'"
  COPYFILE_DISABLE=1 tar -C $O/$b -cf - . | ssh -o BatchMode=yes cafe2 "docker exec -i gem5_dev tar -xf - -C /tmp/anon_g5check/$b"
  case $b in
    amulet-gem5-SpecLFB_AE-v1.1) CMD="mkdir -p build/X86/gem5.build && cp /work/amulet/$b/build/X86/gem5.build/variables build/X86/gem5.build/ 2>/dev/null; SCONS_LIB_DIR= python3 /usr/bin/scons -j$J build/X86/gem5.opt --ignore-style";;
    amulet-gem5-InvisiSpec_AE-v1.1|amulet-gem5-CleanupSpec_AE-v1.1) CMD="mkdir -p build/variables && cp /work/amulet/$b/build/variables/X86_MESI_Two_Level build/variables/ && SCONS_LIB_DIR=/usr/local/lib/python2.7/dist-packages/scons-2.5.1 python2 /usr/local/bin/scons -j$J build/X86_MESI_Two_Level/gem5.opt";;
    *) echo "no recipe for $b" >> $L; continue;;
  esac
  ssh -o BatchMode=yes cafe2 "docker exec gem5_dev bash -lc 'cd /tmp/anon_g5check/$b && nice -n 19 bash -c \"$CMD\" </dev/null > /tmp/anon_g5check/$b.log 2>&1; echo RC=\$? >> /tmp/anon_g5check/$b.log; tail -5 /tmp/anon_g5check/$b.log'" >> $L 2>&1
  echo "$(date -u +%FT%T) END $b" >> $L
done
