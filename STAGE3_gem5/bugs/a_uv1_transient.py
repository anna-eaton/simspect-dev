"""UV1_transient (InvisiSpec): an A-UV1 eviction whose evicting load never became visible (a squashed load).

Signature: an event that carries A-UV1 (a_uv1_invisispec.is_event, not padding) and whose actor's checker visibility point
is never (offending item vp[seq] = [inf, ...]). Reported next to UV1, never instead of it.
Evidence: cache-full session 2026-11-09; moved verbatim from classify_hits.py sigs_invisispec.
Verdict: sub-class of the known real bug A-UV1 (reported, not a separate bug).
"""
LABEL = "UV1_transient"
PAPER_LABEL = None
ALIASES = ["UV1 transient"]
DEFENSES = ["invisispec"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 11
NEEDS_GEM5 = True
FAMILY = "footprint_event"


def is_transient(e, vp) -> bool:
    v = vp.get(str(e.get("seq")))
    return isinstance(v, list) and bool(v) and v[0] == float("inf")
