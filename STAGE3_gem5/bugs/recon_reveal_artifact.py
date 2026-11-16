"""Reveal artifact in the GPR twin (E2LT-3): a ReCon reveal untaint enabled by a Stage-2 committed load pair / alias on
rsp+0. Bucket "R-SA-13 main / reveal artifact in twin (E2LT-3)".

Signature (bucket_eval, ld twin hit): main-run recon_stlf evidence reproduced, not the A2 signature, STL_CHECK
isTainted=0; the twin's reveal_check.py record has revealRequests > 0 (system.cpu.lsq0.revealRequests in stats.txt).
Evidence: e2-losttaint run.py method, verdict E2LT-3; runconfigs/twostage_lp/eval_20261110/reveal_check.py.
Moved verbatim from bucket_eval.py.
Verdict: harness artifact in the twin (the main-run hit is still R-SA-13).
"""
LABEL = "R-SA-13 main / reveal artifact in twin (E2LT-3)"
PAPER_LABEL = None
ALIASES = ["E2LT-3"]
DEFENSES = ["recon"]
PHASE = "disqualifier"
VERDICT = "artifact"
ORDER = 45
NEEDS_GEM5 = True
FAMILY = "recon_bucket"


def matches(r) -> bool:
    return bool(r) and r.get("revealRequests", 0) > 0
