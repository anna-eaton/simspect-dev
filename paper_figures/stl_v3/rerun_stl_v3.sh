#!/bin/bash
# rerun_stl_v3.sh -- one faithful single-test rerun of a counted UV2 (A2 STLF bypass) E2w test for Fig. 7 v3 (agent figs-stl-race-v3, 2026-11-16).
# A copy of cafe3 /tests/bigcorpus_20261115/e2w/rerun_otb_v5.sh (agent fig8-otb-v5) with only the output dir changed:
#   config = the E2w row config (runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc, from the campaign's own code snapshot
#   /tests/bigcorpus_20261115/code), with only paths, keep_tmp=true, jobs=1, branch_modes=[mode] changed and the print-only debug flags
#   Commit, DelayUnit, Rename, IEW added (as rsa8_trace.py / rerun_otb_v5.sh). TMPDIR=/tmp, as shard_rows.py ran the campaign, so the gem5
#   work dir path has the campaign's length (BUGS.md H-STK). Timing point = the campaign's (pipeline.py _timing_grid_point, stem-only).
# Usage (inside cafe3 gem5_dev): bash rerun_stl_v3.sh <int|vec> <mispredict_not_taken|mispredict_taken> <stem>
#   vec = the corpus test (testset STT_6_u_core_lpP_s2A), int = its integer twin (STT_6_u_core_lpP_s2A_gprtwin).
# Output: /tests/bigcorpus_20261115/e2w/stl_v3/<ver>_<mode>_<stem>/ (run.log with start/end/rc, cfg.json, pipeline.log, res/,
#   pipeview.txt.gz, config.ini, stats.txt, branch-ann json, sha256s.txt). Copied to the Mac: simspect paper_figures/stl_v3/.
set -u
VER=$1; MODE=$2; STEM=$3
O=/tests/bigcorpus_20261115; CODE=$O/code
case $VER in int) TS=$O/testsets/STT_6_u_core_lpP_s2A_gprtwin;; vec) TS=$O/testsets/STT_6_u_core_lpP_s2A;; *) echo "bad version $VER"; exit 2;; esac
TAG=${VER}_${MODE#mispredict_}_${STEM}; W=$O/e2w/stl_v3/$TAG; LOG=$W/run.log
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
tar -C "$(dirname "$NEW")" -czf "$W/workdir.tgz" "$(basename "$NEW")"
echo "$NEW" > "$W/workdir.txt"
( cd "$W" && sha256sum pipeview.txt.gz cfg.json ts/X/$MODE/asm/$STEM.s ts/X/$MODE/ann/$STEM.ann.json $(find res -type f) config.ini stats.txt workdir.tgz 2>/dev/null; sha256sum /work/gem5-recon-modded/build/X86/gem5.opt /work/gem5-recon-modded/configs/example/se.py "$TS/$MODE/asm/$STEM.s" "$TS/$MODE/ann/$STEM.ann.json" ) > "$W/sha256s.txt"
rm -rf "$NEW"
echo "[$(date -u '+%F %T')] END $TAG rc=$RC (work dir archived to workdir.tgz and removed)"
