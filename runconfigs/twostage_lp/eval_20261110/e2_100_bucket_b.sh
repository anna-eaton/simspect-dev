#!/bin/bash
# regen-lp 2026-11-10: E2 100% bucketing on cafe3 (twin d built on cafe2 and copied): sharded GPR twin run, recon_stlf
# evidence for statically unexplained keys (in parallel with the twin) then for new twin-hit keys, reveal check on twin d,
# bucket_eval with twins a/b/c (copies) + d shards. Log: bugwork/e2_100_bucket.out.
set -u
R=/tests/simspect_alloy_20261108/loosepin_regen; cd $R/code_eval
E=runconfigs/twostage_lp/eval_20261110; B=$R/bugwork/e2_stlf; T=/tests/simspect_alloy_20261108/testsets_twostage; ROW=E2_STT_6_u_core_lpP_fv3; C=../eval_results/twin_copies
echo "$(date -u '+%F %T') START (b: parallel evidence; twin d shards already running)"
python3 $E/evidence_keys.py --gate ../eval_results/gate_STT_100pct.json --row $ROW --out $B/keys100_other.txt --skip $B/recon_stlf_evidence.json
cp $B/recon_stlf_evidence.json $B/recon_stlf_evidence.pre100.json; rm -rf $B/par
( bash $E/run_evidence_par.sh $ROW STT_6_u_core_lpP_fv3 $B/keys100_other.txt $B/recon_stlf_evidence.json 2 > $B/run_other100.log 2>&1; echo DONE >> $B/run_other100.log ) &
# twin d shards were launched by the first attempt (shard_run.py, 10 shards); wait for their EXIT lines
TW=$(for k in 0 1 2 3 4 5 6 7 8 9; do echo -n "results/E2_STT_6_u_core_lpP_fv3_gprtwin_d_sh${k}__latest "; done)
until [ "$(cat $R/logs/eval_E2_STT_6_u_core_lpP_fv3_gprtwin_d_sh*.log 2>/dev/null | grep -c EXIT)" = "10" ]; do sleep 60; done
echo "$(date -u '+%F %T') twin d shards done: $TW"
wait
echo "$(date -u '+%F %T') other-class evidence done: $(tail -2 $B/run_other100.log | head -1)"
python3 - <<PY
import json,glob,os
ev=set(json.load(open("$B/recon_stlf_evidence.json")))
keys=set()
for d in glob.glob("results/E2_STT_6_u_core_lpP_fv3_gprtwin_d_sh*__latest"):
    for f in glob.glob(os.path.realpath(d)+"/mispredict_*/ld/window-results.json"):
        m=f.split("/")[-3]; x=json.load(open(f)); recs=x if isinstance(x,list) else (x.get("results") or list(x.values()))
        keys|={m+"/"+r["name"].split("__")[0] for r in recs if isinstance(r,dict) and r.get("issued_in_window")}
new=sorted(keys-ev); open("$B/keys100_twinhit.txt","w").write("\n".join(new)+"\n"); print("twin-hit keys", len(keys), "new", len(new))
PY
bash $E/run_evidence_par.sh $ROW STT_6_u_core_lpP_fv3 $B/keys100_twinhit.txt $B/recon_stlf_evidence.json 4 | tail -1
python3 - <<PY
import json
d=json.load(open("$B/recon_stlf_evidence.json")); rv=json.load(open("$B/reveal_evidence_twin.json"))
ts={tuple(l.split("\t")) for l in open("$T/STT_6_u_core_lpP_fv3_gprtwin_e2d/TWIN_STEMS.tsv").read().splitlines()[1:]}
k=[x for x,r in d.items() if "isTainted=0" in (r.get("stl") or "") and x not in rv and tuple(x.split("/",1)) in ts]
open("$B/keys100_untainted_d.txt","w").write("\n".join(k)+"\n"); print("reveal keys", len(k))
PY
python3 $E/reveal_check.py --config $E/E2_STT_6_u_core_lpP_fv3_gprtwin_d.jsonc --model STT_6_u_core_lpP_fv3_gprtwin_e2d --keys $B/keys100_untainted_d.txt --out $B/reveal_evidence_twin.json --jobs 40 --work $R/bugwork/reveal_twin_e2d
cp $T/STT_6_u_core_lpP_fv3_gprtwin_e2d/TWIN_STEMS.tsv $C/TWIN_STEMS_e2d.tsv
python3 $E/bucket_eval.py --row $ROW --gate ../eval_results/gate_STT_100pct.json \
  --twin $C/E2_STT_6_u_core_lpP_fv3_gprtwin $C/E2_STT_6_u_core_lpP_fv3_gprtwin_b $C/E2_STT_6_u_core_lpP_fv3_gprtwin_c $TW \
  --twin-stems $C/TWIN_STEMS_e2.tsv $C/TWIN_STEMS_e2b.tsv $C/TWIN_STEMS_e2c.tsv $C/TWIN_STEMS_e2d.tsv \
  --stlf $B/recon_stlf_evidence.json --reveal $B/reveal_evidence_twin.json --json ../eval_results/buckets_E2_100pct.json
echo "$(date -u '+%F %T') ALLDONE"
