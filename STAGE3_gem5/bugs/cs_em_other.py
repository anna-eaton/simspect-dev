"""EM_other (CleanupSpec): the E->M skip (cs_em_upgrade) by an upgrader that is neither the test's RMW nor the padding.

Signature: an `EM_upgrade_squashed` item where the squashed upgraders have != 1 distinct pc, or one pc that is neither the
RMW transmitter (cs_em_rmw) nor the H-PAD padding RMW (disq_hpad_rmw_padding).
Moved verbatim from STAGE3_gem5/timing/classify_cs_rmw.py refine().
Verdict: reported class; not a target.
"""
LABEL = "EM_other"
PAPER_LABEL = None
ALIASES = []
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "known_pending"
ORDER = 62
NEEDS_GEM5 = True
FAMILY = "cleanupspec_rmw_item"


def matches(pc, xpc, rmw) -> bool:
    """Residual of the EM chain (refine() order: EM_rmw, EM_padding, then this)."""
    return True
