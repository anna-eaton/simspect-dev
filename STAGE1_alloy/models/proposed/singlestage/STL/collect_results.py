#!/usr/bin/env python3
"""collect_results.py — read-only: assemble RESULTS.json for the STL family from the cafe2 outputs (singlestage-stl, 2026-11-09).
Run on cafe2 from /tests/singlestage_20261109:  python3 models/STL/collect_results.py > RESULTS.json"""
import json, re
from pathlib import Path
G = "python3 STAGE1_alloy/models/proposed_twophase/stage15_bound/make_s15_model.py --model {b} --pin none --n 8 --operands 16 --intbits 6{x} --out STAGE1_alloy/models/proposed/singlestage/STL/{m}.als"
BASES = {"STT_6_stl": "STAGE1_alloy/models/STT_6_stl.als", "Recon_6_stl": "STAGE1_alloy/models/proposed/Recon_6_stl.als"}
VARS = [("V0", "", None), ("V1", "_flat_n8_prod", ""), ("V2", "_flat_n8_prod_nospacer", " --shape nospacer"),
        ("V3", "_flat_n8_leakrs_nospacer", " --shape nospacer --minimality leak_rs")]
CORES = {"STT_6_stl": "/tests/simspect_alloy_20261108/out/STT_6_stl_core (306 cores, all 3 instructions, k3/stage1_xml)",
         "Recon_6_stl": "/tests/simspect_alloy_20261108/out/Recon_6_stl_core (858 cores, all 3 instructions, k3/stage1_xml)"}
W = Path("/tests/singlestage_20261109")
out = {"family": "STL", "agent": "singlestage-stl", "date": "2026-11-09", "status": "UNAPPROVED DRAFTS",
       "cafe2_workspace": str(W), "models": {}}
for base, bpath in BASES.items():
    for v, suf, x in VARS:
        m = base + suf; o = W / "out/STL" / m
        log = (o / "run_flat.log").read_text() if (o / "run_flat.log").exists() else ""
        st = re.search(r"START .*?sha256=(\w+)", log)
        rec = {"variant": v, "base_file": bpath, "model_file": bpath if v == "V0" else f"STAGE1_alloy/models/proposed/singlestage/STL/{m}.als",
               "cafe2_model": str(W / "models/STL" / ("base/" + base if v == "V0" else m)) + ".als",
               "model_sha256": st.group(1) if st else None,
               "generator_command": None if v == "V0" else G.format(b=bpath, m=m, x=x),
               "lint": next((l.split(" LINT ", 1)[1] for l in log.splitlines() if " LINT " in l), None),
               "cafe2_out": str(o),
               "runs": [{k: r[k] for k in ("seed", "instances", "verdict", "secs")} for r in map(json.loads, (o / "runs.jsonl").read_text().splitlines())] if (o / "runs.jsonl").exists() else []}
        if v == "V0": rec["cores"] = CORES[base]
        for name in ("census.json", "census_cores_default_1.json", "stl_store_census.json"):
            if (o / name).exists():
                c = json.loads((o / name).read_text())
                rec[name.replace(".json", "")] = {k: c[k] for k in ("UNION", "PAIRWISE_OVERLAP") if k in c}
        out["models"][m] = rec
print(json.dumps(out, indent=1, ensure_ascii=False))
