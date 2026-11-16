"""H-PAD (text end): an offending event executed by the harness zero padding past the end of .text.

Signature: with --testset, an event whose instruction PC (event pc, else its seq's pipeview pc) is at or past the end of
.text of the binary that ran. `00 00` = `add %al,(%rax)`, reached by wrong-path fetch in mispredict_taken; it is not
the generated test. A target signature carried only by such events becomes `excluded_HPAD:<sig>` (not counted).
.text end = objdump -h of the test rebuilt warm (gem5_common.build_binary) plus cache_setup_info.delta when a cache
setup rewrote it (_trace.text_end).
Evidence: URGENT_TODO.md H-PAD (Anna's decision 2026-11-09); BUGS.md H-PAD; moved verbatim from classify_hits.py is_pad.
Verdict: harness artifact (exclusion; only lowers counts). Applies to the InvisiSpec UV1 and SpecLFB tag rules.
"""
from ._trace import ev_pc

LABEL = "excluded_HPAD"
PAPER_LABEL = None
ALIASES = ["H-PAD"]
DEFENSES = ["invisispec", "speclfb"]
PHASE = "disqualifier"
VERDICT = "artifact"
ORDER = 20
NEEDS_GEM5 = True
FAMILY = "footprint_event"


def is_pad(e, byseq, tend):
    pc = ev_pc(e, byseq)
    return tend is not None and pc is not None and pc >= tend
