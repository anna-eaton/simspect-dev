#!/bin/bash
# regen-lp 2026-11-10: E6 100% bucketing on cafe2: merged gate, GPR twin of the new plain hit stems (twin d), recon_stlf
# evidence (new twin hits + statically unexplained keys) on the main + shard runs, reveal check on twin d, bucket_eval with
# all four twins. Log: bugwork/e6_100_bucket.out (stdout of this script).
set -u
R=/tests/simspect_alloy_20261108/loosepin_regen; cd $R/code_eval
E=runconfigs/twostage_lp/eval_20261110; B=$R/bugwork/e6_stlf; T=/tests/simspect_alloy_20261108/testsets_twostage; ROW=E6_Recon_6_u_core_lpP_fv3
echo "$(date -u '+%F %T') START (resume b: gate + twin build already done; twin d run sharded)"
TW=$(python3 $E/shard_run.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin_d.jsonc --model Recon_6_u_core_lpP_fv3_gprtwin_e6d --k 8 --jobs 6 --tag sh --wait | tr "\n" " ")
echo "twin d shards done: $TW"
python3 $E/evidence_keys.py --gate ../eval_results/gate_E6_100pct.json --row $ROW --out $B/keys100_other.txt --skip $B/recon_stlf_evidence.json
python3 - <<PY
import json,glob,os
ev=set(json.load(open("$B/recon_stlf_evidence.json")))
keys=set(l.strip() for l in open("$B/keys100_other.txt") if l.strip())
for f in [g for d in glob.glob("results/E6_Recon_6_u_core_lpP_fv3_gprtwin_d_sh*__latest") for g in glob.glob(os.path.realpath(d)+"/mispredict_*/ld/window-results.json")]:
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
  --twin results/E6_Recon_6_u_core_lpP_fv3_gprtwin__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_b__latest results/E6_Recon_6_u_core_lpP_fv3_gprtwin_c__latest $TW \
  --twin-stems $T/Recon_6_u_core_lpP_fv3_gprtwin_e6/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6b/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6c/TWIN_STEMS.tsv $T/Recon_6_u_core_lpP_fv3_gprtwin_e6d/TWIN_STEMS.tsv \
  --stlf $B/recon_stlf_evidence.json --reveal $B/reveal_evidence_twin.json --json ../eval_results/buckets_E6_100pct.json
echo "$(date -u '+%F %T') ALLDONE"
