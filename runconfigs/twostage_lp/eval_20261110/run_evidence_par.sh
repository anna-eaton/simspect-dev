#!/usr/bin/env bash
# run_evidence_par.sh <row> <corpus> <keys file> <evidence json> [jobs per run] -- as run_evidence.sh, but one
# rerun_hits_evidence.py process per campaign run (main + every shard) IN PARALLEL, each into its own JSON
# (<evidence dir>/par/<run>.json, TMPDIR /tmp/ev<k>), then merged into <evidence json> (existing keys kept).
# Keys already in <evidence json> are skipped. Run from the eval code root. (regen-lp, 2026-11-10)
set -u
ROW=$1; CORPUS=$2; KEYS=$3; OUT=$4; J=${5:-3}; P=$(dirname $OUT)/par; mkdir -p $P
python3 - "$KEYS" "$OUT" <<'PY'
import json, sys
ev = set(json.load(open(sys.argv[2])))
k = [l.strip() for l in open(sys.argv[1]) if l.strip() and l.strip() not in ev]
open(sys.argv[1] + ".todo", "w").write("\n".join(k) + "\n"); print("todo keys", len(k))
PY
i=0
for d in results/${ROW}__latest results/${ROW}_sh*__latest; do
  [ -e "$d" ] || continue; C=$(readlink -f $d); n=$(basename $d); i=$((i+1)); W=/tmp/ev$i; mkdir -p $W
  ( timeout 10800 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src /tests/simspect_alloy_20261108/testsets_twostage/$CORPUS \
      --code . --work $W --analyzer recon_stlf --out $P/$n.json --kinds ld --keys-file $KEYS.todo --batch 64 --jobs $J --extra-debug Commit > $P/$n.log 2>&1
    cp $W/logs/*.log $P/ 2>/dev/null; rm -rf $W ) &
done
wait
python3 - "$OUT" "$P" <<'PY'
import json, sys, glob
out = json.load(open(sys.argv[1])); n0 = len(out)
for f in glob.glob(sys.argv[2] + "/*.json"):
    for k, v in json.load(open(f)).items():
        out.setdefault(k, v)
json.dump(out, open(sys.argv[1], "w"), indent=1); print("evidence keys", n0, "->", len(out))
PY
