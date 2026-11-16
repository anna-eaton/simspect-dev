#!/usr/bin/env bash
# e2w_bucket.sh -- bucket the gated E2w hits (ReCon-STT on STT_6_u_core_lpP_s2A, warm) into known causes, the regen-lp method
# (runconfigs/twostage_lp/eval_20261110/e2_100_bucket.sh) with paths and the Stage-2 recipe adapted (agent bigcorpus, 2026-11-16):
#  1. GPR twin of every stem with a gated PLAIN hit: the same Alloy XML through recipe A (stage2_final_A) with ONLY fpr.enabled false.
#     Faithful (kept in TWIN_STEMS.tsv) only if the corpus test is not an RMW-transmitter test (rmw_stems.tsv), has no jmp filler
#     (vocab_rj.jmp_filler_before_pcs empty) and the twin's vocab_rj equals the corpus test's (same RMW/jmp draws).
#  2. Twin run: E2w config, 12 testrun shards (shard_rows.py) on this host.
#  3. recon_stlf evidence (rerun_hits_evidence.py --analyzer recon_stlf --extra-debug Commit) on the ld keys the static rules leave
#     'other' plus the ld keys that hit in the twin; one process per E2w shard campaign.
#  4. classify.py bucket (A2 = paper UV2, R-SA-8 candidates = paper UV3, R-SA-13, ...).
# Run inside cafe3 gem5_dev from <O>/code: bash scripts/bigcorpus_20261115/e2w_bucket.sh   Log: <O>/e2w/e2w_bucket.log; outputs <O>/e2w/
set -u
O=/tests/bigcorpus_20261115; A=$O/e2w; TS=$O/testsets; CORP=STT_6_u_core_lpP_s2A; TW=${CORP}_gprtwin; ROW=bc_E2w_STT_6_u_core_lpP_s2A
cd $O/code; L=$A/e2w_bucket.log; log(){ echo "[$(date -u '+%F %T')] $*" | tee -a $L; }
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900
log START
# 1. twin stems + twin corpus
python3 - $A/gate.json $ROW $A/twin_stems.txt <<'PY'
import json, sys
g = json.load(open(sys.argv[1]))["campaigns"][sys.argv[2]]; st = set()
for k, v in g.items():
    if k.endswith("_merge") or not k.endswith("/plain"):
        continue
    for cl, ex in v.get("examples", {}).items():
        if not cl.startswith("disq"):
            st |= set(ex)
open(sys.argv[3], "w").write("".join(s + "\n" for s in sorted(st))); print("twin stems", len(st))
PY
mkdir -p $TS/$TW/xml
while read -r s; do cp $TS/${CORP}_base/xml/$s.xml $TS/$TW/xml/ 2>/dev/null || cp $TS/$CORP/xml/$s.xml $TS/$TW/xml/; cp $TS/$CORP/xml/$s.txt $TS/$TW/xml/ 2>/dev/null; done < $A/twin_stems.txt
python3 - $A <<'PY'
import json, re, sys
t = open("runconfigs/bigcorpus_20261115/stage2_final_A.jsonc").read(); c = json.loads(re.sub(r"//[^\n]*", "", t))
c["fpr"]["enabled"] = False; c["paths"]["testset_dir"] = "/tests/bigcorpus_20261115/testsets"; c["gem5"]["jobs"] = 32
open(sys.argv[1] + "/stage2_gprtwin_A.jsonc", "w").write("// GPR twin (e2w_bucket.sh): runconfigs/bigcorpus_20261115/stage2_final_A.jsonc with ONLY fpr.enabled false (+ abs testset_dir, asm jobs)\n" + json.dumps(c, indent=1))
PY
python3 STAGE1_alloy/models/proposed_twophase/stage2_sharded.py --config $A/stage2_gprtwin_A.jsonc --model $TW --jobs 32 --shard-size 20 --first-fraction 0 >> $L 2>&1
log "twin stage2 rc=$?"
python3 - $TS/$CORP $TS/$TW <<'PY' | tee -a $L
import json, os, sys
F, T = sys.argv[1], sys.argv[2]
rmw = {tuple(l.split("\t")[:2]) for l in open(F + "/rmw_stems.tsv").read().splitlines()[1:] if l}
keep, why = [], {"no corpus ann": 0, "rmw": 0, "jmp filler": 0, "vocab_rj differs": 0, "no twin ann": 0}
for m in ("mispredict_not_taken", "mispredict_taken"):
    for f in sorted(os.listdir(f"{T}/{m}/ann")):
        s = f[:-9]; fa = f"{F}/{m}/ann/{f}"
        a = json.load(open(fa)) if os.path.exists(fa) else None; b = json.load(open(f"{T}/{m}/ann/{f}"))
        bad = ("no corpus ann" if a is None else "rmw" if (m, s) in rmw else "jmp filler" if (a.get("vocab_rj") or {}).get("jmp_filler_before_pcs")
               else "vocab_rj differs" if a.get("vocab_rj") != b.get("vocab_rj") else None)
        if bad:
            why[bad] += 1
            for d, e in (("asm", ".s"), ("ann", ".ann.json")):
                p = f"{T}/{m}/{d}/{s}{e}"
                if os.path.exists(p): os.remove(p)
        else:
            keep.append((m, s))
open(T + "/TWIN_STEMS.tsv", "w").write("mode\tstem\n" + "".join(f"{m}\t{s}\n" for m, s in keep))
open(T + "/MANIFEST.tsv", "w").write("stem\tmodes\n" + "".join(f"{s}\t{m}\n" for m, s in keep))
print(f"twin kept {len(keep)} faithful (mode, stem) tests; dropped {why}")
PY
# 2. twin run (12 shards here, wait for all)
python3 scripts/bigcorpus_20261115/shard_rows.py --corpus $TW --config runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc --name ${ROW}_gprtwin --k 12 --mine 0-11 >> $L 2>&1
sleep 60; while pgrep -f "testrun.py --config runconfigs/bigcorpus_20261115/shards/${ROW}_gprtwin" >/dev/null; do sleep 60; done
log "twin run done"
# 3. recon_stlf evidence: static 'other' ld keys + ld keys that hit in the twin
python3 - $A/gate.json $ROW $A/evidence_keys.txt <<'PY' | tee -a $L
import json, sys, glob, os
g = json.load(open(sys.argv[1]))["campaigns"][sys.argv[2]]; keys = set()
for k, v in g.items():
    if k.endswith("_merge") or "/ld/" not in k:
        continue
    m = k.split("/")[0]
    for cl, ex in v.get("examples", {}).items():
        if cl.startswith("other"):
            keys |= {f"{m}/{s}" for s in ex}
n0 = len(keys)
for d in glob.glob(f"results/{sys.argv[2]}_gprtwin_sh*__latest"):
    for f in glob.glob(os.path.realpath(d) + "/mispredict_*/ld/window-results.json"):
        m = f.split("/")[-3]; x = json.load(open(f)); recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
        keys |= {f"{m}/{r['name'].split('__')[0]}" for r in recs if isinstance(r, dict) and r.get("issued_in_window")}
open(sys.argv[3], "w").write("".join(k + "\n" for k in sorted(keys))); print("evidence keys: static other", n0, "total with twin hits", len(keys))
PY
mkdir -p $A/par; echo '{}' > $A/recon_stlf_evidence.json; i=0
for d in results/${ROW}_sh*__latest; do
  C=$(readlink -f $d); n=$(basename $d); i=$((i+1)); W=/tmp/e2wev$i; mkdir -p $W
  ( timeout 10800 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign $C --testset-src $TS/$CORP --code . --work $W --analyzer recon_stlf \
      --out $A/par/$n.json --kinds ld --keys-file $A/evidence_keys.txt --batch 64 --jobs 2 --extra-debug Commit > $A/par/$n.log 2>&1; rm -rf $W ) &
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
# 4. bucket
TWD=$(ls -d results/${ROW}_gprtwin_sh*__latest | tr '\n' ' ')
python3 STAGE3_gem5/bugs/classify.py bucket --row $ROW --gate $A/gate.json --twin $TWD --twin-stems $TS/$TW/TWIN_STEMS.tsv \
    --stlf $A/recon_stlf_evidence.json --json $A/buckets.json --per-stem $A/buckets_per_stem.json > $A/bucket.stdout 2>&1
log "bucket rc=$? (see $A/bucket.stdout, $A/buckets.json)"
log END
