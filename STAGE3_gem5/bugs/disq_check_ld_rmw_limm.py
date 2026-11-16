"""check_ld RMW artifact (RL-10): check_ld scores the RMW's leading limm micro-op; ReCon's delay unit holds the load.

Signature (ReCon builds, RMW transmitter tests without a faithful GPR twin): the main-run recon_stlf rerun evidence for
the key says the transmitter `isTainted=1 isSpeculative=1` and NOT forwarded (`fwd` false), and no earlier bucket rule of
the no-twin chain matched (not A2, not R-SA-13 static, not untainted). Label
"check_ld RMW artifact (scores the RMW's leading limm micro-op; delay unit holds the load; RL-10 resolved)".
Evidence: EVAL_MANIFEST "STT / ReCon eval rows" (root-caused by recon-rmw, CHECKER_FIX_PROPOSALS item 2 addendum);
triage/diag/diag_rmw_limm_artifact.md; moved verbatim from runconfigs/twostage_lp/eval_20261110/bucket_eval.py.
Verdict: checker artifact (disqualifier).
"""
LABEL = "check_ld RMW artifact (scores the RMW's leading limm micro-op; delay unit holds the load; RL-10 resolved)"
PAPER_LABEL = None
ALIASES = ["RL-10", "rmw_limm_artifact"]
DEFENSES = ["recon"]
PHASE = "disqualifier"
VERDICT = "checker"
ORDER = 40
NEEDS_GEM5 = True
FAMILY = "recon_bucket"


def matches(rp, e) -> bool:
    return rp == "rmw" and e is not None and "isTainted=1 isSpeculative=1" in (e.get("stl") or "") and not e.get("fwd")
