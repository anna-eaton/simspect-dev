"""UV3 (ReCon): only the oldest taint source is kept. Internal label R-SA-8 (candidate), OTB / getOldestTaint.

Signature (bucket_eval): a ReCon br_x gated hit with a faithful GPR twin, whose twin run (status ok) also hits:
"R-SA-8 candidate (br_x twin hit; E2LT-2)". Per-test confirmation is a separate rerun (runconfigs/twostage_lp/
eval_20261110/rsa8_trace.py: the transmitter branch is released from the delay unit before the window branch's held
resolve fires, and resolves mispredicted before it); a record with that evidence has rsa8_signature true.
Caveat: in the traced tests the older operand comes from gem5's x86 mov false dependency (DECIDE E2LT-2).
Store-shadow confirmation (rstltriage, 2026-11-16; E2w-stl): rsa8_trace needs a held branch, which store-shadow tests lack,
so STAGE3_gem5/triage/oldest_taint_replay.py replays gem5's taint tracker offline over a faithful Rename/Commit/DelayUnit
rerun (insert counts must equal stats.txt insertedTaints/insertedTaintInsts, no reveal) under gem5's oldest-source rule and
under a keep-all-sources counterfactual. Confirmed (LABEL_STL) when the transmitter (br_x, ld or RMW) is untainted / released
under the oldest rule exactly when an older load O's taint dies, while the counterfactual still holds the annotated bypass
load L (speculative until the store's stl_release) and the signal precedes stl_release. Shape A: X in the delay unit,
released one cycle after O's taint died; shape B: X never in the delay unit (O already dead when STT first judged X; DECIDE
RL-12). The merge instruction and how O entered it (gem5 flags read, a pure move reading its old destination, or a real data
operand) are in the evidence; scope: ReCon scheme 2 store-shadow rows (needs that evidence; others keep LABEL).
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


LABEL_STL = "R-SA-8 confirmed (store shadow; oldest-source taint replay)"


def confirmed_stl(replay_evidence) -> bool:
    """oldest_taint_replay.py record -> True when shape A or shape B holds (every check passed)."""
    return bool(replay_evidence) and str(replay_evidence.get("verdict", "")).startswith("R-SA-8 shape")


def confirmed(rsa8_evidence) -> bool:
    """rsa8_trace.py per-key record -> True when the R-SA-8 release-order signature holds."""
    return bool(rsa8_evidence and rsa8_evidence.get("rsa8_signature"))
