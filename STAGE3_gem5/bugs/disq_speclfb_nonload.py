"""SpecLFB non-load footprint: an in-window footprint event whose request is not a load is not a SpecLFB leak.

Signature: of the SpecLFB tagger's in-window footprint causes, keep only those whose event req is `ld`; the rest (ifetch,
store, writeback) are dropped before any SpecLFB tag counts. A hit left with no cause is
`other:disq_non_load_footprint`. SpecLFB protects speculative loads only.
Evidence: triage.py disqualifier of the 2026-11-07 SpecLFB v2 session; triage/diag/diag_speclfb_nonload_footprint.md;
moved verbatim from classify_hits.py sigs_speclfb (`good = [c ... if c["ev"].get("req") in ("ld",)]`).
Verdict: out of scope of the defense (disqualifier).
"""
LABEL = "other:disq_non_load_footprint"
PAPER_LABEL = None
ALIASES = ["speclfb_nonload_footprint"]
DEFENSES = ["speclfb"]
PHASE = "disqualifier"
VERDICT = "artifact"
ORDER = 30
NEEDS_GEM5 = True
FAMILY = "speclfb_tags"


def is_load_cause(c) -> bool:
    return c["ev"].get("req") in ("ld",)
