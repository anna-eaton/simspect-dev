#!/usr/bin/env python3
"""make_configs.py -- writes runconfigs/bigcorpus_20261115/* (agent bigcorpus, 2026-11-15; Anna: "make sure that the big
corpus can find [all our bugs] ... make sure that the race is on spt and stt").

Every config is a COPY of a validated source config; only paths / corpus names / sample fractions (and, for the race rows,
the gem5 config_script se.py -> se_exp.py plus a provenance block race_knobs) change. Each output starts with a // header
naming its source and every changed key. Rerun to regenerate (idempotent). Run from the repo root on the Mac.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "runconfigs/bigcorpus_20261115"
O = "/tests/bigcorpus_20261115"
TS = f"{O}/testsets"


def load(p):
    t = (ROOT / p).read_text()
    return json.loads(re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S)))


def write(name, cfg, src, changes):
    hdr = (f"// bigcorpus 2026-11-15 (agent bigcorpus): copy of {src} written by scripts/bigcorpus_20261115/make_configs.py.\n"
           f"// Changed ONLY: {changes}\n// Docs: wiki/state/RUNNING.md 'Big corpus 2026-11-15'; results -> wiki/state/EVAL_MANIFEST.md 'Big corpus bug coverage (2026-11-15)'.\n")
    (D / name).write_text(hdr + json.dumps(cfg, indent=2) + "\n")
    return name


out = []
D.mkdir(parents=True, exist_ok=True)

# ---- Stage 1b (Alloy) configs -------------------------------------------------------------------------------------------
for F in ("STT_6_u", "Recon_6_u"):
    src = f"runconfigs/overnight_20261111/twostage_{F}.jsonc"; c = load(src)
    c["paths"]["testset_dir"] = TS
    T = c["twostage_lp"]
    T["corpus"] = f"{F}_core_lpP_s2A"
    T["stage2_config"] = "runconfigs/bigcorpus_20261115/stage2_final_A.jsonc"
    T["stage1"]["reuse_cores"] = [f"{O}/cores/{F}_core_ri/k3/stage1_xml"]
    out.append(write(f"twostage_{F}.jsonc", c, src, "paths.testset_dir, twostage_lp.corpus, stage2_config, stage1.reuse_cores (node paths)"))

src = "runconfigs/twostage_lp/Footprint_6_u.jsonc"; c = load(src); s = load("runconfigs/overnight_20261111/twostage_STT_6_u.jsonc")
c["paths"]["testset_dir"] = TS
T = c["twostage_lp"]
T["corpus"] = "Footprint_6_u_core_lpP_s2A"
T["stage2_config"] = "runconfigs/bigcorpus_20261115/stage2_final_A.jsonc"
T["stage2_postpasses"] = False
T["stage1"] = {"reuse_cores": [f"{O}/cores/Footprint_6_u_core_ri/k2/stage1_xml", f"{O}/cores/Footprint_6_u_core_ri/k3/stage1_xml"],
               "reuse_sha256": "e99079ebd7c4d32ccc5e1120e036b41241bf02d6a08db8236d251b958b3b41fc"}
T["stage15"] = s["twostage_lp"]["stage15"]
T["stream"] = s["twostage_lp"]["stream"]
out.append(write("twostage_Footprint_6_u.jsonc", c, src,
                 "paths.testset_dir, corpus, stage2_config (final recipe A), stage2_postpasses false (RMW/jmp from vocab_rj), "
                 "stage1 = reuse the 1,411 regen-lp cores (k2 11 + k3 1,400, from experiments/2026-11-10_footprint_vs_amulet data tarball; "
                 "body sha256 e99079eb of Footprint_6_u_core_ri.als), stage15 + stream blocks = the overnight STT_6_u final-recipe values "
                 "(target_distinct 60000, budget 9000 s, cap 100, 600 s jobs, 28 slots, shuffle seed 20261115)"))

# ---- Stage 2 configs (final recipe) --------------------------------------------------------------------------------------
for R in ("A", "B"):
    src = f"runconfigs/overnight_20261111/stage2_final_{R}.jsonc"; c = load(src)
    c["paths"]["testset_dir"] = TS; c["paths"]["results_name"] = f"bc_stage2_final_{R}"
    out.append(write(f"stage2_final_{R}.jsonc", c, src, "paths.testset_dir, paths.results_name"))

camps = []
# ---- Footprint gem5 rows (AMuLeT parity, random_all, 3x3 timing grid) -----------------------------------------------------
for row, dfn in (("T1g", "invisispec"), ("T2g", "cleanupspec"), ("T3g", "speclfb")):
    for m in ("Footprint_6_u_core_lpP_s2A", "Footprint_6_u_core_lpP_s2B", "Footprint_6_u_nov10_s2A", "Footprint_6_u_nov10_s2B"):
        src = f"runconfigs/firstdet_final_20261110/{row}_Footprint_6_u_core_lpP_fv3.jsonc"; c = load(src)
        c["paths"]["testset_dir"] = TS; c["paths"]["results_dir"] = f"{O}/results"; c["paths"]["results_name"] = f"bc_{row}_{m}"
        out.append(write(f"{row}_{m}.jsonc", c, src, "paths.testset_dir/results_dir/results_name (corpus " + m + ")"))

# ---- STT / ReCon eval rows ------------------------------------------------------------------------------------------------
JOBS = {"E2": 8, "E3": 8, "E4": 4, "E6": 24}
o3 = load("runconfigs/overnight_20261111/E3_STT_6_u_core_lpP_s2A.jsonc")
for row, fam, node in (("E2", "STT_6_u", "cafe3"), ("E3", "STT_6_u", "cafe3"), ("E6", "Recon_6_u", "cafe2"), ("E4", "STT_6_u", "cafe3")):
    for R in ("A", "B"):
        m = f"{fam}_core_lpP_s2{R}"
        if row == "E4":
            src = "runconfigs/twostage_lp/eval_20261110/E4_STT_6_u_core_lpP_fv3.jsonc"; c = load(src)
            g = c["gem5"]; g.pop("sample_fraction", None)
            g.update(jobs=20, cache_setup="random_all", cache_setup_fill_bytes="32kB", sample_fraction=0.25)
            c["sweep"] = o3["sweep"]; c["speculation"] = o3["speculation"]
            ch = ("paths; gem5.sample_fraction 0.1 -> 0.25 (corroboration row; E3 is SimSpect's STT row), jobs 20, cache_setup random_all, "
                  "cache_setup_fill_bytes 32kB (= its --l1d_size=32kB extra_arg), sweep = 3x3 timing_grid, both modes (the overnight E3 changes)")
        else:
            src = f"runconfigs/overnight_20261111/{row}_{m}.jsonc"; c = load(src); ch = "paths only"
        c["paths"].update(testset_dir=TS, results_dir=f"{O}/results", results_name=f"bc_{row}_{m}")
        c["gem5"]["jobs"] = JOBS[row]; ch += f"; gem5.jobs {JOBS[row]} (throughput only: cafe3 is shared by ~10 rows on 64 cores)"
        n = write(f"{row}_{m}.jsonc", c, src, ch); out.append(n)
        camps.append(dict(recipe=R, row=row, node=node, kind="eval", config=f"runconfigs/bigcorpus_20261115/{n}", model=m,
                          results_name=f"bc_{row}_{m}"))

# ---- E2w: ReCon-STT on the (partial) STT_6_u corpus A, WARM cache (regen-lp E2 protocol), for the OTB / R-SA-8 check (Anna 2026-11-16)
src = "runconfigs/bigcorpus_20261115/E2_STT_6_u_core_lpP_s2A.jsonc"; c = load(src)
c["gem5"].pop("cache_setup", None); c["gem5"].pop("cache_setup_fill_bytes", None); c["gem5"]["jobs"] = 4
c["paths"]["results_name"] = "bc_E2w_STT_6_u_core_lpP_s2A"
out.append(write("E2w_STT_6_u_core_lpP_s2A.jsonc", c, src, "gem5.cache_setup / cache_setup_fill_bytes removed (= warm, the regen-lp E2 eval protocol "
                 "runconfigs/twostage_lp/eval_20261110/E2_*), gem5.jobs 4 (per shard; run by shard_rows.py), results_name"))

# ---- Race rows: commitToIEWDelay sweep on the STT_6_u A corpus --------------------------------------------------------------
RACE_FRAC = 0.1
base = load("runconfigs/bigcorpus_20261115/E3_STT_6_u_core_lpP_s2A.jsonc")
for tree, tag in (("/work/stt", "stt"), ("/work/stt-master", "sttmaster")):
    for d in (1, 3, 4):
        c = json.loads(json.dumps(base)); m = "STT_6_u_core_lpP_s2A"
        c["gem5"]["binary"] = f"{tree}/build/X86/gem5.opt"; c["gem5"]["config_script"] = f"{tree}/configs/example/se_exp.py"
        c["gem5"]["sample_fraction"] = RACE_FRAC; c["gem5"]["jobs"] = 4
        c["race_knobs"] = {"commitToIEWDelay": d, "applied_via": "env SIMSPECT_COMMIT_IEW_DELAY (set from this key by scripts/bigcorpus_20261115/gem5_row.sh) read by se_exp.py; no other knob set (iewToCommitDelay, squashWidth, com sizes stay O3 defaults)"}
        rn = f"bc_race_{tag}_d{d}_{m}"; c["paths"]["results_name"] = rn
        n = write(f"race_{tag}_d{d}_{m}.jsonc", c, "runconfigs/bigcorpus_20261115/E3_STT_6_u_core_lpP_s2A.jsonc",
                  f"gem5.binary/config_script -> {tree} se_exp.py (= se.py + env-driven O3 delay knobs, gem5-hooks/stt/se_exp.py), "
                  f"gem5.sample_fraction {RACE_FRAC}, gem5.jobs 4, race_knobs.commitToIEWDelay {d}, results_name")
        out.append(n); camps.append(dict(recipe="A", row=f"race_{tag}_d{d}", node="cafe3", kind="race", config=f"runconfigs/bigcorpus_20261115/{n}",
                                         model=m, results_name=rn))
src = "runconfigs/overnight_20261111/E11_SPT_6_u_core_lpP_s2A.jsonc"
for d in (1, 4):
    c = load(src); m = "STT_6_u_core_lpP_s2A"
    c["gem5"]["config_script"] = "/work/gem5-spt/configs/example/se_exp.py"; c["gem5"]["sample_fraction"] = RACE_FRAC; c["gem5"]["jobs"] = 12
    c["race_knobs"] = {"commitToIEWDelay": d, "applied_via": "env SIMSPECT_COMMIT_IEW_DELAY read by gem5-hooks/gem5-spt/se_exp.py",
                       "cross_model": "STT_6_u corpus run on SPT-Fence (SPT has no big corpus: DECIDE SPT-BOUND)"}
    rn = f"bc_race_sptfence_d{d}_{m}"
    c["paths"].update(testset_dir=TS, results_dir=f"{O}/results", results_name=rn)
    n = write(f"race_sptfence_d{d}_{m}.jsonc", c, src, f"paths (testset = the STT_6_u A corpus, CROSS-MODEL), gem5.config_script se_exp.py, "
              f"gem5.sample_fraction {RACE_FRAC}, gem5.jobs 12, race_knobs.commitToIEWDelay {d}")
    out.append(n); camps.append(dict(recipe="A", row=f"race_sptfence_d{d}", node="cafe2", kind="race", config=f"runconfigs/bigcorpus_20261115/{n}",
                                     model=m, results_name=rn))

(D / "campaigns.json").write_text(json.dumps(camps, indent=1) + "\n")
print("\n".join(out)); print(f"{len(camps)} campaigns -> {D}/campaigns.json")
