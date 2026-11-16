#!/usr/bin/env python3
"""uv5_dstems.py -- run the UNCHANGED STAGE3_gem5/triage/uv5_shape/uv5_timing_scan.py on a testset (one mode) and write
the full list of class-D stems (same line + U's address ready after S = the full UV5 timing shape) plus its counters.
The scan prints only the first 15 D stems; this wrapper executes the script file as-is with runpy and reads its `ex`
list and `C` counter from the resulting globals (regen-lp, 2026-11-10). Usage: uv5_dstems.py <scan.py> <testset> <mode> <out.json>"""
import io, json, runpy, sys, contextlib
scan, ts, mode, out = sys.argv[1:5]
sys.argv = [scan, ts, mode, "100000000", "1"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path(scan, run_name="__main__")
json.dump({"scan": scan, "testset": ts, "mode": mode, "counters": dict(g["C"]), "D_stems": sorted(g["ex"])}, open(out, "w"), indent=1)
print(len(g["ex"]), "D stems of", g["C"].get("tests"))
