#!/usr/bin/env python3
"""textgap.py (agent stt-int-fig, 2026-11-16) -- report every pair of text lines in a PDF page whose boxes overlap or come within --min pt.
Uses `pdftotext -bbox-layout` line boxes (words joined into lines by poppler). Usage: textgap.py <pdf> [--page N] [--min 1.0] [--region x0,y0,x1,y1]
Prints each line (x0 y0 x1 y1 text) when --list, then every close pair. Exit 0 always (a report, not a gate)."""
import argparse, re, subprocess, xml.etree.ElementTree as ET
ap = argparse.ArgumentParser(); ap.add_argument("pdf"); ap.add_argument("--page", type=int, default=1); ap.add_argument("--min", type=float, default=1.0)
ap.add_argument("--region"); ap.add_argument("--list", action="store_true"); a = ap.parse_args()
x = subprocess.run(["pdftotext", "-bbox-layout", "-f", str(a.page), "-l", str(a.page), a.pdf, "-"], capture_output=True, text=True).stdout
x = re.sub(r"<!DOCTYPE[^>]*>", "", x).replace('xmlns="http://www.w3.org/1999/xhtml"', "")
root = ET.fromstring(x); L = []
for ln in root.iter("line"):
    ws = list(ln.iter("word"))
    t = " ".join(w.text or "" for w in ws)
    b = [float(ln.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]
    if a.region:
        r = [float(v) for v in a.region.split(",")]
        if b[2] < r[0] or b[0] > r[2] or b[3] < r[1] or b[1] > r[3]: continue
    L.append((b, t))
if a.list:
    for b, t in L: print(f"{b[0]:7.2f} {b[1]:7.2f} {b[2]:7.2f} {b[3]:7.2f}  {t}")
n = 0
for i in range(len(L)):
    for j in range(i + 1, len(L)):
        (b1, t1), (b2, t2) = L[i], L[j]
        dx = max(b2[0] - b1[2], b1[0] - b2[2]); dy = max(b2[1] - b1[3], b1[1] - b2[3])
        if dx < a.min and dy < a.min:
            n += 1; print(f"CLOSE dx={dx:5.2f} dy={dy:5.2f}  [{t1}] {b1}  vs  [{t2}] {b2}")
print(f"{len(L)} lines, {n} close pairs (gap < {a.min} pt in both x and y)")
