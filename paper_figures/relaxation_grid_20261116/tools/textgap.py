"""textgap.py fig.pdf: every pair of text spans whose boxes overlap or come within 1.5pt (glyph boxes from PyMuPDF, ascender-descender tight via 'rawdict' chars)."""
import sys, fitz, itertools
doc = fitz.open(sys.argv[1]); pg = doc[0]
sp = []
for b in pg.get_text('rawdict')['blocks']:
    for l in b.get('lines', []):
        for s in l['spans']:
            chars = [c for c in s['chars'] if c['c'].strip()]
            if not chars: continue
            x0 = min(c['bbox'][0] for c in chars); x1 = max(c['bbox'][2] for c in chars)
            # tight vertical box from font metrics: baseline - ascender*size*0.72 .. baseline + 0.2*size
            y = s['origin'][1]; sz = s['size']
            sp.append((''.join(c['c'] for c in s['chars']).strip(), x0, y - 0.70*sz, x1, y + 0.22*sz, sz))
print(len(sp), 'spans; sizes', sorted(set(round(s[5], 2) for s in sp)))
bad = []
for a, b in itertools.combinations(sp, 2):
    dx = max(b[1] - a[3], a[1] - b[3], 0); dy = max(b[2] - a[4], a[2] - b[4], 0)
    if dx < 1.5 and dy < 1.5 and not (dy == 0 and abs(a[2]-b[2]) < 0.5 and dx > 0.5):
        bad.append((round(max(dx, dy), 2), a[0], b[0]))
for g in sorted(bad): print('close/overlap', g)
