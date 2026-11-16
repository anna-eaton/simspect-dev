"""A-UV1 (InvisiSpec): a speculative load evicts a live L1D line. Internal label `UV1`.

Signature: some in-window offending event (the footprint checker's `offending` event ids) is `L1D:evict` with
req=specld, and the event is not H-PAD padding (disq_hpad_text_end). Applied after the SETUP strip (disq_setup_block).
Evidence: AMULET_BUGS_DETECTION_ACCOUNTING.md §2 UV1 row; triage/diag/diag_invisispec_uv1.md (AMuLeT's
--apply-spec-eviction-patch removes the eviction); EVAL_MANIFEST footprint part 7 (complete run 2,002/4,000, all `full`).
Moved verbatim from STAGE3_gem5/timing/classify_hits.py sigs_invisispec.
Verdict: real gem5 defense bug, known (AMuLeT A-UV1), replicated.
"""
LABEL = "UV1"
PAPER_LABEL = "A-UV1"
ALIASES = ["UV1", "invisispec_uv1"]
DEFENSES = ["invisispec"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 10
NEEDS_GEM5 = True
FAMILY = "footprint_event"


def is_event(e) -> bool:
    return bool(e) and e["struct"] == "L1D" and e["kind"] == "evict" and e.get("req") == "specld"
