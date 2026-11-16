#!/bin/bash
# regen-lp 2026-11-10: E6 100% bucketing on cafe2: merged gate, GPR twin of the new plain hit stems (twin d), recon_stlf
# evidence (new twin hits + statically unexplained keys) on the main + shard runs, reveal check on twin d, bucket_eval with
# all four twins. Log: bugwork/e6_100_bucket.out (stdout of this script).
set -u
R=/tests/simspect_alloy_20261108/loosepin_regen; cd $R/code_eval
E=runconfigs/twostage_lp/eval_20261110; B=$R/bugwork/e6_stlf; T=/tests/simspect_alloy_20261108/testsets_twostage; ROW=E6_Recon_6_u_core_lpP_fv3
echo "$(date -u '+%F %T') START"
python3 $E/eval_gate.py --fraction 1.0 --names $ROW --examples 1000000 --json ../eval_results/gate_E6_100pct.json | grep -E "_merge|tests"
python3 - <<PY
import json
d=json.load(open("../eval_results/gate_E6_100pct.json"))["campaigns"]["$ROW"]
old=set()
for f in ("e6_hits_2pct.txt","e6_hits_10pct_new.txt","e6_hits_25pct_new.txt"): old|=set(open("$R/"+f).read().split())
st=set()
for k,v in d.items():
    if "/plain" in k and "examples" in v:
        for cl,ex in v["examples"].items():
            if not cl.startswith("disq"): st|=set(ex)
new=sorted(st-old); open("$R/e6_hits_100pct_new.txt","w").write("\n".join(new)+"\n"); print("plain hit stems", len(st), "new", len(new))
PY
(cd $R/code && bash make_gpr_twin.sh Recon_6_u_core_lpP_fv3 ../e6_hits_100pct_new.txt Recon_6_u_core_lpP_fv3_gprtwin_e6d && tail -2 $T/Recon_6_u_core_lpP_fv3_gprtwin_e6d/make_gpr_twin.log)
sed 's/Recon_6_u_core_lpP_fv3_gprtwin_e6 (make/Recon_6_u_core_lpP_fv3_gprtwin_e6d (make/; s/"E6_Recon_6_u_core_lpP_fv3_gprtwin"/"E6_Recon_6_u_core_lpP_fv3_gprtwin_d"/; s/"jobs": 16/"jobs": 40/' $E/E6_Recon_6_u_core_lpP_fv3_gprtwin.jsonc > $E/E6_Recon_6_u_core_lpP_fv3_gprtwin_d.jsonc
TMPDIR=/tmp python3 -u testrun.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin_d.jsonc --model Recon_6_u_core_lpP_fv3_gprtwin_e6d --once --max-new 1000000 >> ../logs/eval_E6_gprtwin_d.log 2>&1; echo "twin d rc=$?"
python3 $E/evidence_keys.py --gate ../eval_results/gate_E6_100pct.json --row $ROW --out $B/keys100_other.txt --skip $B/recon_stlf_evidence.json
python3 - <<PY
import json,glob,os
ev=set(json.load(open("$B/recon_stlf_evidence.json")))
keys=set(l.strip() for l in open("$B/keys100_other.txt") if l.strip())
for f in glob.glob(os.path.realpath("results/E6_Recon_6_u_core_lpP_fv3_gprtwin_d__latest")+"/mispredict_*/ld/window-results.json"):
    m=f.split("/")[-3]; x=json.load(open(f)); recs=x if isinstance(x,list) else (x.get("results") or list(x.values()))
    keys|={m+"/"+r["name"].split("__")[0] for r in recs if isinstance(r,dict) and r.get("issued_in_window")}
new=sorted(keys-ev); open("$B/keys100_all.txt","w").write("\n".join(new)+"\n"); print("evidence keys", len(new))
PY
bash $E/run_evidence.sh $ROW Recon_6_u_core_lpP_fv3 $B/keys100_all.txt $B/recon_stlf_evidence.json 24
python3 - <<PY
import json
d=json.load(open("$B/recon_stlf_evidence.json")); rv=json.load(open("$B/reveal_evidence_twin.json"))
ts={tuple(l.split("\t")) for l in open("$T/Recon_6_u_core_lpP_fv3_gprtwin_e6d/TWIN_STEMS.tsv").read().splitlines()[1:]}
k=[x for x,r in d.items() if "isTainted=0" in (r.get("stl") or "") and x not in rv and tuple(x.split("/",1)) in ts]
open("$B/keys100_untainted_d.txt","w").write("\n".join(k)+"\n"); print("reveal keys", len(k))
PY
python3 $E/reveal_check.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin_d.jsonc --model Recon_6_u_core_lpP_fv3_gprtwin_e6d --keys $B/keys100_untainted_d.txt --out $B/reveal_evidence_twin.json --jobs 24 --work $R/bugwork/reveal_twin_e6d
python3 $E/bucket_eval.py --row $ROW --gate ../eval_results/gate_E6_100pct.json \
  --twin results/E6_Recon_6_u_core_lpP_fv3_gprtwin__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_b__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_c__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_d__latest \
  --twin-stems $T/Recon_6_u_core_lpP_fv3_gprtwin_e6/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6b/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6c/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6d/TWIN_STEMS.tsv \
  --stlf $B/recon_stlf_evidence.json --reveal $B/reveal_evidence_twin.json --json ../eval_results/buckets_E6_100pct.json
echo "$(date -u '+%F %T') ALLDONE"
