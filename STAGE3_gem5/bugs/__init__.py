"""STAGE3_gem5/bugs: one Python module per known hit cause, plus one orchestrator (classify.py).

Every cause module (any `*.py` here whose name does not start with `_` and is not `classify.py`) carries:
  LABEL        the label the orchestrator writes for this cause (exactly the label the old classifiers wrote)
  PAPER_LABEL  the ISCA-27 results.tex label (e.g. "A-UV4", "UV2"), or None
  ALIASES      internal names used in logs / older docs (e.g. ["A2", "recon_SLF_stlf_bypass"])
  DEFENSES     defenses whose runs this cause is checked on
  PHASE        "disqualifier" (the hit is not a real leak / not the test's own leak) or "real_bug" (a known cause:
               confirmed bug, known-pending bug, or a reported non-target class)
  VERDICT      "real_bug" | "known_pending" | "artifact" | "checker" (registry verdicts of specs/hit_categories.json)
  ORDER        apply order inside the phase (disqualifiers always run before real-bug modules)
  NEEDS_GEM5   True when deciding needs a gem5 trace or a gem5 rerun's evidence (not just the record / static files)
  FAMILY       which record family the decide function takes (footprint_event, cleanupspec_item, cleanupspec_rmw_item,
               speclfb_load, speclfb_tags, stt_record, recon_bucket, race_record)
  one decide function, documented in the module docstring (signature, evidence pointer, verdict).

The registry of all modules is specs/hit_categories.json (one entry per module, key = module name).
Docs: wiki/findings/bug/BUGS.md "Bug scripts (STAGE3_gem5/bugs/)"; command: wiki/state/COMMANDS.md.
"""
import importlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PHASE_RANK = {"disqualifier": 0, "real_bug": 1}


def module_names():
    return sorted(p.stem for p in HERE.glob("*.py")
                  if not p.stem.startswith("_") and p.stem != "classify")


def load_all():
    """-> [module] in apply order (disqualifiers first, then real_bug, each by ORDER)."""
    mods = [importlib.import_module(f"{__name__}.{n}") for n in module_names()]
    return sorted(mods, key=lambda m: (_PHASE_RANK.get(m.PHASE, 9), m.ORDER, m.__name__))
