#!/usr/bin/env bash
# rerun_keep.sh (inspector-v7-agent, 2026-11-16) -- re-run confirmed UV6 SPT-Fence race stems with the trace KEPT, exactly as
# scripts/sptrace_20261116/confirm_uv6.sh ran them: same code tree (/tests/sptrace_20261116/code), same staged inputs with the campaign's
# per-test stalls (/tests/sptrace_20261116/uv6_stage, read-only), same config (uv6_stage/diag_d4_warm.jsonc = race_sptfence_d4 with
# cache_setup warm), same env (SIMSPECT_COMMIT_IEW_DELAY=4, SIMSPECT_GEM5_TIMEOUT_S=900, TMPDIR=/tmp). The only change: a copy of
# diag_stt_vp_squash_race.py with its final shutil.rmtree(workdir) replaced by recording the workdir, so the trace survives.
# Run inside cafe2 gem5_dev: bash /tests/race_v4_20261116/rerun_keep.sh inst-000012 [more stems]   Log: /tests/race_v4_20261116/logs/rerun.log
set -uo pipefail
O=/tests/race_v4_20261116; C=/tests/sptrace_20261116/code; S=/tests/sptrace_20261116/uv6_stage
mkdir -p $O/logs $O/out; exec > >(tee -a $O/logs/rerun.log) 2>&1
echo "START $(date -u +%FT%TZ) stems: $*"
D=$C/wiki/findings/bug/stt_slowcomm_vp_squash_race/diag_stt_vp_squash_race.py
sha256sum $D $S/diag_d4_warm.jsonc; md5sum /work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt
sed -e "s|^REPO = HERE.parents\[3\].*|REPO = Path('$C')|" \
    -e "s|^        shutil.rmtree(wd, ignore_errors=True)|        rec['workdir'] = str(wd)  # kept (race_v4): was shutil.rmtree(wd)|" $D > $O/diag_keep.py
diff $D $O/diag_keep.py
python3 - "$O/out/hits.json" "$@" <<'PY'
import json, sys; json.dump([dict(name=s, issued_in_window=True) for s in sys.argv[2:]], open(sys.argv[1], "w"))
PY
for s in "$@"; do sha256sum $S/$s.s $S/$s.ann.json; python3 -c "import json;a=json.load(open('$S/$s.ann.json'));print('$s stalls', [(e.get('branch_pc'),e.get('mode'),e.get('resolve_stall_cycles')) for e in a['annotations']])"; done
cd $C && export TMPDIR=/tmp SIMSPECT_COMMIT_IEW_DELAY=4 SIMSPECT_GEM5_TIMEOUT_S=900
nice -n 5 python3 $O/diag_keep.py $S --config $S/diag_d4_warm.jsonc --hits-from $O/out/hits.json --jobs 3 --out $O/out/race_keep.json; echo "rc=$?"
cat $O/out/race_keep.json
echo "END $(date -u +%FT%TZ)"
