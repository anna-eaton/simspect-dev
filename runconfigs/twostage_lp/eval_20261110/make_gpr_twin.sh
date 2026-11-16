#!/usr/bin/env bash
# make_gpr_twin.sh -- regen-lp (2026-11-10): build the GPR-only twin of selected stems of a v3 corpus, for the twin half of
# diag_recon_sse_load_producer.py / diag_stt_xmm4_skip.py (does a hit need the xmm routing?).
# Twin = the same Alloy XML through Stage 2 with ONLY fpr.enabled false (stage2_fv3 otherwise unchanged), NO RMW / jmp
# post-pass. It is a faithful twin only for stems whose corpus test is neither an RMW test nor carries a jmp insert;
# those are listed in <twin>/TWIN_STEMS.tsv (mode, stem) and the others are dropped from the twin testset.
# Run inside gem5_dev on the node holding <corpus>_base (cafe2), from the loosepin_regen code root (has stage2_sharded).
# Usage: make_gpr_twin.sh <corpus> <stems file (one stem per line)> <twin name>      Log: <twin>/make_gpr_twin.log
set -eu
CORPUS=$1; STEMS=$2; TWIN=$3
TS=/tests/simspect_alloy_20261108/testsets_twostage; B=$TS/${CORPUS}_base; F=$TS/$CORPUS; T=$TS/$TWIN
mkdir -p $T/xml; L=$T/make_gpr_twin.log; echo "$(date -u '+%F %T') START corpus=$CORPUS stems=$(wc -l < $STEMS) twin=$TWIN" >> $L
while read -r s; do [ -n "$s" ] && cp $B/xml/$s.xml $B/xml/$s.txt $T/xml/ 2>/dev/null || true; done < $STEMS
python3 - "$T" <<'PY'
import json, re, sys
src = "runconfigs/regen_lp_20261110/stage2_fv3_stream.jsonc"; t = open(src).read()
c = json.loads(re.sub(r"//[^\n]*", "", t)); c["fpr"]["enabled"] = False
open(sys.argv[1] + "/stage2_gprtwin.jsonc", "w").write("// GPR twin: stage2_fv3_stream.jsonc with ONLY fpr.enabled false (make_gpr_twin.sh)\n" + json.dumps(c, indent=1))
PY
python3 STAGE1_alloy/models/proposed_twophase/stage2_sharded.py --config $T/stage2_gprtwin.jsonc --model $TWIN --jobs 24 --first-fraction 0 >> $L 2>&1
python3 - "$F" "$T" <<'PY' >> $L
import json, os, sys
F, T = sys.argv[1], sys.argv[2]
rmw = {tuple(l.split("\t")[:2]) for l in open(F + "/rmw_stems.tsv").read().splitlines()[1:] if l}
keep, drop = [], 0
for m in ("mispredict_not_taken", "mispredict_taken"):
    for f in sorted(os.listdir(f"{T}/{m}/ann")):
        s = f[:-9]
        a = json.load(open(f"{F}/{m}/ann/{f}")) if os.path.exists(f"{F}/{m}/ann/{f}") else None
        if a is None or (m, s) in rmw or "jmp_insert" in a:
            for d, e in (("asm", ".s"), ("ann", ".ann.json")):
                p = f"{T}/{m}/{d}/{s}{e}"
                if os.path.exists(p): os.remove(p)
            drop += 1
        else:
            keep.append((m, s))
open(T + "/TWIN_STEMS.tsv", "w").write("mode\tstem\n" + "".join(f"{m}\t{s}\n" for m, s in keep))
print(f"twin kept {len(keep)} (mode, stem) tests (corpus test plain: no RMW, no jmp insert), dropped {drop}")
PY
echo "$(date -u '+%F %T') END" >> $L
