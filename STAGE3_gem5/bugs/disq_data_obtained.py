"""check_ld data-obtained gate: an in-window ld transmitter that never obtained its data is not a leak.

Signature: the raw checker record has `data_obtained == False` (check_ld._xmit_cache_fate + pipeview complete:
never_executed, spec_read_only, or executed_no_packet that never completed = delay-unit bounce). Label
`disq_not_obtained(<cache_fate>)`. `data_obtained` None (br_x, or no LSQ record) stays ungated, so a possible leak is never
hidden. On STT builds this is also how the RMW `never_executed` hits are removed.
Evidence: CLAUDE.md "Leak criteria" (the canonical gate); moved verbatim from classify_hits.py (STT path) and
runconfigs/twostage_lp/eval_20261110/eval_gate.py.
Verdict: checker false positive (disqualifier).
"""
LABEL = "disq_not_obtained"
PAPER_LABEL = None
ALIASES = ["data-obtained gate", "check_ld cache-reach FP"]
DEFENSES = ["stt", "recon"]
PHASE = "disqualifier"
VERDICT = "checker"
ORDER = 1
NEEDS_GEM5 = False
FAMILY = "stt_record"


def label(raw):
    """-> 'disq_not_obtained(<cache_fate>)' when the gate disqualifies the record, else None."""
    if raw.get("data_obtained") is False:
        return f"disq_not_obtained({raw.get('cache_fate')})"
    return None
