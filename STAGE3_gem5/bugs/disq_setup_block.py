"""SETUP exclusion: an offending event that belongs to the harness's own cache-setup block, not to the test.

Signature: the record ran with cache_setup `full` and an offending event's actor PC (event pc, else its seq's pipeview pc)
lies inside the setup block [cache_setup_info.begin, begin + delta). That block is the harness's L1D sweep (committed
plain loads; with no lc instruction the window starts at tick 0, and on InvisiSpec-Futuristic those loads issue as
speculative loads whose evictions look like UV1). Such events are removed from the record's offending items before any
rule runs; a target signature carried only by them becomes `excluded_SETUP:<sig>`, and a hit with no other offending
event is `excluded_SETUP:no_test_event`. Not applied to warm/cold/random records.
Evidence: cache-full session 2026-11-09 (EVAL_MANIFEST "Cache setup `full`"); moved verbatim from
STAGE3_gem5/timing/classify_hits.py strip_setup / with_setup_exclusion.
Verdict: harness artifact (exclusion; only lowers counts).
"""
from ._trace import ev_pc

LABEL = "excluded_SETUP"
PAPER_LABEL = None
ALIASES = ["SETUP", "cache-full setup block"]
DEFENSES = ["invisispec", "cleanupspec", "speclfb"]
PHASE = "disqualifier"
VERDICT = "artifact"
ORDER = 10
NEEDS_GEM5 = True
FAMILY = "footprint_event"


def strip(raw, pv, gc):
    """-> (raw with setup-block events removed from `offending`, n events removed)."""
    info = raw.get("cache_setup_info") or {}
    if raw.get("cache_setup") != "full" or "begin" not in info:
        return raw, 0
    b = int(info["begin"], 16)
    e_ = b + int(info["delta"])
    evs = {x["id"]: x for x in gc.parse_simspect_events(pv)}
    byseq = gc.parse_pipeview_by_seq(pv)

    def in_setup(i):
        x = evs.get(i)
        pc = ev_pc(x, byseq) if x else None
        return pc is not None and b <= pc < e_

    new = dict(raw)
    items, removed = [], 0
    for o in raw.get("offending") or []:
        ids = o.get("event_ids") or []
        keep = [i for i in ids if not in_setup(i)]
        removed += len(ids) - len(keep)
        if not keep and ids:
            continue
        o2 = dict(o, event_ids=keep)
        kseq = set()
        for i in keep:
            try:
                kseq.add(int(evs[i].get("seq")))
            except (KeyError, TypeError, ValueError):
                kseq = None
                break
        if kseq is not None and len(keep) < len(ids):
            o2["seqs"] = [q for q in o.get("seqs") or [] if q in kseq]
            if isinstance(o.get("vp"), dict):
                o2["vp"] = {k: v for k, v in o["vp"].items() if str(k).isdigit() and int(k) in kseq}
        items.append(o2)
    new["offending"] = items
    return new, removed


def with_exclusion(fn, raw, pv, gc, targets):
    """Run signature function fn(raw') on the setup-stripped record; tag targets lost to the strip."""
    raw2, n = strip(raw, pv, gc)
    if not n:
        return fn(raw)
    if not raw2["offending"]:
        lost = {x for x in fn(raw) if x in targets}
        return {"excluded_SETUP:no_test_event"} | {f"excluded_SETUP:{x}" for x in lost}
    got = fn(raw2)
    lost = {x for x in fn(raw) if x in targets} - got
    return got | {f"excluded_SETUP:{x}" for x in lost}
