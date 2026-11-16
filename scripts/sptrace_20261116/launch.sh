#!/usr/bin/env bash
# launch.sh (agent sptrace 2026-11-16) -- run FROM THE MAC: ship a code snapshot to cafe2 /tests/sptrace_20261116/code, start tmux sptrace (node_run.sh).
# Log: ~/Library/Logs/simspect/sptrace_launch.log
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=/tests/sptrace_20261116; N=cafe2
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/sptrace_launch.log; log(){ echo "$(date -u '+%F %T') $*" | tee -a "$LOG"; }
rx(){ ssh -o BatchMode=yes $N "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
rx "tmux has-session -t sptrace 2>/dev/null" && { log "ABORT: tmux sptrace exists"; exit 1; }
rx "mkdir -p $O/code"
cd "$REPO"
COPYFILE_DISABLE=1 tar --no-xattrs --exclude='*/__pycache__' --exclude='*/m5out' --exclude=./results --exclude=./experiments --exclude=./build --exclude=./paper_figures \
  --exclude=./testsets --exclude=./analysis --exclude=./.git --exclude='*.pdf' --exclude='*.png' -czf - . | rx "tar -xzf - -C $O/code"
{ echo "snapshot $(date -u +%FT%TZ) Mac HEAD $(git rev-parse --short HEAD) + working tree"; shasum -a 256 pipeline.py testsetgen.py testrun.py STAGE2_compilation/parsexml.py \
  STAGE3_gem5/check_ld.py STAGE3_gem5/gem5_common.py scripts/bigcorpus_20261115/race_scan.py scripts/bigcorpus_20261115/gem5_row.sh STAGE1_alloy/models/SPT_6_oneLP_v2.als \
  runconfigs/sptrace_20261116/*; } | rx "cat > $O/code/SNAPSHOT.txt"
rx "tmux new-session -d -s sptrace -n ctl 'bash $O/code/scripts/sptrace_20261116/node_run.sh; bash'"
log "launched tmux sptrace on $N"
