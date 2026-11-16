"""A-UV6 (SpecLFB): the first speculative load of a window is left unprotected. Internal tag `uv6_first`, label `UV6`.

Signature (per in-window load footprint event, SpecLFB tagger _speclfb.analyze): the event's actor is a squashed load
younger than lc_seq, its last LSQ:unsafe line says unsafe=0 (else unsafe1_filled / replayed_after_safe), and it has rank
0 in its squash group (the first speculative load of that window). Hit label `UV6` when any surviving cause has this tag
(after disq_speclfb_nonload and disq_hpad_text_end).
Evidence: lsq_unit.cc:877 (the walk starts one entry after the LQ head); triage/diag/diag_speclfb_uv6.md; EVAL_MANIFEST
footprint part 7 (861/4,000). Moved verbatim from STAGE3_gem5/timing/speclfb_analyze.py and classify_hits.py.
Verdict: real gem5 defense bug, known (AMuLeT A-UV6), replicated.
"""
LABEL = "UV6"
PAPER_LABEL = "A-UV6"
ALIASES = ["uv6_first"]
DEFENSES = ["speclfb"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 70
NEEDS_GEM5 = True
FAMILY = "speclfb_load"


def load_tag(L):
    return "uv6_first" if L["rank"] == 0 else None


def in_tags(tags) -> bool:
    return "uv6_first" in tags
