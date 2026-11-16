"""R-SA-9 (ReCon, in the GPR twin): a twin-hit ld whose main-run transmitter was untainted, and the twin rerun shows no
reveal untaint. Bucket "R-SA-13 main / R-SA-9 twin (E2LT-1)".

Signature (bucket_eval, ld twin hit): main-run recon_stlf evidence reproduced, not the A2 signature, STL_CHECK
isTainted=0; the twin's reveal_check.py record exists and has revealRequests == 0. If no reveal record exists the bucket is
"isTainted=0 (reveal not checked)".
Evidence: e2-losttaint verdict E2LT-1; EVAL_MANIFEST "STT / ReCon eval rows". Moved verbatim from bucket_eval.py.
Verdict: known ReCon behaviour (R-SA-13 in the main run, R-SA-9 in the twin); not a paper bug.
"""
LABEL = "R-SA-13 main / R-SA-9 twin (E2LT-1)"
PAPER_LABEL = None
ALIASES = ["R-SA-9", "E2LT-1"]
DEFENSES = ["recon"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 92
NEEDS_GEM5 = True
FAMILY = "recon_bucket"


def matches(r) -> bool:
    """r = reveal_check.py record for the key (None when not checked); called after recon_reveal_artifact."""
    return r is not None
