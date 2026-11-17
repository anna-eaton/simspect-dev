"""rotgap.py fig.pdf [fig2.pdf ...]: overlap check that also handles rotated text. Each span's box = union of its glyph boxes as PyMuPDF reports them
(font-box tall: ascender..descender, so conservative), for horizontal and rotated spans alike. Prints pairs of different spans closer than 1pt
(same-line neighbours such as '565' + 'x' and superscripts are skipped: they belong to one label)."""
import sys, itertools, warnings
warnings.filterwarnings('ignore')
import fitz
for f in sys.argv[1:]:
    pg = fitz.open(f)[0]; sp = []
    for b in pg.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            d = l['dir']
            for s in l['spans']:
                ch = [c for c in s['chars'] if c['c'].strip()]
                if not ch: continue
                bb = fitz.Rect(ch[0]['bbox'])
                for c in ch[1:]: bb |= fitz.Rect(c['bbox'])
                sp.append((''.join(c['c'] for c in s['chars']).strip(), bb, tuple(round(x, 2) for x in d), id(l)))
    bad = []
    for a, b in itertools.combinations(sp, 2):
        if a[3] == b[3]: continue  # same line object = one label (number + x, A-UV5 + dagger)
        dx = max(b[1].x0 - a[1].x1, a[1].x0 - b[1].x1, 0); dy = max(b[1].y0 - a[1].y1, a[1].y0 - b[1].y1, 0)
        if max(dx, dy) < 1.0: bad.append((round(max(dx, dy), 2), a[0], b[0], a[2], b[2]))
    print(f'{f}: {len(sp)} spans, {len(bad)} pairs closer than 1pt (font boxes)')
    for g in sorted(bad): print('  ', g)
