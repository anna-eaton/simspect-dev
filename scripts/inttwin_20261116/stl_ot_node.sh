#!/usr/bin/env bash
# stl_ot_node.sh (agent inttwin 2026-11-16; coordinator: UV3 on store shadows must be final) -- the rstltriage method
# (scripts/rstltriage_20261116/: rstl_rerun.py faithful traced reruns + STAGE3_gem5/triage/oldest_taint_replay.py + classify.py bucket
# --oldest-taint) applied to every store-shadow record the E2w method leaves as an R-SA-8 candidate, a twin-hit ld, an untainted
# no-twin transmitter or unexplained, for both versions of one store-shadow row. FPR version: main = FPR test, twin = integer test;
# INT version: main = integer test (its replay record is reused as its own twin, the INT row's twin being itself).
# Waits for cls/<row>/DONE. Run inside gem5_dev from /tests/inttwin_20261116/code:  bash scripts/inttwin_20261116/stl_ot_node.sh <row>
# Out: cls/<row>/ot_keys_<ver>.txt, ot_<ver>.json (bucket --oldest-taint input), bucket_ot_<ver>.{json,stdout}, per_stem_ot_<ver>.json;
# reruns (gz traces) in /tests/inttwin_20261116/otwork/<row>_<ver>/ ; log logs/stl_ot.log
R=${1:?row}; O=/tests/inttwin_20261116; cd $O/code; export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 SIMSPECT_GEM5_MAX_TICK=2000000000
L=$O/logs/stl_ot.log; log(){ echo "[$(date -u '+%F %T')] $*" >> $L; }; D=$O/cls/$R
until [ -f $D/DONE ]; do sleep 120; done
cq(){ python3 -c "import json;print([c['$1'] for c in json.load(open('runconfigs/inttwin_20261116/campaigns.json')) if c['row']=='$R' and c['version']=='$2'][0])"; }
F=$(cq model fpr); I=$(cq model int); RNI=$(cq results_name int)
for V in fpr int; do
  python3 - $D/per_stem_$V.json $D/ot_keys_$V.txt $V $O/testsets/$F $O/testsets/$I <<'PY'
import json, sys
ps, out, v, F, I = sys.argv[1:]
pref = ("R-SA-8 candidate", "twin-hit ld", "untainted transmitter", "unexplained")
st = sorted({k.split("/")[-1] for k, l in json.load(open(ps)).items() if l.startswith(pref)})
lines = []
for s in st:
    if v == "fpr":
        lines += [f"main {F} {s}", f"twin {I} {s}"]
    else:
        lines += [f"main {I} {s}"]
open(out, "w").write("".join(l + "\n" for l in lines)); print(len(st), "stems")
PY
  RN=$(cq results_name $V); CF=$(cq config $V); W=$O/otwork/${R}_$V; mkdir -p $W
  log "START $R $V keys=$(wc -l < $D/ot_keys_$V.txt)"
  nice -n 5 python3 scripts/rstltriage_20261116/rstl_rerun.py --config $CF --keys $D/ot_keys_$V.txt --work $W --par 10 > $W/rerun.stdout 2>&1
  log "rerun rc=$?"
  ls -d $W/main_* $W/twin_* 2>/dev/null > $W/dirs.txt
  [ -s $W/dirs.txt ] && nice -n 5 python3 STAGE3_gem5/triage/oldest_taint_replay.py $(cat $W/dirs.txt) --json $W/replay.json > $W/replay.stdout 2>&1
  log "replay rc=$?"
  python3 - $W/replay.json $D/ot_$V.json $V <<'PY'
import json, os, sys
r = json.load(open(sys.argv[1])) if os.path.exists(sys.argv[1]) else {}
out = {}
for k, x in r.items():
    tag, s = k.split("_", 1); out[f"stl_bypass/{s}/{tag}"] = x
    if sys.argv[3] == "int" and tag == "main":
        out[f"stl_bypass/{s}/twin"] = x
json.dump(out, open(sys.argv[2], "w"), indent=1); print(len(out))
PY
  TW=$(ls -d results/${RNI}_sh*__latest | tr '\n' ' ')
  python3 STAGE3_gem5/bugs/classify.py bucket --row $RN --gate $D/gate.json --twin $TW --twin-stems $O/testsets/$I/FPR_PAIRS.tsv \
    --stlf $D/recon_stlf_$V.json --oldest-taint $D/ot_$V.json --json $D/bucket_ot_$V.json --per-stem $D/per_stem_ot_$V.json --examples 1000000 > $D/bucket_ot_$V.stdout 2>&1
  log "bucket_ot $R $V rc=$?"
done
touch $D/OT_DONE; log "DONE $R"
