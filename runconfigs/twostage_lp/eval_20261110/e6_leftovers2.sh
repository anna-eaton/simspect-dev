#!/bin/bash
# regen-lp 2026-11-10: E6 leftover diligence, part 2 (cafe2): recon_stlf evidence + reveal check on the faithful-twin hits
# of the 15 ld leftovers; reveal check on the 21 br_x R-SA-8 candidates whose transmitter was never in the delay unit.
set -u
R=/tests/simspect_alloy_20261108/loosepin_regen; cd $R/code_eval; E=runconfigs/twostage_lp/eval_20261110; T=/tests/simspect_alloy_20261108/testsets_twostage; B=$R/bugwork/e6_left; mkdir -p $B
echo "$(date -u '+%F %T') START"
C=$(readlink -f results/E6_Recon_6_u_core_lpP_fv3_ftwin_left__latest)
python3 - <<PY
import json,glob
keys=[]
for f in glob.glob("$C/mispredict_*/ld/window-results.json"):
    m=f.split("/")[-3]; x=json.load(open(f)); recs=x if isinstance(x,list) else (x.get("results") or list(x.values()))
    keys+=[m+"/"+r["name"].split("__")[0] for r in recs if isinstance(r,dict) and r.get("issued_in_window")]
open("$B/keys_ld_twinhit.txt","w").write("\n".join(sorted(keys))+"\n"); print("ld twin-hit keys", len(keys))
d=json.load(open("$R/bugwork/rsa8/e6_rsa8.json"))
open("$B/keys_brx_noinsert.txt","w").write("\n".join(sorted(k for k,v in d.items() if not v.get("rsa8_signature")))+"\n")
PY
mkdir -p /tmp/evF; python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src $T/Recon_6_u_core_lpP_fv3_ftwin_e6left --code . --work /tmp/evF --analyzer recon_stlf --out $B/twin_stlf.json --kinds ld --keys-file $B/keys_ld_twinhit.txt --batch 32 --jobs 16 --extra-debug Commit 2>&1 | tail -1; rm -rf /tmp/evF
python3 $E/reveal_check.py --config $E/E6_Recon_6_u_core_lpP_fv3_ftwin_left.jsonc --model Recon_6_u_core_lpP_fv3_ftwin_e6left --keys $B/keys_ld_twinhit.txt --out $B/reveal_ld_twin.json --jobs 16 --work $B/rv_ld
for t in e6 e6b e6c e6d; do
  python3 - <<PY
ts={tuple(l.split("\t")) for l in open("$T/Recon_6_u_core_lpP_fv3_gprtwin_$t/TWIN_STEMS.tsv").read().splitlines()[1:]}
k=[l.strip() for l in open("$B/keys_brx_noinsert.txt") if l.strip() and tuple(l.strip().split("/",1)) in ts]
open("$B/keys_brx_$t.txt","w").write("\n".join(k)+"\n")
PY
  python3 $E/reveal_check.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin.jsonc --model Recon_6_u_core_lpP_fv3_gprtwin_$t --keys $B/keys_brx_$t.txt --out $B/reveal_brx_twin.json --jobs 16 --work $B/rv_brx_$t
done
python3 - <<PY
import json
s=json.load(open("$B/twin_stlf.json")); r=json.load(open("$B/reveal_ld_twin.json")); rb=json.load(open("$B/reveal_brx_twin.json"))
for k in sorted(s): print("ld", k, (s[k].get("stl") or "")[-28:], "fwd", s[k].get("fwd"), "inwin", s[k].get("ready_in_window"), "reveal", r.get(k,{}).get("revealRequests"))
for k in sorted(rb): print("brx", k, "reveal", rb[k].get("revealRequests"), "allowlisted", rb[k].get("allowlistedTaintsFromTT"))
PY
echo "$(date -u '+%F %T') ALLDONE"
