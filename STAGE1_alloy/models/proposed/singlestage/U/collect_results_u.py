#!/usr/bin/env python3
"""collect_results_u.py -- assemble family U's RESULTS.json from the cafe2 run outputs (read-only on the runs).
singlestage-u agent, 2026-11-09. Run inside gem5_dev on cafe2 from /tests/singlestage_20261109:
  python3 models/U/collect_results_u.py > models/U/RESULTS.json
Per model: model file + sha256, base file + sha256, generator command (from the .als header; V0 = the base itself),
the LINT line and START/END lines of run_flat.log, every runs.jsonl row (seed, instances, verdict, secs), and the
census UNION + PAIRWISE_OVERLAP blocks (+ per-seed instance/distinct counts) from census.json."""
import hashlib, json, re
from pathlib import Path
W = Path("/tests/singlestage_20261109")
MODELS = [("V0", "base/STT_6_u"), ("V1", "STT_6_u_flat_n8_prod"), ("V2", "STT_6_u_flat_n8_prod_nospacer"),
          ("V3", "STT_6_u_flat_n8_leakrs_nospacer"), ("V0", "base/Recon_6_u"), ("V1", "Recon_6_u_flat_n8_prod"),
          ("V2", "Recon_6_u_flat_n8_prod_nospacer"), ("V3", "Recon_6_u_flat_n8_leakrs_nospacer")]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
res = {"family": "U", "agent": "singlestage-u", "date": "2026-11-09", "cafe2_workspace": str(W),
       "repo_dir": "STAGE1_alloy/models/proposed/singlestage/U/", "models": []}
for v, m in MODELS:
    f = W / "models/U" / f"{m}.als"; stem = Path(m).name; out = W / "out/U" / stem
    t = f.read_text(); e = {"variant": v, "model": stem, "cafe2_model": str(f), "model_sha256": sha(f), "cafe2_out": str(out)}
    if v == "V0":
        e.update(base_file=f"STAGE1_alloy/models/proposed/ultimate/{stem}.als", base_sha256=sha(f),
                 generator_command="none (V0 = the base model unchanged)")
    else:
        e["base_file"], e["base_sha256"] = re.search(r"// Base: (\S+)\s+sha256 (\w+)", t).groups()
        e["generator_command"] = re.search(r"//   (python3 \S*make_s15_model\.py[^\n]*)", t).group(1)
    e["scope"] = re.search(r"\}\s*(for [^\n]*Instruction[^\n]*)", t).group(1)
    log = (out / "run_flat.log").read_text() if (out / "run_flat.log").exists() else ""
    e["lint"] = next((l for l in log.splitlines() if " LINT " in l), None)
    e["run_flat_start_end"] = [l for l in log.splitlines() if " START " in l or l.endswith(" END")]
    e["errors_in_log"] = [l for l in log.splitlines() if "ERROR" in l or "REFUS" in l or "Traceback" in l]
    rj = out / "runs.jsonl"
    e["runs"] = [{k: r.get(k) for k in ("seed", "instances", "verdict", "secs")} for r in
                 (json.loads(l) for l in rj.read_text().splitlines() if l.strip())] if rj.exists() else []
    cj = out / "census.json"
    if cj.exists():
        c = json.loads(cj.read_text())
        e["census_cmd"] = (out / "census_cmd.txt").read_text().strip() if (out / "census_cmd.txt").exists() else None
        e["census_UNION"] = c["UNION"]; e["census_PAIRWISE_OVERLAP"] = c["PAIRWISE_OVERLAP"]
        e["census_per_seed"] = {Path(k).name: {"instances": x["instances"], "distinct": x["distinct"], "parse_errors": x.get("parse_errors")}
                                for k, x in c.items() if k not in ("UNION", "PAIRWISE_OVERLAP")}
    res["models"].append(e)
print(json.dumps(res, indent=1, ensure_ascii=False))
