#!/usr/bin/env bash
# ship_code.sh (agent invisispec-fut 2026-11-16) -- run FROM THE MAC: copy today's code (Mac HEAD + working tree) to
# <node>:/tests/futuristic_20261116/code (same tar as scripts/inttwin_20261116/ship_code.sh) and append SNAPSHOT.txt with the
# sha256s of every file that decides a verdict (the four _fut models included).
# Refuses if any 'fut' tmux window other than ctl is running on the node (a refresh mid-run would mix code).
# Log: ~/Library/Logs/simspect/futuristic_ship.log.  Usage: scripts/futuristic_20261116/ship_code.sh cafe2 [cafe3 ...]
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=/tests/futuristic_20261116
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/futuristic_ship.log; log(){ echo "$(date -u '+%F %T') $*" | tee -a "$LOG"; }
cd "$REPO"
SUMS=$( { echo "snapshot $(date -u +%FT%TZ) Mac HEAD $(git rev-parse --short HEAD) + working tree"; shasum -a 256 pipeline.py testsetgen.py testrun.py twostage_lp.py \
  STAGE2_compilation/parsexml.py STAGE2_compilation/batch_generate.py STAGE2_compilation/compile_annotate.py STAGE1_alloy/models/proposed_twophase/stage2_sharded.py \
  STAGE1_alloy/models/*_fut.als STAGE1_alloy/models/Footprint_6_u_core_ri.als STAGE1_alloy/models/Footprint_6_u_lpP.als STAGE1_alloy/models/STT_6_u_core_ri.als STAGE1_alloy/models/STT_6_u_lpP.als \
  STAGE3_gem5/check_ld.py STAGE3_gem5/check_br.py STAGE3_gem5/check_other.py STAGE3_gem5/check_footprint.py STAGE3_gem5/gem5_common.py STAGE3_gem5/bugs/*.py \
  STAGE3_gem5/timing/firstdet_stream.py STAGE3_gem5/timing/timing_driver.py specs/leakage/invisispec.json runconfigs/futuristic_20261116/*.jsonc scripts/futuristic_20261116/* 2>/dev/null; } )
for N in "$@"; do
  rx(){ ssh -o BatchMode=yes -o ConnectTimeout=20 "$N" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
  if rx "tmux list-windows -t fut -F '#W' 2>/dev/null | grep -v '^ctl\$' | grep -q ."; then log "ABORT $N: tmux fut has running windows"; exit 1; fi
  rx "mkdir -p $O/code $O/logs $O/testsets $O/cfg"
  COPYFILE_DISABLE=1 tar --no-xattrs --exclude='*/__pycache__' --exclude='*/m5out' --exclude=./results --exclude=./experiments --exclude=./build --exclude=./paper_figures \
    --exclude=./testsets --exclude=./analysis --exclude=./.git --exclude='*.pdf' --exclude='*.png' -czf - . | rx "tar -xzf - -C $O/code"
  echo "$SUMS" | rx "cat >> $O/code/SNAPSHOT.txt"
  log "shipped code to $N:$O/code ($(echo "$SUMS" | head -1))"
done
