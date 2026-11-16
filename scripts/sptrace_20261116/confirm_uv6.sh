#!/usr/bin/env bash
# confirm_uv6.sh (agent sptrace 2026-11-16) -- UV6 confirmation sample: re-run gem5 (diag_stt_vp_squash_race.py, delay 4, the d4 run_config env)
# on the first 40 (sorted by stem) delay-induced not_taken stems whose d4 campaign record drew cache_setup=warm (the diag builds binaries
# directly, and gem5_common applies non-warm setups only inside process_one, so only warm draws can be re-run faithfully; the diag config is
# the d4 config with cache_setup warm), then STAGE3_gem5/bugs/classify.py race. Per-test stalls = the campaign's timing-grid draw, materialised with pipeline._enumerate_grid_for_corpus/_materialise_grid_run.
# Run inside gem5_dev from /tests/sptrace_20261116/code. Out: race/uv6_confirm_d4_stalled.json, race/uv6_classify_stalled.txt, log logs/confirm_uv6.log
O=/tests/sptrace_20261116; T=SPT_6_oneLP_v2_flat_ld_s2Aspt; M=mispredict_not_taken; cd $O/code; export TMPDIR=/tmp
echo "START $(date -u)"
S=$O/uv6_stage; rm -rf $S; mkdir -p $S
python3 - $S/hits.json <<'PY'
import json, sys; sys.path.insert(0, "scripts/bigcorpus_20261115"); import race_scan as rs
R = "results/sptrace_fence_d%d_SPT_6_oneLP_v2_flat_ld_s2Aspt__latest"; m = "mispredict_not_taken"
d4, d1 = rs.load_recs(R % 4, m), rs.load_recs(R % 1, m)
st = sorted(n for n in d4 if n in d1 and d4[n].get("status") == d1[n].get("status") == "ok" and rs.wp_obtained(d4[n]) and not rs.wp_obtained(d1[n])
            and d4[n].get("cache_setup") == "warm")[:40]
json.dump([dict(name=s, issued_in_window=True) for s in st], open(sys.argv[1], "w")); print(len(st), "stems:", st)
PY
# Materialise the campaign's exact per-test stalls (sweep.timing_grid draw) into the staged ann, with pipeline.py's own grid code.
python3 - $S <<'PY'
import json, sys; from pathlib import Path; sys.path.insert(0, "."); import pipeline
S = Path(sys.argv[1]); T = "SPT_6_oneLP_v2_flat_ld_s2Aspt"; M = "mispredict_not_taken"
cfg = pipeline.load_config(Path(f"runconfigs/sptrace_20261116/race_sptfence_d4_{T}.jsonc")); sw = cfg["sweep"]
stems = [r["name"] for r in json.load(open(S / "hits.json"))]; src = Path(f"/tests/sptrace_20261116/testsets/{T}/{M}")
per, man, mx = pipeline._enumerate_grid_for_corpus([src / "asm" / f"{s}.s" for s in stems], src / "ann", sw)
assert mx == 1, mx
pipeline._materialise_grid_run(per[0], S, int(sw.get("unresolved_stall_cycles", 0)))
json.dump(man, open(S / "stalls_manifest.json", "w"), indent=1); print("staged", len(per[0]), "tests with campaign stalls")
PY
sed 's/"cache_setup": "random_all"/"cache_setup": "warm"/' runconfigs/sptrace_20261116/race_sptfence_d4_$T.jsonc > $S/diag_d4_warm.jsonc
grep -q '"cache_setup": "warm"' $S/diag_d4_warm.jsonc || { echo "ERROR cache_setup sed"; exit 1; }
export SIMSPECT_COMMIT_IEW_DELAY=4 SIMSPECT_GEM5_TIMEOUT_S=900
nice -n 5 python3 wiki/findings/bug/stt_slowcomm_vp_squash_race/diag_stt_vp_squash_race.py $S --config $S/diag_d4_warm.jsonc \
  --hits-from $S/hits.json --jobs 6 --out $O/race/uv6_confirm_d4_stalled.json
python3 STAGE3_gem5/bugs/classify.py race $O/race/uv6_confirm_d4_stalled.json --json $O/race/uv6_classify_stalled.json > $O/race/uv6_classify_stalled.txt 2>&1
cat $O/race/uv6_classify_stalled.txt; echo "END $(date -u)"
