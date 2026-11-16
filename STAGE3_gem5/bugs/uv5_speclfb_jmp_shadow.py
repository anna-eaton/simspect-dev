"""UV5 (SpecLFB): the shadow of a direct jmp / call erases an older branch's shadow. Internal tag `jmp_shadow`.

Signature (per in-window load footprint event, _speclfb.analyze): actor load with unsafe=0 at its last translation, rank
>= 1, never CUSL/mUSL at its first translation, and a direct JMP_I / CALL_NEAR_I between the squashing branch and it
(why_safe contains direct_jmp_call_in_shadow); tag "jmp_shadow", plus "+walk_order" when prevnounsafe=1 as well. Hit
label `jmp_shadow` when any surviving cause's tag starts with "jmp_shadow".
Evidence: rob.cc ROB::updateSafeState resets prevBrsResolved=true at a direct unconditional control op (rob.cc:501 in the
SpecLFB artifact); wiki/findings/bug/speclfb_jmp_shadow/; EVAL_MANIFEST footprint part 7 (555/4,000).
Moved verbatim from STAGE3_gem5/timing/speclfb_analyze.py and classify_hits.py.
Verdict: real gem5 defense bug, new (paper UV5).
"""
LABEL = "jmp_shadow"
PAPER_LABEL = "UV5"
ALIASES = ["jmp_shadow", "speclfb_jmp_shadow"]
DEFENSES = ["speclfb"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 72
NEEDS_GEM5 = True
FAMILY = "speclfb_load"


def load_tag(L):
    if "direct_jmp_call_in_shadow" in L["why_safe"]:
        return "jmp_shadow" + ("+walk_order" if "prevnounsafe" in L["why_safe"] else "")
    return None


def in_tags(tags) -> bool:
    return any(t.startswith("jmp_shadow") for t in tags)
