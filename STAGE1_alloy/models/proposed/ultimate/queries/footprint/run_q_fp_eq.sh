#!/bin/bash
# run_q_fp_eq.sh <q.als> <timeout_s> <parallel> -- split every check/run of <q.als> into its own file (split/), run each with
# a6RunAll (one JVM each, <parallel> at once, gtimeout), append one line per command to runs.log here. check UNSAT = holds.
Q=$1; TO=${2:-3600}; P=${3:-4}; D=$(cd "$(dirname "$0")" && pwd); A=$(cd "$D/../../../../.." && pwd)   # STAGE1_alloy
export TO D A JAVA=/opt/homebrew/opt/openjdk@17/bin/java; mkdir -p "$D/split" "$D/out"
stem=$(basename "$Q" .als); base=$(grep -v -E '^(check|run) ' "$Q")
grep -E '^(check|run) ' "$Q" | while read -r line; do l=$(echo "$line" | awk '{print $2}'); { echo "$base"; echo "$line"; } > "$D/split/${stem}__$l.als"; done
echo "$(date -u +%FT%TZ) BEGIN $Q timeout=$TO parallel=$P sha256=$(shasum -a 256 "$Q" | cut -c1-64)" >> "$D/runs.log"
one() { f=$1; n=$(basename "$f" .als); s=$(date +%s)
  gtimeout -k 10 "$TO" "$JAVA" -Xmx6g -cp "$A/alloy6.jar:$D/.." a6RunAll "$f" "$D/out/$n" > "$D/out/$n.log" 2>&1; rc=$?
  echo "$(date -u +%FT%TZ) $n rc=$rc secs=$(( $(date +%s)-s )) $(grep '^CMD' "$D/out/$n.log" | tr '\n' ' ')" >> "$D/runs.log"; }
export -f one
ls "$D/split/${stem}__"*.als | xargs -P "$P" -n 1 bash -c 'one "$0"'
echo "$(date -u +%FT%TZ) END $Q" >> "$D/runs.log"
