"""A-UV5 (CleanupSpec): cleanup invalidates a line that an older committed access used. Internal `UV5_older_load` / `UV5`.

Signature (over_clean item; actor S = first offending event's seq, every event id present, S never committed): S filled
the item's line, an older committed access U < S hits that line after the fill and before the cleanup, then
`L1D:cleanup_inv line=<line> seq=S`.
DG-3 (Anna, 2026-11-15, option (i)): the footprint checker's net-state replay used to call these lines "outside W" (S's
fill precedes lc_retire because U is the lc), which made every UV5 record `inconsistent`. classify.py now exempts
over_clean lines from that outside-window filter (_dg3.normalize), so the count rule and the replay agree; the hits stay.
Evidence: CleanupSpec §3.4 (lines used by older accesses must be kept); Sequencer.cc:1300-1346; EVAL_MANIFEST footprint
parts 7-8 (4/50,232; every hit reproduced). Moved verbatim from cleanupspec_skip_evidence.py judge().
Verdict: real gem5 defense bug, known (AMuLeT A-UV5), replicated.
"""
from ._trace import cs_actor, cs_sel

LABEL = "UV5"
PAPER_LABEL = "A-UV5"
ALIASES = ["UV5_older_load"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 40
NEEDS_GEM5 = True
FAMILY = "cleanupspec_item"
CAUSE = "UV5_older_load"


def judge(item, tr):
    es, S, _ = cs_actor(item, tr)
    if es is None or item["term"] != "over_clean":
        return None
    evs, by_id, committed = tr
    line = item["line"]
    fills = [e for e in es if e["kind"] == "fill" and e.get("line") == line and e["seqn"] == S]
    invs = cs_sel(evs, "L1D", "cleanup_inv", line=line, seq=str(S))
    if fills and invs:
        hits = [e for e in cs_sel(evs, "L1D", "hit", line=line)
                if fills[0]["tick"] <= e["tick"] <= invs[0]["tick"] and e["seqn"] is not None
                and e["seqn"] < S and e["seqn"] in committed]
        if hits:
            h = hits[0]
            return (f"S={S} fill {line} @{fills[0]['tick']}; older committed U={h['seqn']} "
                    f"req={h.get('req')} addr={h.get('addr')} size={h.get('size')} hits @{h['tick']}; "
                    f"cleanup_inv @{invs[0]['tick']}")
    return None
