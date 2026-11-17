"""phr.py main.pdf 'w1 w2' ...: grid row (and page/column) of each two-word phrase occurrence (body area)."""
import re, subprocess, sys
t = subprocess.run(['pdftotext', '-bbox', sys.argv[1], '-'], capture_output=True, text=True).stdout
W = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
out = []
for pno, p in enumerate(t.split('<page ')[1:], 1):
    ws = W.findall(p)
    L = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) < 45]
    R = [(float(b), int(w)) for a, b, c, d, w in ws if w.isdigit() and float(a) > 565]
    for ph in sys.argv[2:]:
        a1, a2 = ph.split(' ', 1)
        for i in range(len(ws)-1):
            if ws[i][4] == a1 and ws[i+1][4] == a2 and 45 < float(ws[i][0]) < 565:
                col = L if float(ws[i][0]) < 306 else R
                if col: out.append(f'{ph}: p{pno} row {min(col, key=lambda n: abs(n[0]-float(ws[i][1])))[1]}')
print('; '.join(out))
