#!/usr/bin/env python3
"""uv5_dstems.py -- run the UNCHANGED STAGE3_gem5/triage/uv5_shape/uv5_timing_scan.py on a testset (one mode) and write the
per-stem scan class: D (same line + U's address ready after S = the full UV5 timing shape), C (static same-line pair, not D),
other. The scan prints only counters and the first 15 D stems; this wrapper executes the script file as-is with runpy and
reads its `ex` (D stems) list. For C it temporarily adds a __setitem__ to collections.Counter that records the loop's current stem `st`
whenever the scan increments "C_same_line_pair(static)" (the script text is not touched).
Usage: uv5_dstems.py <scan.py> <testset> <mode> <out.json>"""
import collections, contextlib, io, json, runpy, sys
scan, ts, mode, out = sys.argv[1:5]
C_STEMS = []
def _rec_setitem(self, k, v):          # temporarily added to collections.Counter (removed again below)
    if k == "C_same_line_pair(static)":
        st = sys._getframe(1).f_globals.get("st")
        if st is not None:
            C_STEMS.append(st)
    dict.__setitem__(self, k, v)
collections.Counter.__setitem__ = _rec_setitem
sys.argv = [scan, ts, mode, "100000000", "1"]
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        g = runpy.run_path(scan, run_name="__main__")
finally:
    del collections.Counter.__setitem__
D = sorted(g["ex"]); Cs = sorted(set(C_STEMS) - set(D))
json.dump({"scan": scan, "testset": ts, "mode": mode, "counters": dict(g["C"]), "D_stems": D, "C_not_D_stems": Cs}, open(out, "w"), indent=1)
print(len(D), "D,", len(Cs), "C-not-D, of", g["C"].get("tests"))
