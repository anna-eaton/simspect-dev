#!/usr/bin/env bash
# gem5_row.sh -- node-side body of one launch_gem5.sh row (verify-x1, 2026-11-12). Runs INSIDE the gem5_dev container, from tmux.
# Usage: gem5_row.sh <OUT> <ROW> <cfgA> <modelA> [<cfgB> <modelB> ...]
# Why: testrun.py's own loop only exits when every mode has >= alloy.max_instances (93,041) .s files; the streamed corpora stop at
# Stage 1.5's target_distinct (60,000) or earlier, so `testrun.py` for recipe A never exited and recipe B never started.
# Here each recipe runs `testrun.py --once --resume` passes (one campaign, results/<results_name>__latest) until a pass finds
# nothing new AND <OUT>/testsets/<model>/READY exists (stream_fp writes READY after its last publish), then the next recipe.
# Log: <OUT>/logs/gem5_<ROW>.out (every pass appended live). A batch that fails every time is retried every pass (as testrun did).
O=${1:?OUT}; ROW=${2:?ROW}; shift 2
L=$O/logs/gem5_$ROW.out; LAST=$O/logs/.gem5_$ROW.last
cd "$O/code" || exit 1
export TMPDIR=/tmp
while [ $# -ge 2 ]; do
  C=$1; M=$2; shift 2
  echo "START $C $M $(date -u)" >> "$L"
  while :; do
    python3 -u testrun.py --config "$C" --model "$M" --max-new 2000 --once --resume 2>&1 | tee -a "$L" > "$LAST"
    rc=${PIPESTATUS[0]}
    [ "$rc" -eq 0 ] || echo "testrun pass rc=$rc $(date -u)" >> "$L"
    if grep -q ' new (of ' "$LAST"; then continue; fi        # this pass ran a batch: go again at once
    if [ -f "$O/testsets/$M/READY" ]; then break; fi         # corpus finished and nothing pending: recipe done
    sleep 300
  done
  echo "EXIT $C: $M READY and drained $(date -u)" >> "$L"
done
echo "ROW $ROW DONE $(date -u)" >> "$L"
