"""labels.py -- neutral E2w (ReCon) bucket labels for the anonymous artifact (agent anonrepo, 2026-11-16, coordinator:
rename labels that carry internal IDs). Used by build_anon.py (classifier code), pack_data.py (shipped records) and
relabel_data.py (one-off rewrite of an existing data/ tree). Applied longest-first as plain substring replacements."""
RENAMES = [
    ("check_ld RMW artifact (scores the RMW's leading limm micro-op; delay unit holds the load; RL-10 resolved)",
     "check_ld RMW artifact (scores the RMW's leading limm micro-op; delay unit holds the load)"),
    ("R-SA-13 via FP elsewhere (twin held; e2-losttaint idiv-divisor case)", "SSE-load producer via FP elsewhere (twin held; idiv divisor case)"),
    ("R-SA-8 candidate (br_x twin hit; E2LT-2)", "oldest-taint candidate (br_x twin hit)"),
    ("R-SA-8 candidate (br_x twin hit)", "oldest-taint candidate (br_x twin hit)"),
    ("R-SA-13_static(SSE-load producer)", "SSE-load producer (static)"),
    ("(R-SA-13 candidate", "(SSE-load producer candidate"),
    ("R-SA-13 (static only", "SSE-load producer (static only"),
    ("A2 STLF bypass", "STLF bypass"),
    ("R-SA-13", "SSE-load producer"),
]
FIELD_RENAMES = [("rsa8_signature", "oldest_taint_signature")]


def relabel(s):
    for a, b in RENAMES:
        s = s.replace(a, b)
    return s
