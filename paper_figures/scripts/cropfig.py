import sys, re, fitz
pdf = fitz.open(sys.argv[1]); out = sys.argv[2]; want = sys.argv[3:]  # e.g. "Figure 1:" path ...
pairs = list(zip(want[0::2], want[1::2]))
for pno, page in enumerate(pdf):
    W = page.rect.width; mid = W / 2
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            lt = "".join(s["text"] for s in l["spans"]).strip()
            for cap, dst in pairs:
                if lt.startswith(cap):
                    x0, y0, x1, y1 = l["bbox"]
                    left = x0 < mid
                    cx0, cx1 = (50, mid - 4) if left else (mid + 4, W - 50)
                    # figure top: smallest y of drawings/text in the column above the caption, bounded by the text area top
                    ys = [d["rect"].y0 for d in page.get_drawings() if d["rect"].x0 >= cx0 - 2 and d["rect"].x1 <= cx1 + 2 and d["rect"].y1 <= y0 and d["rect"].y0 > 60]
                    top = min(ys) - 4 if ys else 70
                    clip = fitz.Rect(cx0, top, cx1, y0 - 1)
                    page.get_pixmap(dpi=300, clip=clip).save(dst)
                    print(cap, "page", pno + 1, "clip", [round(v) for v in clip])
