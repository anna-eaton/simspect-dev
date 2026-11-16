"""EM_upgrade (CleanupSpec): a squashed store / RMW upgrades a squashed load's E line to M, so its cleanup is skipped.

Signature (actor S never committed, not a split):
  victim item: the CS1 chain (cs1_older_store_upgrade) but the upgrader U never committed and U > Q (younger than the
  squashing branch: the speculative RMW transmitter);
  install item: under_clean fill of the line by S, exactly one `cleanup_skip line seq=S ev=Inv_CLEANUP st=M`, exactly one
  `L1D:hit line st=E nst=M` between S's fill and that skip, by a never-committed upgrader.
classify_hits.py label `EM_upgrade`; classify_cs_rmw refines it into EM_rmw (cs_em_rmw), EM_padding
(disq_hpad_rmw_padding) or EM_other (cs_em_other).
Evidence: URGENT_TODO DECIDE "CleanupSpec E->M case"; triage/diag/diag_cleanupspec_em.md (MESI_Two_Level-L1cache.sm:2294-2298,
2701-2705). Moved verbatim from STAGE3_gem5/timing/cleanupspec_skip_evidence.py judge().
Verdict: real gem5 defense bug, UV3 family (E->M path); count-as-new vs UV3 variant is Anna's DECIDE. Not a target.
"""
from ._trace import cs_actor, cs_is_victim_item, cs_is_install_item, cs_split_seqs, cs_victim_chain, cs_sel

LABEL = "EM_upgrade"
PAPER_LABEL = None
ALIASES = ["EM_upgrade_squashed", "CS-EM"]
DEFENSES = ["cleanupspec"]
PHASE = "real_bug"
VERDICT = "known_pending"
ORDER = 31
NEEDS_GEM5 = True
FAMILY = "cleanupspec_item"
CAUSE = "EM_upgrade_squashed"


def judge(item, tr):
    es, S, _ = cs_actor(item, tr)
    if es is None:
        return None
    evs, by_id, committed = tr
    line = item["line"]
    if cs_is_victim_item(item, es, S):
        if S in cs_split_seqs(evs):
            return None
        c = cs_victim_chain(item, es, S, tr)
        if c["ok"] and c["U"] is not None and c["U"] not in committed and c["U"] > c["Q"]:
            return c["chain"]
        return None
    if cs_is_install_item(item, es, S):
        if any(e["seqn"] == S and e.get("line") == line for e in cs_sel(evs, "L1D", "cleanup_skip", why="split")):
            return None
        e0 = es[0]
        sk = [e for e in cs_sel(evs, "L1D", "cleanup_skip", line=line, seq=str(S))
              if e.get("ev") == "Inv_CLEANUP" and e.get("st") == "M"]
        ups = [e for e in cs_sel(evs, "L1D", "hit", line=line, st="E", nst="M") if sk and e0["tick"] <= e["tick"] <= sk[0]["tick"]]
        if len(sk) == 1 and len(ups) == 1 and ups[0]["seqn"] not in committed:
            return f"S={S} fill {line}; squashed U={ups[0]['seqn']} st E->M @{ups[0]['tick']}; cleanup_skip st=M @{sk[0]['tick']}"
    return None
