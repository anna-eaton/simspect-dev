"""UV2 (ReCon): store-to-load forwarding skips the taint check. Internal label A2, `recon_SLF_stlf_bypass`.

Signature (ld transmitter; recon_stlf evidence from one faithful rerun, STAGE3_gem5/triage/rerun_hits_evidence.py
--analyzer recon_stlf): the hit reproduced, the STL_CHECK line after the transmitter's execute says `isTainted=1
isSpeculative=1`, a forwarding line follows it (`fwd`), and it is ready inside the window (`ready_in_window`).
Bucket labels: "A2 STLF bypass" (twin hit), "A2 STLF bypass (main-run evidence, no twin[, RMW])".
Evidence: lsq_unit.cc:2019 in ReCon; wiki/findings/bug/recon_SLF_stlf_bypass/; triage/diag/diag_recon_stlf_bypass.md.
Moved verbatim from runconfigs/twostage_lp/eval_20261110/bucket_eval.py.
Verdict: real gem5 defense bug, new (paper UV2).
"""
LABEL = "A2 STLF bypass"
PAPER_LABEL = "UV2"
ALIASES = ["A2", "recon_SLF_stlf_bypass", "recon_slf"]
DEFENSES = ["recon"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 85
NEEDS_GEM5 = True
FAMILY = "recon_bucket"


def matches(e) -> bool:
    return (e is not None and e.get("reproduced", True) and "isTainted=1 isSpeculative=1" in (e.get("stl") or "")
            and bool(e.get("fwd")) and bool(e.get("ready_in_window")))
