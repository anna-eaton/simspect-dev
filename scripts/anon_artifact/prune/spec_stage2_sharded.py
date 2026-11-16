"""Prune ops for STAGE1_alloy/gen/stage2_sharded.py: every Stage-2 option is always passed (recipe A), no
store-separation variant, no '--kind' no-op, and a single tier (every caller passed --first-fraction 0)."""
OPS = [
    ("text", '''    cmd = [sys.executable, str(stage2 / "batch_generate.py"), str(xml_dir), "--out", str(llvm_dir),
           "--kind", "--instruction-tables", str(tables), "--mode", mode]
    il = cfg.get("interleave", {})
    if il:
        cmd += ["--interleave-config", json.dumps(il)]
    if cfg.get("fpr", {}).get("enabled"):
        cmd += ["--fpr-config", json.dumps(cfg["fpr"])]
    if cfg.get("reg_naming"):
        cmd += ["--reg-naming-config", json.dumps(cfg["reg_naming"])]
    if cfg.get("fanout_v2", {}).get("enabled"):
        cmd += ["--fanout-v2-config", json.dumps(cfg["fanout_v2"])]
    if cfg.get("store_separation", {}).get("enabled"):
        cmd += ["--store-separation-config", json.dumps(cfg["store_separation"])]
    if cfg.get("branch_cond", {}).get("from_alloy"):
        cmd += ["--branch-cond-config", json.dumps(cfg["branch_cond"])]
    return cmd''', '''    return [sys.executable, str(stage2 / "batch_generate.py"), str(xml_dir), "--out", str(llvm_dir),
            "--instruction-tables", str(tables), "--mode", mode,
            "--interleave-config", json.dumps(cfg.get("interleave", {})),
            "--fpr-config", json.dumps(cfg["fpr"]),
            "--reg-naming-config", json.dumps(cfg["reg_naming"]),
            "--fanout-v2-config", json.dumps(cfg["fanout_v2"]),
            "--branch-cond-config", json.dumps(cfg["branch_cond"])]''', 1),
    ("text", '    ap.add_argument("--first-fraction", type=float, default=0.02)\n', "", 1),
    ("text", '''    first = [x for x in xmls if sample_keep(x.stem, a.first_fraction)]
    rest = [x for x in xmls if not sample_keep(x.stem, a.first_fraction)]
''', "", 1),
    ("text", 'f"first_tier={len(first)} (fraction {a.first_fraction}) jobs={a.jobs} modes={modes}")', 'f"jobs={a.jobs} modes={modes}")', 1),
    ("text", '    for tier_name, tier in (("first", first), ("rest", rest)):\n', '    for tier_name, tier in (("all", xmls),):\n', 1),
    ("text", "from gem5_common import sample_keep\n", "", 1),
]
