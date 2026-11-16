#!/usr/bin/env bash
# uv5_round_post.sh <round> -- the tail of uv5_rounds.sh for one round, run by hand (agent bigcorpus 2026-11-16) after the loops hung on a
# zombie stream pid: classify_hits.py + classify_cs_rmw.py on firstdet/T2g_Footprint_6_u_nov10_c<r>_s2A and uv5_rounds/c<r>/summary.json.
# Run inside gem5_dev from the code root the round used (<O>/code for rounds 1-3). Log: <O>/uv5_rounds/c<r>/post.log
set -u
O=/tests/bigcorpus_20261115; R=${1:?round}; C=c$R; MODEL=Footprint_6_u_nov10_${C}_s2A; OUT=$O/firstdet/T2g_$MODEL; TS=$O/testsets/$MODEL; RD=$O/uv5_rounds/$C
export TMPDIR=/tmp; L=$RD/post.log; echo "[$(date -u '+%F %T')] post START round $R code $PWD" >> $L
python3 STAGE3_gem5/timing/classify_hits.py $OUT --defense cleanupspec --stage3 $PWD/STAGE3_gem5 --testset $TS --jobs 16 > $OUT/classify.stdout 2>&1; c1=$?
python3 STAGE3_gem5/timing/classify_cs_rmw.py $OUT --rmw-stems $TS/rmw_stems.tsv --testset $TS > $OUT/classify_cs_rmw.stdout 2>&1; c2=$?
python3 - $OUT $RD/summary.json $R "$PWD" <<'PY' >> $L
import json, sys, collections
out, dst, r, code = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
rows = [json.loads(l) for l in open(out + "/results.jsonl")]
sig = collections.Counter(); uv5 = []
for l in open(out + "/classes.jsonl"):
    c = json.loads(l)
    for s in c.get("sigs", []): sig[s] += 1
    if "UV5" in c.get("sigs", []): uv5.append(f"{c['mode']}/{c['stem']}")
s = dict(round=r, code=code, fast_path_config=False, exec_path=dict(collections.Counter(x.get("exec_path", "production") for x in rows)), N=len(rows),
         status=dict(collections.Counter(x.get("status") for x in rows)), hits=sum(bool(x.get("hit")) for x in rows),
         over_clean_rows=[f"{x['mode']}/{x['stem']}" for x in rows if "over_clean" in (x.get("terms_fired") or [])], UV5=len(uv5), UV5_stems=uv5, sigs=dict(sig))
json.dump(s, open(dst, "w"), indent=1); print(json.dumps(s))
PY
echo "[$(date -u '+%F %T')] post END classify rc=$c1/$c2" >> $L
