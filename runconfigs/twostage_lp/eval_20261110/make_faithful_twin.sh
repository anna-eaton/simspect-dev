#!/usr/bin/env bash
# make_faithful_twin.sh -- regen-lp (2026-11-10): GPR-only twin of selected stems that ALSO carries the corpus test's
# RMW rewrite and jmp insert, for leftover hits that make_gpr_twin.sh cannot twin (it drops RMW / jmp tests).
#   1. Stage 2 of the stems' XML with ONLY fpr.enabled false (stage2_fv3_stream.jsonc otherwise unchanged) -> <twin>_plain
#   2. make_rmw_corpus.py --select eligible --fraction 1.0 --complete -> <twin>_rmwall (every eligible ld xmit rewritten)
#   3. per (mode, stem): the RMW version if the corpus test is in rmw_stems.tsv (must have been rewritten in step 2), else
#      the plain one -> <twin>_asm
#   4. make_jmp_corpus.py --p 0.5 --seed 20261109 (same per-stem draw as the corpus) -> <twin>
#   5. keep a (mode, stem) only if RMW-ness and the jmp insert (presence and before_pc) equal the corpus test's;
#      TWIN_STEMS.tsv lists the kept tests, TWIN_MISMATCH.tsv the rest with the reason.
# Run inside gem5_dev on the node holding <corpus>_base (cafe2), from the loosepin_regen code root.
# Usage: make_faithful_twin.sh <corpus> <stems file> <twin name>     Log: <twin>/make_faithful_twin.log
set -eu
CORPUS=$1; STEMS=$2; TWIN=$3
TS=/tests/simspect_alloy_20261108/testsets_twostage; B=$TS/${CORPUS}_base; F=$TS/$CORPUS; T=$TS/$TWIN; P=${T}_plain
mkdir -p $P/xml $T; L=$T/make_faithful_twin.log; echo "$(date -u '+%F %T') START corpus=$CORPUS stems=$(wc -l < $STEMS) twin=$TWIN" >> $L
while read -r s; do [ -n "$s" ] && cp $B/xml/$s.xml $B/xml/$s.txt $P/xml/ 2>/dev/null || true; done < $STEMS
python3 - "$P" <<'PY'
import json, re, sys
t = open("runconfigs/regen_lp_20261110/stage2_fv3_stream.jsonc").read()
c = json.loads(re.sub(r"//[^\n]*", "", t)); c["fpr"]["enabled"] = False
open(sys.argv[1] + "/stage2_gprtwin.jsonc", "w").write("// faithful GPR twin: stage2_fv3_stream.jsonc with ONLY fpr.enabled false\n" + json.dumps(c, indent=1))
PY
python3 STAGE1_alloy/models/proposed_twophase/stage2_sharded.py --config $P/stage2_gprtwin.jsonc --model ${TWIN}_plain --jobs 16 --first-fraction 0 >> $L 2>&1
python3 STAGE2_compilation/make_rmw_corpus.py --repo-root . --src $P --dst ${T}_rmwall --fraction 1.0 --seed 20261109 --select eligible --complete --jobs 16 >> $L 2>&1
python3 - "$F" "$P" "${T}_rmwall" "${T}_asm" <<'PY' >> $L
import os, shutil, sys
F, P, RA, A = sys.argv[1:5]
rmw = {tuple(l.split("\t")[:2]) for l in open(F + "/rmw_stems.tsv").read().splitlines()[1:] if l}
rwa = {tuple(l.split("\t")[:2]) for l in open(RA + "/rmw_stems.tsv").read().splitlines()[1:] if l}
os.makedirs(A, exist_ok=True); os.path.exists(A + "/xml") or os.symlink(P + "/xml", A + "/xml")
for m in ("mispredict_not_taken", "mispredict_taken"):
    for d in ("asm", "ann", "llvm"):
        os.makedirs(f"{A}/{m}/{d}", exist_ok=True)
    for f in os.listdir(f"{P}/{m}/ann"):
        s = f[:-9]; src = RA if ((m, s) in rmw and (m, s) in rwa) else P
        for d, e in (("asm", ".s"), ("ann", ".ann.json")):
            shutil.copy2(f"{src}/{m}/{d}/{s}{e}", f"{A}/{m}/{d}/{s}{e}")
        if os.path.exists(f"{P}/{m}/llvm/{s}.ann.json"):
            shutil.copy2(f"{P}/{m}/llvm/{s}.ann.json", f"{A}/{m}/llvm/{s}.ann.json")
print("assembled", A)
PY
python3 STAGE2_compilation/make_jmp_corpus.py --repo-root . --src ${T}_asm --dst $T --p 0.5 --seed 20261109 --jobs 16 >> $L 2>&1
python3 - "$F" "$T" "${T}_rmwall" <<'PY' >> $L
import json, os, sys
F, T, RA = sys.argv[1:4]
rmw = {tuple(l.split("\t")[:2]) for l in open(F + "/rmw_stems.tsv").read().splitlines()[1:] if l}
rwa = {tuple(l.split("\t")[:2]) for l in open(RA + "/rmw_stems.tsv").read().splitlines()[1:] if l}
keep, bad = [], []
for m in ("mispredict_not_taken", "mispredict_taken"):
    for f in sorted(os.listdir(f"{T}/{m}/ann")):
        s = f[:-9]; a = json.load(open(f"{T}/{m}/ann/{f}")); o = json.load(open(f"{F}/{m}/ann/{f}"))
        why = []
        if ((m, s) in rmw) and ((m, s) not in rwa):
            why.append("corpus RMW, twin not RMW-eligible")
        ja, jo = a.get("jmp_insert"), o.get("jmp_insert")
        if bool(ja) != bool(jo) or (ja and jo and ja.get("before_pc") != jo.get("before_pc")):
            why.append(f"jmp differs (twin {ja and ja.get('before_pc')}, corpus {jo and jo.get('before_pc')})")
        if why:
            bad.append((m, s, "; ".join(why)))
            for d, e in (("asm", ".s"), ("ann", ".ann.json")):
                os.remove(f"{T}/{m}/{d}/{s}{e}")
        else:
            keep.append((m, s))
open(T + "/TWIN_STEMS.tsv", "w").write("mode\tstem\n" + "".join(f"{m}\t{s}\n" for m, s in keep))
open(T + "/TWIN_MISMATCH.tsv", "w").write("mode\tstem\treason\n" + "".join(f"{m}\t{s}\t{w}\n" for m, s, w in bad))
print(f"faithful twin kept {len(keep)}, mismatched {len(bad)}")
PY
echo "$(date -u '+%F %T') END" >> $L
