#!/usr/bin/env bash
# s2_twin.sh (agent inttwin 2026-11-16) -- build the integer twin of one FPR corpus. Runs INSIDE gem5_dev, code root /tests/inttwin_20261116/code.
# Usage: s2_twin.sh <family>   family = STT | Recon | STL | SPT
#  1. stems = every stem with a compiled FPR test (asm + ann) in the corpus; their Stage-1.5 XMLs (+ .txt) are copied into the twin's xml/
#  2. Stage 2 = stage2_sharded.py with the integer-twin recipe (runconfigs/inttwin_20261116/stage2_*_int.jsonc) where ONLY
#     paths.testset_dir (-> /tests/inttwin_20261116/testsets) and gem5.jobs (asm compile parallelism, 32) are changed, as
#     launch_stage2.sh did for the FPR corpora (testset_dir + jobs 24). Same parsexml code path (fpr off => fpr.p code inert).
#  3. MANIFEST.tsv / rmw_stems.tsv / jmp_stems.tsv for twin AND an FPR wrapper dir (/tests/inttwin_20261116/testsets/<FPR corpus>:
#     symlinks to the corpus's mode dirs + xml; tsvs regenerated with stream_fp.vocab_rows' rules, compared with the corpus's own tsvs)
#  4. checks: same (mode, stem) set in both, 0 missing; pairdiff.py on 50 programs and on all pairs.
# Log: /tests/inttwin_20261116/logs/s2_<family>.log ; outputs /tests/inttwin_20261116/s2check/<family>_*.json ; READY + DONE markers.
set -u
O=/tests/inttwin_20261116; F=${1:?family}; cd $O/code || exit 1
L=$O/logs/s2_$F.log; mkdir -p $O/s2check $O/cfg; log(){ echo "[$(date -u '+%F %T')] $*" | tee -a $L; }
case $F in
  STT)   SRC=/tests/bigcorpus_20261115/testsets/STT_6_u_core_lpP_s2A;   FC=STT_6_u_core_lpP_s2A;   TW=STT_6_u_core_lpP_s2Aint;   R=stage2_final_A_int.jsonc;;
  Recon) SRC=/tests/bigcorpus_20261115/testsets/Recon_6_u_core_lpP_s2A; FC=Recon_6_u_core_lpP_s2A; TW=Recon_6_u_core_lpP_s2Aint; R=stage2_final_A_int.jsonc;;
  STL)   SRC=$O/src/Recon_6_u_stl_core_lpP_s2A;                         FC=Recon_6_u_stl_core_lpP_s2A; TW=Recon_6_u_stl_core_lpP_s2Aint; R=stage2_stl_A_int.jsonc;;
  SPT)   SRC=$O/src/SPT_6_oneLP_v2_flat_ld_s2Aspt;                      FC=SPT_6_oneLP_v2_flat_ld_s2Aspt; TW=SPT_6_oneLP_v2_flat_ld_s2Asptint; R=stage2_final_A_spt_int.jsonc;;
  *) echo "bad family $F"; exit 2;;
esac
TS=$O/testsets; T0=$(date +%s)
log "START $F src=$SRC twin=$TS/$TW recipe=runconfigs/inttwin_20261116/$R (sha256 $(sha256sum runconfigs/inttwin_20261116/$R | cut -c1-16))"
[ -e $TS/$TW/READY ] && { log "twin READY exists, skipping Stage 2"; }
# 1. stems + xml
python3 - $SRC $TS/$TW <<'PY' | tee -a $L
import os, shutil, sys
src, tw = sys.argv[1], sys.argv[2]
modes = [m for m in ("mispredict_not_taken", "mispredict_taken", "stl_bypass") if os.path.isdir(f"{src}/{m}/asm")]
per = {m: {f[:-2] for f in os.listdir(f"{src}/{m}/asm") if f.endswith(".s") and os.path.exists(f"{src}/{m}/ann/{f[:-2]}.ann.json")} for m in modes}
stems = sorted(set().union(*per.values()))
os.makedirs(f"{tw}/xml", exist_ok=True); n = 0
for s in stems:
    for e in (".xml", ".txt"):
        p = f"{src}/xml/{s}{e}"
        if os.path.exists(p) and not os.path.exists(f"{tw}/xml/{s}{e}"):
            shutil.copy2(p, f"{tw}/xml/{s}{e}"); n += 1
miss = [s for s in stems if not os.path.exists(f"{tw}/xml/{s}.xml")]
open(f"{tw}/FPR_PAIRS.tsv", "w").write("mode\tstem\n" + "".join(f"{m}\t{s}\n" for m in modes for s in sorted(per[m])))
print(f"modes {modes} fpr tests " + " ".join(f"{m}={len(per[m])}" for m in modes) + f" programs {len(stems)} xml copied {n} xml missing {len(miss)} {miss[:3]}")
PY
# 2. Stage 2
C=$O/cfg/${TW}_stage2.jsonc
sed -e "s#\"testset_dir\": *\"[^\"]*\"#\"testset_dir\": \"$TS\"#" -e '0,/"jobs": *[0-9]*/s//"jobs": 32/' runconfigs/inttwin_20261116/$R > $C
python3 - runconfigs/inttwin_20261116/$R $C <<'PY' | tee -a $L
import json, re, sys
l = lambda p: json.loads(re.sub(r"//[^\n]*", "", open(p).read()))
a, b = l(sys.argv[1]), l(sys.argv[2])
def d(x, y, p=""):
    o = []
    for k in sorted(set(x) | set(y)):
        if isinstance(x.get(k), dict) and isinstance(y.get(k), dict): o += d(x[k], y[k], p + k + ".")
        elif x.get(k) != y.get(k): o.append(p + k)
    return o
print("stream cfg differs from recipe in:", d(a, b), "| fpr:", b["fpr"]["enabled"], "| modes:", b["speculation"]["branch_modes"])
PY
if [ ! -e $TS/$TW/READY ]; then
  export TMPDIR=/tmp
  nice -n 5 python3 STAGE1_alloy/models/proposed_twophase/stage2_sharded.py --config $C --model $TW --jobs 32 --shard-size 20 --first-fraction 0 >> $L 2>&1
  log "stage2_sharded rc=$? ($(( $(date +%s) - T0 )) s)"
fi
# 3+4. tsvs, wrapper, checks
python3 - $SRC $TS $FC $TW <<'PY' 2>&1 | tee -a $L
import json, os, sys
src, TS, fc, tw = sys.argv[1:]
T = f"{TS}/{tw}"; W = f"{TS}/{fc}"
modes = [m for m in ("mispredict_not_taken", "mispredict_taken", "stl_bypass") if os.path.isdir(f"{src}/{m}/asm")]
fpr = {tuple(l.split("\t")) for l in open(f"{T}/FPR_PAIRS.tsv").read().splitlines()[1:] if l}
got = {(m, f[:-2]) for m in modes if os.path.isdir(f"{T}/{m}/asm") for f in os.listdir(f"{T}/{m}/asm") if f.endswith(".s") and os.path.exists(f"{T}/{m}/ann/{f[:-2]}.ann.json")}
extra = sorted(got - fpr); missing = sorted(fpr - got)
for m, s in extra:   # twin test whose FPR test does not exist: not part of the pair set
    for d, e in (("asm", ".s"), ("ann", ".ann.json")):
        p = f"{T}/{m}/{d}/{s}{e}"
        if os.path.exists(p): os.rename(p, p + ".nofpr")
print(f"pairs: fpr {len(fpr)} twin {len(got)} missing_in_twin {len(missing)} {missing[:5]} extra_in_twin(moved aside) {len(extra)} {extra[:5]}")
def rows(base):
    rr, jr, man = [], [], {}
    for m, s in sorted(fpr):
        p = f"{base}/{m}/ann/{s}.ann.json"
        if not os.path.exists(p): continue
        a = json.load(open(p)); v = a.get("vocab_rj") or {}; x = a.get("xmit") or {}
        man.setdefault(s, []).append(m)
        if x.get("pc") in v.get("rmw_pcs", []): rr.append([m, s, "load_rmw_or0 (Stage 2)", str(x.get("addr_hex"))])
        for k in v.get("jmp_filler_before_pcs", []): jr.append([m, s, str(k), "", ""])
    return rr, jr, man
def write(base, out):
    rr, jr, man = rows(base)
    open(f"{out}/rmw_stems.tsv", "w").write("mode\tstem\torig_instr\txmit_addr\n" + "".join("\t".join(r) + "\n" for r in rr))
    open(f"{out}/jmp_stems.tsv", "w").write("mode\tstem\tbefore_pc\tjmp_addr\tn_candidates\n" + "".join("\t".join(r) + "\n" for r in jr))
    open(f"{out}/MANIFEST.tsv", "w").write("stem\tmodes\n" + "".join(f"{s}\t{','.join(ms)}\n" for s, ms in sorted(man.items())))
    return rr, jr
os.makedirs(W, exist_ok=True)
for m in modes + ["xml"]:
    if not os.path.lexists(f"{W}/{m}"): os.symlink(f"{src}/{m}", f"{W}/{m}")
fr, fj = write(src, W); ir, ij = write(T, T)
key = lambda r: tuple(r[:3]) if len(r) > 3 else tuple(r)
print(f"rmw rows fpr {len(fr)} twin {len(ir)} same(mode,stem) {sorted(r[:2] for r in fr) == sorted(r[:2] for r in ir)}; "
      f"jmp rows fpr {len(fj)} twin {len(ij)} same {sorted(r[:3] for r in fj) == sorted(r[:3] for r in ij)}")
for nm in ("rmw_stems.tsv", "jmp_stems.tsv"):
    if os.path.exists(f"{src}/{nm}"):
        own = sorted(tuple(l.split("\t")[:2]) for l in open(f"{src}/{nm}").read().splitlines()[1:] if l)
        mine = sorted(tuple(l.split("\t")[:2]) for l in open(f"{W}/{nm}").read().splitlines()[1:] if l)
        print(f"corpus's own {nm}: {len(own)} rows; regenerated {len(mine)}; (mode,stem) multiset equal {own == mine}")
    else:
        print(f"corpus has no {nm} (regenerated one in the wrapper)")
PY
python3 scripts/inttwin_20261116/pairdiff.py $TS/$FC $TS/$TW --sample 50 --json $O/s2check/${F}_pairdiff50.json 2>&1 | tee -a $L; r50=${PIPESTATUS[0]}
python3 scripts/inttwin_20261116/pairdiff.py $TS/$FC $TS/$TW --json $O/s2check/${F}_pairdiff_all.json 2>&1 | tail -8 | tee -a $L; rall=${PIPESTATUS[0]}
log "pairdiff rc 50=$r50 all=$rall"
if [ "$r50" = 0 ] && [ "$rall" = 0 ]; then
  echo "READY $(date -u) inttwin: $TW = integer twin of $FC (recipe runconfigs/inttwin_20261116/$R), pairdiff clean" > $TS/$TW/READY
fi
echo "rc50=$r50 rcall=$rall $(date -u) $(( $(date +%s) - T0 ))s" > $O/logs/s2_$F.DONE
log "END $F ($(( $(date +%s) - T0 )) s)"
