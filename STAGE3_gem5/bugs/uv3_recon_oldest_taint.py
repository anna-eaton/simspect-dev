"""UV3 (ReCon): only the oldest taint source is kept. Internal label R-SA-8 (candidate), OTB / getOldestTaint.

Signature (bucket_eval): a ReCon br_x gated hit with a faithful GPR twin, whose twin run (status ok) also hits:
"R-SA-8 candidate (br_x twin hit; E2LT-2)". Per-test confirmation is a separate rerun (runconfigs/twostage_lp/
eval_20261110/rsa8_trace.py: the transmitter branch is released from the delay unit before the window branch's held
resolve fires, and resolves mispredicted before it); a record with that evidence has rsa8_signature true.
Caveat: in the traced tests the older operand comes from gem5's x86 mov false dependency (DECIDE E2LT-2).
Evidence: taint_tracker.cc:108-131 in ReCon; triage/diag/diag_recon_oldest_taint.md; paper 29/53,908.
Moved verbatim from runconfigs/twostage_lp/eval_20261110/bucket_eval.py (and rsa8_trace.py's verdict field).
Verdict: real gem5 defense bug, new (paper UV3); the bucket is a candidate class until rsa8_trace confirms a test.
"""
LABEL = "R-SA-8 candidate (br_x twin hit; E2LT-2)"
PAPER_LABEL = "UV3"
ALIASES = ["R-SA-8", "OTB", "getOldestTaint", "recon_oldest_taint"]
DEFENSES = ["recon"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 87
NEEDS_GEM5 = True
FAMILY = "recon_bucket"


def matches(kind, twin_hit) -> bool:
    return kind == "br_x" and bool(twin_hit)


def confirmed(rsa8_evidence) -> bool:
    """rsa8_trace.py per-key record -> True when the R-SA-8 release-order signature holds."""
    return bool(rsa8_evidence and rsa8_evidence.get("rsa8_signature"))
