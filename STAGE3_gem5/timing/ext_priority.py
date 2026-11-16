#!/usr/bin/env python3
"""ext_priority.py: write a firstdet_stream --priority-file from the ext corpus MANIFEST.tsv.
Each MANIFEST row carries a shape class (D / C / other); tier 0 = D, 1 = C (not_taken mode), 2 = other
and every taken-mode test. Only the run ORDER depends on it. Atomic rewrite.
    python3 ext_priority.py <testset>/MANIFEST.tsv <out.tsv>
"""
import re, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
lines = src.read_text().splitlines()
hdr = lines[0].split("\t")
lc = [h.lower() for h in hdr]
ci = next((i for i, h in enumerate(lc) if h in ("class", "shape", "shape_class", "uv5_class")), None)
mi = next((i for i, h in enumerate(lc) if h in ("modes", "mode")), None)
TIER = {"d": 0, "c": 1}
out, n = [], {0: 0, 1: 0, 2: 0}
for l in lines[1:]:
    f = l.split("\t")
    if not f or not f[0].startswith("inst-"):
        continue
    cls = (f[ci].strip().lower() if ci is not None and ci < len(f) else "other")
    t = TIER.get(cls, 2)
    modes = re.findall(r"mispredict_not_taken|mispredict_taken", f[mi]) if mi is not None and mi < len(f) else ["mispredict_not_taken"]
    for m in modes:   # the D/C shapes are not_taken-mode shapes (uv5_timing_scan); taken-mode tests go last
        tt = t if m == "mispredict_not_taken" else 2
        out.append(f"{tt}\t{m}\t{f[0].strip()}\n"); n[tt] += 1
tmp = dst.with_suffix(".tmp"); tmp.write_text("".join(out)); tmp.replace(dst)
print(f"class column={hdr[ci] if ci is not None else None}; tiers {n}")
