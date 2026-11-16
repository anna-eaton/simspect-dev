#!/usr/bin/env bash
# reconstlhook: rerun recon_stlf evidence for the cafe3 shards (sh12-19; their configs were missing on cafe1 in the first pass),
# merge, and re-run classify.py bucket. Run in cafe1 gem5_dev from /tests/reconstlhook_20261116/code after rstl_bucket.sh ends.
O=/tests/reconstlhook_20261116; A=$O/bucket; ROW=rstl_E2w_Recon_6_u_stl_core_lpP_s2A; SRC=$(readlink -f $O/testsets/Recon_6_u_stl_core_lpP_s2A)
L=$A/rstl_bucket.log; log(){ echo "[$(date -u '+%F %T')] $*" | tee -a $L; }
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900
log "ev_rest START (sh12-19 evidence)"
i=100
for s in 12 13 14 15 16 17 18 19; do
  d=results/${ROW}_sh${s}__latest; C=$(readlink -f $d); n=$(basename $d); i=$((i+1)); W=/tmp/rstlev$i; mkdir -p $W
  ( timeout 10800 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src $SRC --code . --work $W --analyzer recon_stlf \
      --out $A/par/$n.json --kinds ld --keys-file $A/evidence_keys.txt --batch 64 --jobs 3 --extra-debug Commit > $A/par/$n.log 2>&1; rm -rf $W ) &
done
wait
python3 - $A/recon_stlf_evidence.json $A/par <<'PY' | tee -a $L
import json, sys, glob
out = {}
for f in glob.glob(sys.argv[2] + "/*.json"):
    for k, v in json.load(open(f)).items():
        out.setdefault(k, v)
json.dump(out, open(sys.argv[1], "w"), indent=1); print("evidence keys", len(out))
PY
TWD=$(ls -d results/${ROW}_gprtwin_sh*__latest | tr '\n' ' ')
python3 STAGE3_gem5/bugs/classify.py bucket --row $ROW --gate $A/gate.json --twin $TWD --twin-stems $O/testsets/Recon_6_u_stl_core_lpP_s2A_gprtwin/TWIN_STEMS.tsv \
    --stlf $A/recon_stlf_evidence.json --json $A/buckets.json --per-stem $A/buckets_per_stem.json --examples 1000000 > $A/bucket.stdout 2>&1
log "bucket rc=$?"; cat $A/bucket.stdout | tee -a $L
log "ev_rest END"
