#!/usr/bin/env bash
# confirm_uv6_twin.sh (agent inttwin 2026-11-16) -- copy of scripts/sptrace_20261116/confirm_uv6.sh (the faithful UV6 confirmation) for one
# version of the SPT race rows. Changed ONLY: paths (the inttwin merged campaigns results/race_sptfence_d{4,1}_<T>_<ver>_merged, the corpus
# /tests/inttwin_20261116/testsets/<model>, the inttwin d4 config) and the output dir. Same rule: the first 40 (sorted) delay-induced
# not_taken stems whose d4 record drew cache_setup=warm, rerun with the campaign's exact per-test stalls (diag_stt_vp_squash_race.py,
# delay 4), then classify.py race. Run inside gem5_dev from /tests/inttwin_20261116/code:  bash scripts/inttwin_20261116/confirm_uv6_twin.sh fpr|int
# Out: /tests/inttwin_20261116/cls/uv6_confirm_<ver>/{hits.json,uv6_confirm_d4_stalled.json,uv6_classify_stalled.{json,txt}}; log alongside.
V=${1:?fpr|int}; O=/tests/inttwin_20261116; T=SPT_6_oneLP_v2_flat_ld_s2Aspt; M=mispredict_not_taken; cd $O/code; export TMPDIR=/tmp
MODEL=$T; [ $V = int ] && MODEL=${T}int
R=$O/cls/uv6_confirm_$V; S=$R/stage; rm -rf $S; mkdir -p $S; exec >> $R/confirm.log 2>&1
echo "START $(date -u) version $V model $MODEL"
python3 - $S/hits.json $V <<'PY'
import json, sys; sys.path.insert(0, "scripts/bigcorpus_20261115"); import race_scan as rs
V = sys.argv[2]; R = "results/race_sptfence_d%d_SPT_6_oneLP_v2_flat_ld_s2Aspt_" + V + "_merged"; m = "mispredict_not_taken"
d4, d1 = rs.load_recs(R % 4, m), rs.load_recs(R % 1, m)
st = sorted(n for n in d4 if n in d1 and d4[n].get("status") == d1[n].get("status") == "ok" and rs.wp_obtained(d4[n]) and not rs.wp_obtained(d1[n])
            and d4[n].get("cache_setup") == "warm")[:40]
json.dump([dict(name=s, issued_in_window=True) for s in st], open(sys.argv[1], "w")); print(len(st), "stems:", st)
PY
python3 - $S $V $MODEL <<'PY'
import json, sys; from pathlib import Path; sys.path.insert(0, "."); import pipeline
S = Path(sys.argv[1]); V, MODEL = sys.argv[2], sys.argv[3]; T = "SPT_6_oneLP_v2_flat_ld_s2Aspt"; M = "mispredict_not_taken"
cfg = pipeline.load_config(Path(f"runconfigs/inttwin_20261116/race_sptfence_d4_{T}_{V}.jsonc")); sw = cfg["sweep"]
stems = [r["name"] for r in json.load(open(S / "hits.json"))]; src = Path(f"/tests/inttwin_20261116/testsets/{MODEL}/{M}")
per, man, mx = pipeline._enumerate_grid_for_corpus([src / "asm" / f"{s}.s" for s in stems], src / "ann", sw)
assert mx == 1, mx
pipeline._materialise_grid_run(per[0], S, int(sw.get("unresolved_stall_cycles", 0)))
json.dump(man, open(S / "stalls_manifest.json", "w"), indent=1); print("staged", len(per[0]), "tests with campaign stalls")
PY
sed 's/"cache_setup": "random_all"/"cache_setup": "warm"/' runconfigs/inttwin_20261116/race_sptfence_d4_${T}_$V.jsonc > $S/diag_d4_warm.jsonc
grep -q '"cache_setup": "warm"' $S/diag_d4_warm.jsonc || { echo "ERROR cache_setup sed"; exit 1; }
export SIMSPECT_COMMIT_IEW_DELAY=4 SIMSPECT_GEM5_TIMEOUT_S=900
nice -n 5 python3 wiki/findings/bug/stt_slowcomm_vp_squash_race/diag_stt_vp_squash_race.py $S --config $S/diag_d4_warm.jsonc \
  --hits-from $S/hits.json --jobs 6 --out $R/uv6_confirm_d4_stalled.json
python3 STAGE3_gem5/bugs/classify.py race $R/uv6_confirm_d4_stalled.json --json $R/uv6_classify_stalled.json > $R/uv6_classify_stalled.txt 2>&1
cat $R/uv6_classify_stalled.txt; echo "END $(date -u)"
