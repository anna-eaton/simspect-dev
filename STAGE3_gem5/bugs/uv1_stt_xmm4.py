"""UV1 (STT): STT fails to taint one register (FP index 16 = low half of xmm4). Internal label `S1_xmm4`.

Signature (static half of triage/diag/diag_stt_xmm4_skip.py): the gated hit's transmitter backward register slice
(triage/diag/_fv2_slice.transmitter_slice on the test's .s) touches %xmm4. The GPR-twin half is replaced by the parity
baseline (T4 on STT_6_fv2, GPR only, hit 0/1000). Slice errors are `other_stt(slice_err)` (timing runs) /
`other(slice_err)` (eval_gate); other gated hits `other_stt` / `other`. Known slice-tool gap: idiv's implicit operands
(inst-025271, inst-013526 are S1 by inspection, still labelled other).
Evidence: rob_impl.hh:229 at STT e3283b9 (the zero-register check ignores the register class);
wiki/findings/bug/stt_xmm4_taint_skip/; EVAL_MANIFEST "STT / ReCon eval rows" (E3/E4).
Moved verbatim from classify_hits.py (STT path) and runconfigs/twostage_lp/eval_20261110/eval_gate.py.
Verdict: real gem5 defense bug, new (paper UV1).
"""
LABEL = "S1_xmm4"
PAPER_LABEL = "UV1"
ALIASES = ["S1", "S1_xmm4", "stt_xmm4_skip"]
DEFENSES = ["stt"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 80
NEEDS_GEM5 = False
FAMILY = "stt_record"


def matches(sl) -> bool:
    """sl = _fv2_slice.transmitter_slice(stem, mode_dir) without 'err'."""
    return bool(sl["xmm4"])
