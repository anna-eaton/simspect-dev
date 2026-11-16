"""Audit rendered font sizes inside every figure/table of a two-column ACM PDF.
Region of a float = spans in its column(s) above (figures) or below (tables) its caption,
up to the nearest full-width 9pt body line. Sizes are in PDF bp (8 TeX pt = 7.97 bp)."""
import sys, re, fitz
pdf = fitz.open(sys.argv[1]); MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 7.9
def spans(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            lt = "".join(s["text"] for s in l["spans"]).strip()
            for s in l["spans"]:
                x0, y0, x1, y1 = s["bbox"]
                if s["text"].strip() and x0 > 50 and x1 < page.rect.width - 50 and y0 > 62 and y1 < page.rect.height - 50:
                    out.append(dict(t=s["text"], size=s["size"], bbox=s["bbox"], line=lt, lbbox=l["bbox"], font=s["font"]))
    return out
for pno, page in enumerate(pdf, 1):
    W = page.rect.width; mid = W / 2
    ss = spans(page)
    caps = [s for s in ss if re.match(r"^(Figure|Table) \d+[:.]", s["line"]) and s["t"].strip().startswith(("Figure", "Table"))]
    seen = set()
    for c in caps:
        key = c["line"][:12]
        if key in seen: continue
        seen.add(key)
        cx0, cy0, cx1, cy1 = c["lbbox"]
        # caption block extent: lines below with same x-range until a gap
        wide = False
        capblock = [x for x in ss if abs(x["lbbox"][0] - cx0) < 30 and x["lbbox"][1] >= cy0 - 1 and x["lbbox"][1] < cy0 + 120]
        right = max(x["lbbox"][2] for x in capblock); wide = (right - cx0) > 300
        col = (lambda x: True) if wide else ((lambda x: x["bbox"][0] < mid) if cx0 < mid else (lambda x: x["bbox"][0] >= mid - 5))
        is_table = c["line"].startswith("Table")
        cand = [x for x in ss if col(x) and ((x["bbox"][3] <= cy0 + 0.5) if not is_table else (x["bbox"][1] >= cy1 + 20))]
        cand.sort(key=lambda x: -x["bbox"][1] if not is_table else x["bbox"][1])
        region = []
        for x in cand:
            lw = x["lbbox"][2] - x["lbbox"][0]
            if 8.8 < x["size"] < 9.3 and lw > 200 and not re.match(r"^(Figure|Table) \d", x["line"]):
                break
            if re.match(r"^(Figure|Table) \d", x["line"]): break
            region.append(x)
        if not region:
            print(f"p{pno} {key}: no text found in region"); continue
        mn = min(x["size"] for x in region)
        small = [x for x in region if x["size"] < MIN]
        print(f"p{pno} {key:12s} {'wide' if wide else 'col '} spans={len(region):4d} min={mn:5.2f} sizes={sorted(set(round(x['size'],2) for x in region))}")
        for x in small[:40]:
            print(f"      SMALL {x['size']:.2f} {x['font']:>18s} {x['t'][:40]!r}  line={x['line'][:70]!r}")
