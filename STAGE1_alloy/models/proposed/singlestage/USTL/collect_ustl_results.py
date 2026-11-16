#!/usr/bin/env python3
"""collect_ustl_results.py — read-only: gather the USTL run outputs on cafe2 into one JSON (stdout) that is saved
as USTL/RESULTS.json (agent singlestage-ustl, 2026-11-09). Run from /tests/singlestage_20261109 inside gem5_dev."""
import hashlib, json, re
from pathlib import Path
W = Path("/tests/singlestage_20261109")
MODELS = [("V0 n6_prod", "base/STT_6_u_stl.als"), ("V1", "STT_6_u_stl_flat_n8_prod.als"),
          ("V2", "STT_6_u_stl_flat_n8_prod_nospacer.als"), ("V3", "STT_6_u_stl_flat_n8_leakrs_nospacer.als"),
          ("V0 n6_prod", "base/Recon_6_u_stl.als"), ("V1", "Recon_6_u_stl_flat_n8_prod.als"),
          ("V2", "Recon_6_u_stl_flat_n8_prod_nospacer.als"), ("V3", "Recon_6_u_stl_flat_n8_leakrs_nospacer.als")]
res = {"family": "USTL", "generated_by": "models/USTL/collect_ustl_results.py", "cafe2_workspace": str(W), "models": []}
for var, rel in MODELS:
    m = W / "models/USTL" / rel; stem = m.stem; out = W / "out/USTL" / stem
    t = m.read_text() if m.exists() else ""
    g = re.search(r"^// Generator \(unchanged shared tool\): (.*)$", t, re.M)
    b = re.search(r"^// Base: (\S+)\s+sha256 (\w+)", t, re.M)
    e = {"variant": var, "model": str(m), "model_sha256": hashlib.sha256(t.encode()).hexdigest() if t else None,
         "base_file": b.group(1) if b else f"STAGE1_alloy/models/proposed/ultimate/{m.name}",
         "base_sha256": b.group(2) if b else (hashlib.sha256(t.encode()).hexdigest() if t else None),
         "generator_command": g.group(1) if g else "none (V0 = base model unchanged)", "out_dir": str(out)}
    log = out / "run_flat.log"
    if log.exists():
        L = log.read_text().splitlines()
        e["lint"] = next((l.split(" ", 1)[1] for l in L if " LINT " in l), None)
        e["run_finished"] = bool(L) and L[-1].endswith(" END")
    rj = out / "runs.jsonl"
    e["runs"] = [{k: r.get(k) for k in ("seed", "instances", "verdict", "secs")} for r in map(json.loads, rj.read_text().splitlines())] if rj.exists() else []
    for key, fn in (("census", "census.json"), ("store_hist", "store_hist.json")):
        p = out / fn
        if p.exists():
            c = json.loads(p.read_text())
            e[key] = {k: c[k] for k in ("UNION", "PAIRWISE_OVERLAP") if k in c}
            e[key]["per_run_dir"] = {Path(k).name: {kk: v.get(kk) for kk in ("instances", "distinct", "parse_errors")} for k, v in c.items() if k not in ("UNION", "PAIRWISE_OVERLAP")}
            e[key + "_path"] = str(p)
    res["models"].append(e)
print(json.dumps(res, indent=1, ensure_ascii=False))
