#!/bin/bash
# rerun_otb_v5.sh -- one faithful single-test rerun of an E2w test for Fig. 8 v5 (agent fig8-otb-v5, 2026-11-16).
# Same as runconfigs/twostage_lp/eval_20261110/rsa8_trace.py (the R-SA-8 confirmation run) except that the FULL trace is kept:
#   config = the E2w row config (runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc; the gprtwin shard configs are
#   identical apart from results_name), with only paths, keep_tmp=true, jobs=1, branch_modes=[mode] changed and the print-only
#   debug flags Commit,DelayUnit,Rename (as rsa8_trace.py) + IEW added. TMPDIR=/tmp, as shard_rows.py ran the campaign, so the
#   gem5 work dir path has the campaign's length (H-STK). Timing point = the campaign's (pipeline.py _timing_grid_point, stem-only).
# Usage (inside cafe3 gem5_dev): rerun_otb_v5.sh <int|vec> <mispredict_not_taken|mispredict_taken> <stem>
#   int = the integer version (testset STT_6_u_core_lpP_s2A_gprtwin), vec = the vector version (STT_6_u_core_lpP_s2A, the corpus).
# Output: /tests/bigcorpus_20261115/e2w/otb_v5/<ver>_<mode>_<stem>/ (run.log with start/end/rc, cfg.json, pipeline.log, res/,
#   pipeview.txt.gz, config.ini, stats.txt, gem5 stdout/stderr if present, sha256s.txt).
set -u
VER=$1; MODE=$2; STEM=$3
O=/tests/bigcorpus_20261115; CODE=$O/code
case $VER in int) TS=$O/testsets/STT_6_u_core_lpP_s2A_gprtwin;; vec) TS=$O/testsets/STT_6_u_core_lpP_s2A;; *) echo "bad version $VER"; exit 2;; esac
TAG=${VER}_${MODE#mispredict_}_${STEM}; W=$O/e2w/otb_v5/$TAG; LOG=$W/run.log
rm -rf "$W"; mkdir -p "$W/ts/X/$MODE/asm" "$W/ts/X/$MODE/ann"
exec > >(tee -a "$LOG") 2>&1
echo "[$(date -u '+%F %T')] START $TAG host=$(hostname) ts=$TS"
cp "$TS/$MODE/asm/$STEM.s" "$W/ts/X/$MODE/asm/" && cp "$TS/$MODE/ann/$STEM.ann.json" "$W/ts/X/$MODE/ann/" || { echo "ERROR: test files missing"; exit 3; }
python3 - "$CODE/runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc" "$W" "$MODE" <<'PY'
import json, re, sys
c = json.loads(re.sub(r"//[^\n]*", "", open(sys.argv[1]).read())); W = sys.argv[2]
c["paths"].update(testset_dir=f"{W}/ts", results_dir=f"{W}/res", results_name="rr")
c.setdefault("pipeline", {})["keep_tmp"] = True; c["gem5"]["jobs"] = 1; c["gem5"].pop("sample_fraction", None)
c["speculation"]["branch_modes"] = [sys.argv[3]]
c["gem5"]["debug_flags"] = list(c["gem5"]["debug_flags"]) + ["Commit", "DelayUnit", "Rename", "IEW"]
json.dump(c, open(f"{W}/cfg.json", "w"), indent=1)
PY
cd "$CODE" || exit 4
ls -d /tmp/gem5_${STEM}_* 2>/dev/null | sort > "$W/tmp_before.txt"
export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900
nice -n 19 python3 pipeline.py gem5 --model X --config "$W/cfg.json" --force > "$W/pipeline.log" 2>&1; RC=$?
echo "[$(date -u '+%F %T')] pipeline rc=$RC"
ls -d /tmp/gem5_${STEM}_* 2>/dev/null | sort > "$W/tmp_after.txt"
NEW=$(comm -13 "$W/tmp_before.txt" "$W/tmp_after.txt")
echo "new tmp dirs: $NEW"
N=$(echo "$NEW" | grep -c . ); if [ "$N" != 1 ]; then echo "ERROR: expected 1 new work dir, got $N"; exit 5; fi
ls -la "$NEW" | tee "$W/workdir_listing.txt"
PV=$(find "$NEW" -name pipeview.txt | head -1); [ -n "$PV" ] || { echo "ERROR: no pipeview.txt"; exit 6; }
gzip -c "$PV" > "$W/pipeview.txt.gz"
for f in config.ini stats.txt simout simerr stdout stderr; do g=$(find "$NEW" -name "$f" | head -1); [ -n "$g" ] && cp "$g" "$W/"; done
find "$NEW" -maxdepth 2 \( -name '*.ann.json' -o -name '*branch*ann*' -o -name '*.json' \) -exec cp {} "$W/" \; 2>/dev/null
echo "$NEW" > "$W/workdir.txt"
( cd "$W" && sha256sum pipeview.txt.gz cfg.json ts/X/$MODE/asm/$STEM.s ts/X/$MODE/ann/$STEM.ann.json $(find res -type f) config.ini stats.txt 2>/dev/null; sha256sum /work/gem5-recon-modded/build/X86/gem5.opt /work/gem5-recon-modded/configs/example/se.py ) > "$W/sha256s.txt"
rm -rf "$NEW"
echo "[$(date -u '+%F %T')] END $TAG rc=$RC (work dir copied and removed)"
