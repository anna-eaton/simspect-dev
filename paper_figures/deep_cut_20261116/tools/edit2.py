r"""Wrap deep-cut spans in Anna's highlight macros: pure cut -> \cutsug{old}; replacement -> \cutrep{old}{new}."""
import os
def live(line): return not line.lstrip().startswith('%')
def r(root, f, old, new):
    p = os.path.join(root, f); L = open(p).read().split('\n')
    hits = [i for i, l in enumerate(L) if live(l) and old in l]
    occ = sum(L[i].count(old) for i in hits)
    if len(hits) != 1 or occ != 1:
        raise SystemExit(f"NOT UNIQUE/NOT FOUND in {f}: live-line hits={len(hits)} occ={occ}: {old[:90]!r}")
    i = hits[0]
    w = ('\\cutsug{' + old + '}') if new == '' else ('\\cutrep{' + old + '}{' + new + '}')
    L[i] = L[i].replace(old, w)
    open(p, 'w').write('\n'.join(L))
def block(root, f, start, end, new):
    p = os.path.join(root, f); L = open(p).read().split('\n')
    s = [i for i, l in enumerate(L) if live(l) and start in l]
    if len(s) != 1: raise SystemExit(f"block start not unique {f}: {len(s)} {start[:60]!r}")
    s = s[0]; e = [i for i, l in enumerate(L) if i >= s and live(l) and end in l][0]
    a = L[s].index(start); L[s] = L[s][:a] + ('\\cutsug{' if not new else '\\cutrep{') + L[s][a:]
    b = L[e].rindex(end) + len(end); L[e] = L[e][:b] + ('}' if not new else '}{' + new + '}') + L[e][b:]
    open(p, 'w').write('\n'.join(L))
def apply(root, edits):
    for e in edits:
        if e[0] == 'r': r(root, e[1], e[2], e[3])
        elif e[0] == 'block': block(root, e[1], e[2], e[3], e[4])
        elif e[0] == 'rx': p=os.path.join(root,e[1]); t=open(p).read(); assert t.count(e[2])==1, e[2]; open(p,'w').write(t.replace(e[2],e[3]))
import edit as _direct
def apply(root, edits):   # override: 'rd' = direct replacement (old line kept as a % comment), for macro definitions and \input lines
    for e in edits:
        if e[0] == 'r': r(root, e[1], e[2], e[3])
        elif e[0] == 'rd': _direct.r(root, e[1], e[2], e[3], [])
        elif e[0] == 'block': block(root, e[1], e[2], e[3], e[4])
        elif e[0] == 'rx': p=os.path.join(root,e[1]); t=open(p).read(); assert t.count(e[2])==1, e[2]; open(p,'w').write(t.replace(e[2],e[3]))
