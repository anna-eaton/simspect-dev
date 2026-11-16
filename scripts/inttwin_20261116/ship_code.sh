#!/usr/bin/env bash
# ship_code.sh (agent inttwin 2026-11-16) -- run FROM THE MAC: copy today's code (Mac HEAD + working tree) to <node>:/tests/inttwin_20261116/code
# (same tar as scripts/sptrace_20261116/launch.sh) and write SNAPSHOT.txt with the sha256s of every file that decides a verdict.
# Refuses if any inttwin tmux window is running on the node (a refresh mid-run would mix code). Log: ~/Library/Logs/simspect/inttwin_ship.log
# Usage: scripts/inttwin_20261116/ship_code.sh cafe3 [cafe1 ...]
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=/tests/inttwin_20261116
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/inttwin_ship.log; log(){ echo "$(date -u '+%F %T') $*" | tee -a "$LOG"; }
cd "$REPO"
SUMS=$( { echo "snapshot $(date -u +%FT%TZ) Mac HEAD $(git rev-parse --short HEAD) + working tree"; shasum -a 256 pipeline.py testsetgen.py testrun.py \
  STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py STAGE1_alloy/models/proposed_twophase/stage2_sharded.py \
  STAGE3_gem5/check_ld.py STAGE3_gem5/check_br.py STAGE3_gem5/check_other.py STAGE3_gem5/check_st.py STAGE3_gem5/gem5_common.py STAGE3_gem5/bugs/*.py \
  STAGE3_gem5/triage/rerun_hits_evidence.py scripts/bigcorpus_20261115/race_scan.py runconfigs/inttwin_20261116/*.jsonc scripts/inttwin_20261116/*; } )
for N in "$@"; do
  rx(){ ssh -o BatchMode=yes -o ConnectTimeout=20 "$N" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
  if rx "tmux list-windows -t inttwin -F '#W' 2>/dev/null | grep -v '^ctl\$' | grep -q ."; then log "ABORT $N: tmux inttwin has running windows"; exit 1; fi
  rx "mkdir -p $O/code $O/logs $O/testsets $O/cfg"
  COPYFILE_DISABLE=1 tar --no-xattrs --exclude='*/__pycache__' --exclude='*/m5out' --exclude=./results --exclude=./experiments --exclude=./build --exclude=./paper_figures \
    --exclude=./testsets --exclude=./analysis --exclude=./.git --exclude='*.pdf' --exclude='*.png' -czf - . | rx "tar -xzf - -C $O/code"
  echo "$SUMS" | rx "cat >> $O/code/SNAPSHOT.txt"
  log "shipped code to $N:$O/code ($(echo "$SUMS" | head -1))"
done
