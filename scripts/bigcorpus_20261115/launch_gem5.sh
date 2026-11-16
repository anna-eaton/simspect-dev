#!/usr/bin/env bash
# BIGCORPUS COPY (agent bigcorpus 2026-11-15) of scripts/overnight_20261111/launch_gem5.sh: OUT /tests/bigcorpus_20261115, campaigns
# runconfigs/bigcorpus_20261115/campaigns.json (rows E2 E3 E4 + race_stt*/race_sttmaster* on cafe3; E6 + race_sptfence* on cafe2), tmux bc_gem5,
# node body scripts/bigcorpus_20261115/gem5_row.sh (race env + race_scan). Rows with only recipe A run A only. L1D preflight only for E2/E3.
# Run: scripts/bigcorpus_20261115/launch_gem5.sh <node> [row ...]
# launch_gem5.sh -- X3 of the overnight plan: gem5 campaigns on the X2b corpora, recipe A first, then recipe B, per row.
# Run FROM THE MAC. Usage: scripts/overnight_20261111/launch_gem5.sh <node> [row ...]   (rows E3 E2 E11 on cafe3, E6 on cafe1;
# default = every row of runconfigs/bigcorpus_20261115/campaigns.json whose node is <node>).
# Preflight on the node (logged; refuses the row on failure): the gem5 binary exists; for full-cache setup the se.py default
#   --l1d_size of E2/E3/E11's tree equals the config's gem5.cache_setup_fill_bytes (64kB) (grep configs/common/Options.py).
# Each row = tmux session bc_gem5, window <row>: scripts/bigcorpus_20261115/gem5_row.sh (copied to the node) runs
#   `testrun.py --once --resume` passes on A until nothing is pending and <OUT>/testsets/<A model>/READY exists, then the same for B.
#   TMPDIR=/tmp (H-STK). testrun.py writes <OUT>/code/results/<results_name>__<ts>/ (it ignores paths.results_dir).
#   Logs: <OUT>/logs/gem5_<row>.out, launcher ~/Library/Logs/simspect/bigcorpus_gem5_<node>.log.
# Resume: rerun the launcher after the window is gone; passes always --resume the __latest campaign (verify-x1 2026-11-12).
set -euo pipefail
NODE=${1:?node}; shift || true
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=${OUT:-/tests/bigcorpus_20261115}
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/bigcorpus_gem5_${NODE}.log
log(){ echo "$(date -u '+%F %T') [$NODE] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
cd "$REPO"   # verify-x1 2026-11-12: before the python below, which opens runconfigs/... relative to cwd (was after it)
rows=$(python3 - "$NODE" "$@" <<'PY'
import json, sys
node, want = sys.argv[1], set(sys.argv[2:])
c = json.load(open("runconfigs/bigcorpus_20261115/campaigns.json"))
for r in sorted({x["row"] for x in c if x["node"] == node and (not want or x["row"] in want)}):
    print(r, " ".join(f'{x["config"]} {x["model"]}' for x in sorted((x for x in c if x["row"] == r), key=lambda x: x["recipe"])))
PY
)
cd "$REPO"
log "START rows: $(echo "$rows" | awk '{print $1}' | tr '\n' ' ')"
rx "tmux has-session -t bc_gem5 2>/dev/null || tmux new-session -d -s bc_gem5 -n ctl"
# verify-x1 2026-11-12: rows come in on fd 3; on stdin, the first ssh (rx) in the body swallowed the remaining rows,
# so only the first row (E11, binary missing on cafe3 -> SKIP) was ever processed.
while read -r ROW CA MA REST <&3; do
  [ -n "$ROW" ] || continue
  BIN=$(python3 -c "import json,re,sys;print(json.loads(re.sub(r'//[^\n]*','',open('$CA').read()))['gem5']['binary'])")
  rx "test -x $BIN" || { log "SKIP $ROW: $BIN missing on $NODE"; continue; }
  case "$ROW" in E2|E3)
    # verify-x1 2026-11-12: match both optparse (type="string", stt-master) and argparse (type=str, gem5-recon-modded) lines;
    # the old pattern only matched optparse, so E2 (recon-modded) was always SKIPPED with d=''.
    T=${BIN%/build/*}; d=$(rx "grep -oE 'l1d_size\"[^)]*default=\"[0-9a-zA-Z]*\"' $T/configs/common/Options.py | head -1 | grep -o 'default=\"[^\"]*' | cut -d'\"' -f2" || true)
    log "$ROW se.py default l1d_size on node: '$d' (config fill 64kB)"
    [ "$d" = 64kB ] || { log "SKIP $ROW: default L1D '$d' != 64kB; fix gem5.cache_setup_fill_bytes in $CA"; continue; };;
  esac
  if rx "tmux list-windows -t bc_gem5 -F '#W' | grep -qx $ROW"; then log "skip $ROW (window exists)"; continue; fi
  # verify-x1 2026-11-12: the old window ran `testrun.py` (loop mode) for A then B, but testrun only exits once every mode has
  # >= alloy.max_instances (93,041) .s files and the corpora stop at target_distinct 60,000, so B never started. gem5_row.sh runs
  # `testrun.py --once --resume` passes until nothing is pending and the corpus READY exists, then B (always resumes __latest,
  # so RESUME is no longer needed; a relaunch continues the same campaign). Old command: launch_gem5.sh.orig.
  rx "mkdir -p $O/code/scripts/bigcorpus_20261115 $O/logs && cat > $O/code/scripts/bigcorpus_20261115/gem5_row.sh" < "$REPO/scripts/bigcorpus_20261115/gem5_row.sh"
  rx "tmux new-window -d -t bc_gem5 -n $ROW 'nice -n 15 bash $O/code/scripts/bigcorpus_20261115/gem5_row.sh $O $ROW $CA $MA $REST'"
  log "LAUNCHED $ROW: $MA $REST"
done 3<<< "$rows"
log "END"
