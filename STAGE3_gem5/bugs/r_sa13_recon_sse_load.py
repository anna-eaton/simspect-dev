"""R-SA-13 (ReCon): the transmitter's taint is lost through an SSE load producer (FP routing). Labels below.

Static half (eval_gate class, triage/diag/diag_recon_sse_load_producer.py): the transmitter slice ends at a direct SSE load
(`sl["sse_producer"]`) -> "R-SA-13_static(SSE-load producer)"; else "other(xmm on slice)" if the slice has xmm registers,
else "other(GPR slice)".
Bucket rules (bucket_eval chain, ReCon plain tests):
  twin held + static class R-SA-13 -> "R-SA-13"; twin held + other class -> "R-SA-13 via FP elsewhere (twin held;
  e2-losttaint idiv-divisor case)";
  no faithful twin + static class R-SA-13 (and not A2) -> "R-SA-13 (static only[, RMW])";
  no faithful twin + main-run STL_CHECK isTainted=0 -> "untainted transmitter, no twin (R-SA-13 candidate[, RMW])".
Evidence: e2-losttaint verdicts; EVAL_MANIFEST "STT / ReCon eval rows" (E2/E6 buckets). Moved verbatim from
runconfigs/twostage_lp/eval_20261110/{eval_gate,bucket_eval}.py.
Verdict: real gem5 defense behaviour (ReCon loses taint through FP/SSE routing); not a paper bug.
"""
LABEL = "R-SA-13"
PAPER_LABEL = None
ALIASES = ["R-SA-13", "recon_sse_load_producer", "e2-losttaint"]
DEFENSES = ["recon"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 90
NEEDS_GEM5 = False
FAMILY = "recon_bucket"


def gate_class(sl) -> str:
    """Static class of a gated ReCon hit (sl without 'err')."""
    return ("R-SA-13_static(SSE-load producer)" if sl.get("sse_producer")
            else "other(xmm on slice)" if sl.get("xmms") else "other(GPR slice)")


def is_static(cl) -> bool:
    return cl.startswith("R-SA-13")


def untainted(e) -> bool:
    return e is not None and "isTainted=0" in (e.get("stl") or "")
