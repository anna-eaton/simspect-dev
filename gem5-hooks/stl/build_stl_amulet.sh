#!/bin/bash
# Build the SimSpect-STL binary of one AMuLeT tree, in its COPY under
# /work/amulet/hooks_stl_work/<Build> (cafe2, inside gem5_dev). The in-place trees
# (/work/amulet/amulet-gem5-<Build>_AE-v1.1) are never touched.
# Usage: build_stl_amulet.sh <InvisiSpec|CleanupSpec|SpecLFB> [tag]     J=<jobs> (default 32)
#        N=1 build_stl_amulet.sh <Build>   # scons -n: list what would be rebuilt, build nothing
# Log (appended): /work/amulet/hooks_stl_work/build_<Build>_<tag>.log  (start/end time, command, all output, rc)
# Same scons / Python per tree as gem5-hooks/verify/build_simspect_hooks.sh.
# Doc: wiki/design/STL_SPECULATION.md "Port to the AMuLeT builds (2026-11-09)".
set -u
b=$1
tag=${2:-stl}
J=${J:-32}
W=${W:-/work/amulet/hooks_stl_work}
LOG=$W/build_${b}_${tag}.log
cd "$W/$b" || { echo "no tree $W/$b"; exit 1; }
case "$PWD" in /work/amulet/amulet-gem5-*) echo "refusing: in-place tree"; exit 1;; esac
NFLAG=""; [ "${N:-0}" = 1 ] && NFLAG="-n"
if [ "$b" = SpecLFB ]; then
  CMD="python3 /usr/bin/scons -j$J $NFLAG build/X86/gem5.opt --ignore-style"
  export SCONS_LIB_DIR=
else
  CMD="python2 /usr/local/bin/scons -j$J $NFLAG build/X86_MESI_Two_Level/gem5.opt"
  export SCONS_LIB_DIR=/usr/local/lib/python2.7/dist-packages/scons-2.5.1
fi
echo "[$(date -Iseconds)] START $b tag=$tag j=$J cwd=$PWD cmd: $CMD" >> "$LOG"
$CMD </dev/null >> "$LOG" 2>&1
rc=$?
echo "[$(date -Iseconds)] END $b tag=$tag rc=$rc" >> "$LOG"
exit $rc
