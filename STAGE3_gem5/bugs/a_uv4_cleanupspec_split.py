"""A-UV4 (CleanupSpec): a line-crossing (split) squashed access is not cleaned. Internal labels `UV4_split` / `UV4`.

Signature (per offending item; actor S = the first offending event's seq, every event id present, S never committed):
  victim item: under_clean, every event an evict of the item's line by S, and the trace has `L1D:cleanup_skip seq=S
  why=split`;  install item: under_clean, every event a fill of the item's line by S, and a `cleanup_skip why=split` with
  seq=S and line=<item line>.
Evidence: lsq_unit_impl.hh:2529-2535; triage/diag/diag_uv4_split.md; EVAL_MANIFEST footprint part 7 (599/50,232).
Moved verbatim from STAGE3_gem5/timing/cleanupspec_skip_evidence.py judge().
Verdict: real gem5 defense bug, known (AMuLeT A-UV4), replicated.
"""
from ._trace import cs_actor, cs_is_victim_item, cs_is_install_item, cs_split_seqs, cs_sel

LABEL = "UV4"
PAPER_LABEL = "A-UV4"
ALIASES = ["UV4_split", "uv4_split"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 20
NEEDS_GEM5 = True
FAMILY = "cleanupspec_item"
CAUSE = "UV4_split"


def judge(item, tr):
    """-> why (str) when this cause explains the item, else None."""
    es, S, _ = cs_actor(item, tr)
    if es is None:
        return None
    evs = tr[0]
    line = item["line"]
    if cs_is_victim_item(item, es, S):
        if S in cs_split_seqs(evs):
            return f"S={S} filled {es[0].get('line')} evicting V={line}; cleanup_skip seq={S} why=split"
        return None
    if cs_is_install_item(item, es, S):
        if any(e["seqn"] == S and e.get("line") == line for e in cs_sel(evs, "L1D", "cleanup_skip", why="split")):
            return f"S={S} fill {item['struct']} {line}; cleanup_skip line={line} seq={S} why=split"
    return None
