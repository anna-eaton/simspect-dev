O=/tests/bigcorpus_20261115; A=$O/e2w; TS=$O/testsets; CORP=STT_6_u_core_lpP_s2A; ROW=bc_E2w_STT_6_u_core_lpP_s2A; TW=${CORP}_gprtwin; cd $O/code
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900; L=$A/e2w_bucket.log
echo "[$(date -u '+%F %T')] REST: evidence for shards 12-35 (their shard configs were only on cafe1/cafe2; copied)" >> $L
i=100
for s in $(seq 12 35); do d=results/${ROW}_sh${s}__latest; C=$(readlink -f $d); n=$(basename $d); i=$((i+1)); W=/tmp/e2wev$i; mkdir -p $W
  ( timeout 10800 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src $TS/$CORP --code . --work $W --analyzer recon_stlf \
      --out $A/par/$n.json --kinds ld --keys-file $A/evidence_keys.txt --batch 64 --jobs 1 --extra-debug Commit > $A/par/$n.log 2>&1; rm -rf $W ) &
done; wait
python3 - $A/recon_stlf_evidence.json $A/par <<'PY' >> $L
import json, sys, glob
out = {}
for f in glob.glob(sys.argv[2] + "/*.json"):
    for k, v in json.load(open(f)).items(): out.setdefault(k, v)
json.dump(out, open(sys.argv[1], "w"), indent=1); print("evidence keys", len(out))
PY
TWD=$(ls -d results/${ROW}_gprtwin_sh*__latest | tr '\n' ' ')
python3 STAGE3_gem5/bugs/classify.py bucket --row $ROW --gate $A/gate.json --twin $TWD --twin-stems $TS/$TW/TWIN_STEMS.tsv --stlf $A/recon_stlf_evidence.json --json $A/buckets.json --per-stem $A/buckets_per_stem.json > $A/bucket.stdout 2>&1
echo "[$(date -u '+%F %T')] REST bucket rc=$? END" >> $L
