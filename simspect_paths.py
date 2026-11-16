#!/usr/bin/env python3
"""
simspect_paths.py — canonical filesystem locations for the SimSpect pipeline.

pipeline.py, testsetgen.py, testrun.py, sweep_monitor.py and dashboard.py import ROOT and the canonical dirs from
here. ROOT self-locates via __file__, so the same code works on any checkout. Run configs may override the
generated dirs via paths.{testset_dir,results_dir,results_name,...}; these constants are the defaults and the
locations the dashboard reads.
"""
from __future__ import annotations
from pathlib import Path

# Repo root = the directory this file lives in.
ROOT = Path(__file__).parent.resolve()

# ── Canonical source dirs (committed) ─────────────────────────────────────────
ALLOY_STAGE        = ROOT / "STAGE1_alloy"
MODELS_DIR         = ALLOY_STAGE / "models"
STAGE2_DIR         = ROOT / "STAGE2_compilation"
STAGE3_DIR         = ROOT / "STAGE3_gem5"
RUNCONFIGS         = ROOT / "runconfigs"
INSTRUCTION_TABLES = STAGE2_DIR / "instruction_tables" / "instructions.jsonc"

# ── Canonical generated dirs (gitignored) ─────────────────────────────────────
# The CORPUS lives under TESTSETS/<model>/:
#   xml/                     base corpus produced by the Generation (Alloy) phase
#   <mode>/{llvm,asm,ann}/   post-fanout, concretized + annotated corpus
TESTSETS = ROOT / "testsets"
# gem5 CAMPAIGNS: RESULTS/<results_name>__<ts>/<mode>/<kind>/
RESULTS  = ROOT / "results"

# ── Canonical jobs registry (gitignored) ──────────────────────────────────────
# Append-only manifest of every launched run (producer + consumer). See
# jobs_registry.py for the record schema and the reader.
JOBS_DIR      = ROOT / "jobs"
JOBS_MANIFEST = JOBS_DIR / "manifest.jsonl"
JOBS_LOGS     = JOBS_DIR / "logs"


def resolve(cfg_value, base: Path = ROOT) -> Path:
    """Resolve a config path value: absolute → as-is; relative → under base (ROOT)."""
    p = Path(cfg_value)
    return p if p.is_absolute() else (base / p).resolve()
