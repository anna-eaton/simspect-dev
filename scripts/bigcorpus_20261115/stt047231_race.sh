#!/usr/bin/env bash
# stt047231_race.sh -- sanity line for the STT race (agent bigcorpus 2026-11-15): the paper's race test inst-047231 (wiki/findings/bug/
# stt_slowcomm_vp_squash_race/, old STT_6 corpus) under TODAY's code and the bigcorpus STT race configs (E3 gem5 block, random_all, se_exp.py)
# at commitToIEWDelay 1/3/4 on /work/stt and /work/stt-master; check_ld default stall (direct check_ld call, no timing grid).
# Run on a node inside gem5_dev from <OUT>/code: bash scripts/bigcorpus_20261115/stt047231_race.sh  -> <OUT>/race/stt047231_<tree>_d<d>.json
set -u
O=/tests/bigcorpus_20261115; cd $O/code; mkdir -p $O/race /tmp/stt047231; export TMPDIR=/tmp
cp wiki/findings/bug/stt_slowcomm_vp_squash_race/inst-047231.{s,ann.json} /tmp/stt047231/
for tag in stt sttmaster; do for d in 1 3 4; do
  C=runconfigs/bigcorpus_20261115/race_${tag}_d${d}_STT_6_u_core_lpP_s2A.jsonc
  ( eval "$(python3 - "$C" <<'PY'
import sys, shlex, os; sys.path.insert(0, "."); import pipeline; from pathlib import Path
cfg = pipeline.load_config(Path(sys.argv[1])); env = pipeline._build_gem5_env(cfg["gem5"], cfg.get("speculation", {}))
for k, v in env.items():
    if k.startswith("SIMSPECT_") and os.environ.get(k) != str(v): print(f"export {k}={shlex.quote(str(v))}")
print(f"export SIMSPECT_COMMIT_IEW_DELAY={cfg['race_knobs']['commitToIEWDelay']}")
PY
)"
    python3 STAGE3_gem5/check_ld.py /tmp/stt047231 --jobs 1 --scheme 2 --out $O/race/stt047231_${tag}_d$d.json > $O/race/stt047231_${tag}_d$d.log 2>&1 )
  python3 - $O/race/stt047231_${tag}_d$d.json <<'PY'
import json, sys; sys.path.insert(0, "scripts/bigcorpus_20261115"); import race_scan as rs
for r in json.load(open(sys.argv[1])):
    print(sys.argv[1].split("/")[-1], r.get("status"), "class", rs.classify(r), "wp_obtained", rs.wp_obtained(r), "fate", r.get("cache_fate"), "pkt", r.get("packet_tick"), "sq", r.get("load_squash_tick"), "in_window", r.get("issued_in_window"), "res", [b.get("resolve_tick") for b in r.get("branch_resolutions") or []])
PY
done; done
