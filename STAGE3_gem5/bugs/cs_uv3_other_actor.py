"""UV3_other_actor (CleanupSpec): the A-UV3 event chain, but by an actor that is neither the test's RMW transmitter nor
the harness padding RMW.

Signature: _trace.rmw_uv3_chain holds, a_uv3_cleanupspec_rmw does not match (pc != xmit_pc or not an RMW stem) and
disq_hpad_rmw_padding does not match. Reported, not credited to UV3.
Evidence / moved verbatim from: STAGE3_gem5/timing/classify_cs_rmw.py refine().
Verdict: reported class (UV3 mechanism by another write-request actor); not a target.
"""
LABEL = "UV3_other_actor"
PAPER_LABEL = None
ALIASES = []
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "known_pending"
ORDER = 52
NEEDS_GEM5 = True
FAMILY = "cleanupspec_rmw_item"


def matches(pc, xpc, rmw) -> bool:
    """Residual of the UV3 chain: always true once UV3 and UV3_padding were ruled out (refine() order)."""
    return True
