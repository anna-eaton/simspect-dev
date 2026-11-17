"""bodyend.py main.pdf -> References heading row, last body line row (acmart review grid)."""
import re, subprocess, sys
pdf = sys.argv[1]
t = subprocess.run(['pdftotext', '-bbox', pdf, '-'], capture_output=True, text=True).stdout
pages = t.split('<page ')[1:]
W = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
def rows(ws):
    L = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) < 45]
    R = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) > 565]
    return L, R
def rowof(y, nums):
    return min(nums, key=lambda n: abs(n[0] - y))[1]
for pno, p in enumerate(pages, 1):
    ws = W.findall(p)
    refs = [w for w in ws if w[4] == 'References' and 45 < float(w[0]) < 565]
    if not refs: continue
    a, b, c, d, _ = refs[-1]; x0, y0 = float(a), float(b)
    L, R = rows(ws)
    col = L if x0 < 306 else R
    rr = rowof(y0, col)
    # last body word before References in reading order (same column above, else left column)
    body = [(float(w[1]), float(w[0]), w[4]) for w in ws if 45 < float(w[0]) < 565 and not w[4].isdigit() or (45 < float(w[0]) < 565 and w[4].isdigit())]
    same = [x for x in body if ((x[1] < 306) == (x0 < 306)) and x[0] < y0 - 2 and x[0] > 75]
    if same:
        yl = max(same)[0]; last = rowof(yl, col); words = ' '.join(x[2] for x in sorted(same) if abs(x[0]-yl) < 1)
    else:
        lc = [x for x in body if x[1] < 306 and x[0] > 75 and x[0] < 735 and not x[2].isdigit()]
        yl = max(lc)[0]; last = rowof(yl, L); words = ' '.join(x[2] for x in sorted(lc) if abs(x[0]-yl) < 1)
    print(f'page {pno}: References heading row {rr}; last line before it row {last}: "{words[-60:]}"')
