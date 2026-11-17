"""floats.py main.pdf: page/column/row of every 'Figure N:' / 'Table N:' caption start, plus section heads."""
import re, subprocess, sys
t = subprocess.run(['pdftotext', '-bbox', sys.argv[1], '-'], capture_output=True, text=True).stdout
W = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
for pno, p in enumerate(t.split('<page ')[1:], 1):
    ws = W.findall(p)
    L = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) < 45]
    R = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) > 565]
    out = []
    for i, (a, b, c, d, w) in enumerate(ws[:-1]):
        nxt = ws[i+1][4]
        if w in ('Figure', 'Table') and re.match(r'^\d+:$', nxt) and 45 < float(a) < 565:
            col = L if float(a) < 306 else R
            row = min(col, key=lambda n: abs(n[0] - float(b)))[1] if col else -1
            out.append(f'{w} {nxt} {"L" if float(a) < 306 else "R"} row {row}')
    if out: print(f'p{pno}: ' + '; '.join(out))
