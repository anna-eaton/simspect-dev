"""UV4 (SpecLFB): ROB walk order unprotects later loads. Internal tag `walk_order`.

Signature (per in-window load footprint event, _speclfb.analyze): actor load with unsafe=0 at its last translation, rank
>= 1, not jmp_shadow, and prevnounsafe=1 at its first translation (the sticky ROB-walk flag). Hit label `walk_order`
when any surviving cause's tag is or contains "walk_order" (so jmp_shadow+walk_order also counts here).
Evidence: the ROB walk marks a younger load one cycle before the LSQ walk flags the older one; triage/diag/
diag_speclfb_walk_order.md; EVAL_MANIFEST footprint part 7 (walk_order 666 in the first 4,000).
Moved verbatim from STAGE3_gem5/timing/speclfb_analyze.py and classify_hits.py.
Verdict: real gem5 defense bug, new (paper UV4).
"""
LABEL = "walk_order"
PAPER_LABEL = "UV4"
ALIASES = ["walk_order", "speclfb_walk_order"]
DEFENSES = ["speclfb"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 74
NEEDS_GEM5 = True
FAMILY = "speclfb_load"


def load_tag(L):
    return "walk_order" if L["first"]["prevnounsafe"] == 1 else None


def in_tags(tags) -> bool:
    return "walk_order" in tags or any("walk_order" in t for t in tags)
