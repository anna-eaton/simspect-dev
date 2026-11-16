"""EM_rmw / CS-EM (CleanupSpec): the E->M skip (cs_em_upgrade) caused by the test's OWN RMW transmitter.

Signature: an `EM_upgrade_squashed` item whose squashed E->M upgraders (_trace.rmw_em_upgraders: L1D hit st=E nst=M
req=st on the item's line or its events' fill lines, never committed) have exactly one pc, that pc == xmit_pc, and the
stem is an RMW stem.
Evidence: triage/diag/diag_cleanupspec_em.md; EVAL_MANIFEST footprint part 7 (own-RMW E->M 472). Moved verbatim from
STAGE3_gem5/timing/classify_cs_rmw.py refine().
Verdict: real gem5 defense bug, UV3 family (non-AMuLeT signature), reported separately; count-as-new is Anna's DECIDE.
"""
LABEL = "EM_rmw"
PAPER_LABEL = None
ALIASES = ["CS-EM", "EM_rmw"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "known_pending"
ORDER = 60
NEEDS_GEM5 = True
FAMILY = "cleanupspec_rmw_item"


def matches(pc, xpc, rmw) -> bool:
    return pc == xpc and bool(rmw)
