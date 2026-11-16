"""CS1 (CleanupSpec): an older committed store upgrades a squashed load's E line to M, so its cleanup is skipped.

Signature (victim item; actor S never committed, not a split): S filled L and evicted V (the item's line); V not restored
by S; exactly one `L1D:cleanup_skip line=L seq=S ev=Inv_CLEANUP st=M`; exactly one `L1D:hit line=L st=E nst=M` between
S's fill and that skip, by U with req=st; the skip's squash seq Q is known with S > Q; and U < Q and U committed.
Evidence: SOURCE_AUDIT_CLEANUPSPEC_SPECLFB.md CS-1; MESI_Two_Level-L1cache.sm:2701-2705; triage/diag/diag_cs1_store_upgrade.md.
Moved verbatim from STAGE3_gem5/timing/cleanupspec_skip_evidence.py judge().
Verdict: known cause, verdict pending (URGENT_TODO DECIDE CS-1); reported separately, never a target.
"""
from ._trace import cs_actor, cs_is_victim_item, cs_split_seqs, cs_victim_chain

LABEL = "CS1"
PAPER_LABEL = None
ALIASES = ["CS1_older_store_upgrade", "CS-1"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "known_pending"
ORDER = 30
NEEDS_GEM5 = True
FAMILY = "cleanupspec_item"
CAUSE = "CS1_older_store_upgrade"


def judge(item, tr):
    es, S, _ = cs_actor(item, tr)
    if es is None or not cs_is_victim_item(item, es, S) or S in cs_split_seqs(tr[0]):
        return None
    c = cs_victim_chain(item, es, S, tr)
    if c["ok"] and c["U"] is not None and c["U"] < c["Q"] and c["U"] in tr[2]:
        return c["chain"]
    return None
