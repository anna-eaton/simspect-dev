#!/usr/bin/env bash
# rebucket.sh -- re-bucket row E2w-stl with the rstltriage additions (agent rstltriage, 2026-11-16).
# Run in cafe1 gem5_dev from /tests/reconstlhook_20261116/triage/code (= the row's code snapshot ../../code + the changed
# classify.py, uv3_recon_oldest_taint.py, r_sa13_recon_sse_load.py, triage/rerun_hits_evidence.py, triage/oldest_taint_replay.py).
#   noflags : the new code with the row's original inputs        -> must equal ../../bucket/buckets.json (regression)
#   v2      : + recon_stlf evidence of inst-021161 re-made with the fixed window end (ev021161.json)
#             + oldest-taint replay evidence (oldest_taint_evidence.json, from rstl_rerun.py reruns + oldest_taint_replay.py)
# Log: <T>/rebucket.log
set -u
O=/tests/reconstlhook_20261116; A=$O/bucket; T=$O/triage; ROW=rstl_E2w_Recon_6_u_stl_core_lpP_s2A; TS=$O/testsets
TWS=$TS/Recon_6_u_stl_core_lpP_s2A_gprtwin/TWIN_STEMS.tsv; L=$T/rebucket.log
log(){ echo "[$(date -u '+%F %T')] $*" | tee -a $L; }
TWD=$(ls -d results/${ROW}_gprtwin_sh*__latest | tr '\n' ' ')
log START; mkdir -p $T/bucket_noflags $T/bucket_v2
python3 -c "import json,sys; e=json.load(open('$A/recon_stlf_evidence.json')); e.update(json.load(open('$T/ev021161.json'))); json.dump(e, open('$T/bucket_v2/recon_stlf_evidence.json','w'), indent=1)"
python3 STAGE3_gem5/bugs/classify.py bucket --row $ROW --gate $A/gate.json --twin $TWD --twin-stems $TWS --stlf $A/recon_stlf_evidence.json \
  --json $T/bucket_noflags/buckets.json --per-stem $T/bucket_noflags/buckets_per_stem.json --examples 1000000 > $T/bucket_noflags/bucket.stdout 2>&1
log "noflags rc=$?"
python3 STAGE3_gem5/bugs/_regress.py bucket $A/buckets.json $T/bucket_noflags/buckets.json > $T/bucket_noflags/regress.txt 2>&1
log "regress noflags vs original rc=$? ($T/bucket_noflags/regress.txt)"
python3 STAGE3_gem5/bugs/classify.py bucket --row $ROW --gate $A/gate.json --twin $TWD --twin-stems $TWS --stlf $T/bucket_v2/recon_stlf_evidence.json \
  --oldest-taint $T/oldest_taint_evidence.json --json $T/bucket_v2/buckets.json --per-stem $T/bucket_v2/buckets_per_stem.json --examples 1000000 > $T/bucket_v2/bucket.stdout 2>&1
log "v2 rc=$?"
python3 STAGE3_gem5/bugs/_regress.py bucket $A/buckets.json $T/bucket_v2/buckets.json > $T/bucket_v2/regress_vs_original.txt 2>&1
log "regress v2 vs original rc=$? (expected 1: only the 67 records change)"
python3 - $A/buckets_per_stem.json $T/bucket_v2/buckets_per_stem.json <<'PY' | tee $T/bucket_v2/changed_records.txt
import json, sys, collections
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])); c = collections.Counter()
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        c[(a.get(k), b.get(k))] += 1; print("CHANGED", k, "|", a.get(k), "->", b.get(k))
for (x, y), n in c.most_common(): print(n, x, "->", y)
print("records", len(a), len(b), "changed", sum(c.values()))
PY
log END
