#!/usr/bin/env python3
"""collect_results.py -- assemble SPTU/RESULTS.json from the cafe2 outputs (singlestage-sptu agent, 2026-11-09).
Read-only on the run dirs. Run inside gem5_dev on cafe2:
  python3 collect_results.py /tests/singlestage_20261109 > RESULTS.json
Per model: base + sha256, generator command (from the .als header), lint line + scope (run_flat.log), runs.jsonl rows,
census UNION + PAIRWISE_OVERLAP (+ per-run blocks) from every census*.json in the out dir, the translation-timing
timelines under out/SPTU/_timing, and the SPT fixpoint-depth check (spt_depth*.txt) if present."""
import hashlib, json, re, sys
from pathlib import Path
W = Path(sys.argv[1]); OUT = W / "out/SPTU"; MOD = W / "models/SPTU"
BASE = "STAGE1_alloy/models/proposed/ultimate/SPT_6_u.als"
models = {"V0 n6_prod (base, unchanged)": MOD / "base/SPT_6_u.als",
          "V1": MOD / "SPT_6_u_flat_n8_prod.als",
          "V2": MOD / "SPT_6_u_flat_n8_prod_nospacer.als",
          "V3": MOD / "SPT_6_u_flat_n8_leakrs_nospacer.als"}
res = {"family": "SPTU", "agent": "singlestage-sptu", "date": "2026-11-09",
       "base": BASE, "base_sha256": hashlib.sha256((MOD / "base/SPT_6_u.als").read_bytes()).hexdigest(),
       "cafe2_workspace": str(W), "models": {}}
for var, m in models.items():
    if not m.exists(): continue
    t = m.read_text(); d = OUT / m.stem; r = {"model_cafe2": str(m), "sha256": hashlib.sha256(t.encode()).hexdigest(), "out_cafe2": str(d)}
    g = re.search(r"^// generator: (.*)$", t, re.M); r["generator_command"] = g.group(1) if g else "none (base model run unchanged)"
    log = d / "run_flat.log"
    if log.exists():
        L = log.read_text().splitlines()
        r["lint"] = next((l.split(" LINT ", 1)[1] for l in L if " LINT " in l), None)
        r["start"] = next((l for l in L if " START " in l), None)
        r["ended"] = any(l.endswith(" END") for l in L)
    rj = d / "runs.jsonl"
    r["runs"] = [{k: v for k, v in json.loads(l).items() if k in ("seed", "instances", "verdict", "secs", "rc", "ended")}
                 for l in rj.read_text().splitlines() if l.strip()] if rj.exists() else []
    for c in sorted(d.glob("census*.json")):
        C = json.loads(c.read_text())
        r[c.stem] = {"path": str(c), "UNION": C.get("UNION"), "PAIRWISE_OVERLAP": C.get("PAIRWISE_OVERLAP"),
                     "per_run": {Path(k).name: v for k, v in C.items() if k not in ("UNION", "PAIRWISE_OVERLAP")}}
    for s in sorted(d.glob("spt_depth*.txt")):
        r[s.stem] = s.read_text().splitlines()[-30:]
    res["models"][var] = r
res["translation_timing"] = {p.parent.name: p.read_text().splitlines() for p in sorted((OUT / "_timing").glob("*/timeline.txt"))}
smp = OUT / "cores_sample300/SAMPLE_LIST.txt"
if smp.exists(): res["core_sample"] = {"path": str(smp.parent), "how": smp.read_text().splitlines()[0],
                                        "note": "300-core RANDOM SAMPLE of the 58,758 SPT_6_u_core_ri cores (7 of 12 partitions ended DISK_GUARD, so the core set itself is partial); 'contains no core' against it is NOT evidence of a gap"}
print(json.dumps(res, indent=1, ensure_ascii=False))
