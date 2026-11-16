"""A-UV3 (CleanupSpec): a speculative read-modify-write's line is not cleaned. Internal label `UV3`.

Signature (per offending item the CleanupSpec item rules left `unattributed`; _trace.rmw_uv3_chain): under_clean item,
every offending event a fill with req=st (L1D msg=ST / L2 msg=GETX) of the item's line by one actor seq S with one pc,
the trace has `L1D:cleanup_skip line=<line> seq=S why=nohitinfo`, S never retired; and (this module) S's pc == the
record's xmit_pc and the stem is an RMW stem (rmw_stems.tsv). Same event rule as triage/uv3_rmw_evidence.py judge().
The same chain by the harness padding RMW is UV3_padding (disq_hpad_rmw_padding), by anything else UV3_other_actor.
Evidence: triage/diag/diag_uv3_rmw.md; EVAL_MANIFEST footprint part 7 (1,861/50,232, cold 1,770 / full 91).
Moved verbatim from STAGE3_gem5/timing/classify_cs_rmw.py refine().
Verdict: real gem5 defense bug, known (AMuLeT A-UV3), replicated (Anna 2026-11-09: counts as found).
"""
LABEL = "UV3"
PAPER_LABEL = "A-UV3"
ALIASES = ["uv3_rmw"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 50
NEEDS_GEM5 = True
FAMILY = "cleanupspec_rmw_item"


def matches(pc, xpc, rmw) -> bool:
    return pc == xpc and bool(rmw)
