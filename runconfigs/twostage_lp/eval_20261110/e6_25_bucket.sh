#!/bin/bash
# regen-lp 2026-11-10: E6 25% bucketing (evidence for new twin-hit + unexplained keys, reveal check on twin c, bucket_eval)
set -u
cd /tests/simspect_alloy_20261108/loosepin_regen/code_eval
E=runconfigs/twostage_lp/eval_20261110; B=/tests/simspect_alloy_20261108/loosepin_regen/bugwork/e6_stlf; T=/tests/simspect_alloy_20261108/testsets_twostage
python3 $E/evidence_keys.py --gate ../eval_results/gate_E6_25pct.json --row E6_Recon_6_u_core_lpP_fv3 --out $B/keys25_other.txt --skip $B/recon_stlf_evidence.json
python3 - <<PY
import json,glob,os
ev=set(json.load(open("$B/recon_stlf_evidence.json")))
keys=set(l.strip() for l in open("$B/keys25_other.txt") if l.strip())
for f in glob.glob(os.path.realpath("results/E6_Recon_6_u_core_lpP_fv3_gprtwin_c__latest")+"/mispredict_*/ld/window-results.json"):
    m=f.split("/")[-3]; x=json.load(open(f)); recs=x if isinstance(x,list) else (x.get("results") or list(x.values()))
    keys|={m+"/"+r["name"].split("__")[0] for r in recs if isinstance(r,dict) and r.get("issued_in_window")}
new=sorted(keys-ev); open("$B/keys25_all.txt","w").write("\n".join(new)+"\n"); print("evidence keys", len(new))
PY
for d in results/E6_Recon_6_u_core_lpP_fv3__latest results/E6_Recon_6_u_core_lpP_fv3_sh[0-9]__latest results/E6_Recon_6_u_core_lpP_fv3_sh25_*__latest; do
  C=$(readlink -f $d); W=/tmp/ev_E6; mkdir -p $W
  timeout 3600 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src $T/Recon_6_u_core_lpP_fv3 --code . --work $W --analyzer recon_stlf --out $B/recon_stlf_evidence.json --kinds ld --keys-file $B/keys25_all.txt --batch 64 --jobs 12 --extra-debug Commit 2>&1 | grep -E "hit keys|end"
  cp $W/logs/*.log $B/ 2>/dev/null; rm -rf $W
done
python3 - <<PY
import json
d=json.load(open("$B/recon_stlf_evidence.json")); rv=json.load(open("$B/reveal_evidence_twin.json"))
ts={tuple(l.split("\t")) for l in open("$T/Recon_6_u_core_lpP_fv3_gprtwin_e6c/TWIN_STEMS.tsv").read().splitlines()[1:]}
k=[x for x,r in d.items() if "isTainted=0" in (r.get("stl") or "") and x not in rv and tuple(x.split("/",1)) in ts]
open("$B/keys25_untainted_c.txt","w").write("\n".join(k)+"\n"); print("reveal keys", len(k))
PY
python3 $E/reveal_check.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin_c.jsonc --model Recon_6_u_core_lpP_fv3_gprtwin_e6c --keys $B/keys25_untainted_c.txt --out $B/reveal_evidence_twin.json --jobs 12 --work /tests/simspect_alloy_20261108/loosepin_regen/bugwork/reveal_twin_e6c
python3 $E/bucket_eval.py --row E6_Recon_6_u_core_lpP_fv3 --gate ../eval_results/gate_E6_25pct.json --twin results/E6_Recon_6_u_core_lpP_fv3_gprtwin__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_b__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_c__latest --twin-stems $T/Recon_6_u_core_lpP_fv3_gprtwin_e6/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6b/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6c/TWIN_STEMS.tsv --stlf $B/recon_stlf_evidence.json --reveal $B/reveal_evidence_twin.json --json ../eval_results/buckets_E6_25pct.json
echo ALLDONE
