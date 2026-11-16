#!/usr/bin/env python3
"""check_subsequence.py <v4 pipeview(.gz)> <v5 pipeview(.gz)> -- faithfulness check for the race v5 rerun (figs-stl-race-v3, 2026-11-16).
Passes when every line of the v4 trace (debug flags O3PipeView,LSQUnit,Commit) appears unchanged and in the same order in the v5 trace
(same flags + print-only IEW,IQ), i.e. adding the flags changed no tick of any event v4 printed. Prints the counts and which components
printed the extra lines. (rerun_iq.sh's built-in check filtered only the IEW/IQ-named lines and so reported "DIFFERS": the IEW flag also
prints LSQ-named and 'global' lines; this subsequence check is the one to read.)"""
import collections, gzip, re, sys
def lines(p):
    with (gzip.open(p, "rt", errors="replace") if p.endswith(".gz") else open(p, errors="replace")) as f:
        return f.read().splitlines()
v4, v5 = lines(sys.argv[1]), lines(sys.argv[2])
i, extra = 0, []
for l in v5:
    if i < len(v4) and l == v4[i]:
        i += 1
    else:
        extra.append(l)
print(f"v4 lines {len(v4)}, matched in order {i}, v5 lines {len(v5)}, extra {len(extra)}")
print(collections.Counter(re.sub(r"^\s*\d+: ", "", l).split(":")[0] for l in extra).most_common(8))
sys.exit(0 if i == len(v4) else 1)
