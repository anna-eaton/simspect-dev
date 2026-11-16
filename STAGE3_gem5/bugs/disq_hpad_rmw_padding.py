"""H-PAD (RMW padding actor): a CleanupSpec UV3 / E->M chain whose actor is the harness padding RMW, not the test's RMW.

Signature: the chain's actor macro-op (looked up by pc in any O3PipeView fetch record; the actor's own seq often has
none) is ADD_M_R and its pc lies after the transmitter (pc > xmit_pc). The source corpus has no memory-destination ALU
op, so ADD_M_R after the xmit can only be the `00 00` padding past .text. Labels `UV3_padding` (UV3 chain) and
`EM_padding` (E->M chain); both EXCLUDED. The stored annotation cannot bound the code: cold cache_setup shifts every pc.
Evidence: BUGS.md H-PAD; moved verbatim from STAGE3_gem5/timing/classify_cs_rmw.py is_padding.
Verdict: harness artifact (exclusion; only lowers counts).
"""
LABEL = "UV3_padding|EM_padding"
PAPER_LABEL = None
ALIASES = ["H-PAD", "UV3_padding", "EM_padding"]
DEFENSES = ["cleanupspec"]
PHASE = "disqualifier"
VERDICT = "artifact"
ORDER = 21
NEEDS_GEM5 = True
FAMILY = "cleanupspec_rmw_item"


def is_padding(pc: int, xpc, dis_by_pc) -> bool:
    return xpc is not None and pc > xpc and dis_by_pc.get(pc) == "ADD_M_R"
