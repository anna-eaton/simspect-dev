"""Apply deep-cut edits to a tree. Old text is kept as % comment lines (Anna's convention)."""
import sys, os, re
TAG = "% [deep cut 2026-11-16, was:] "
def live(line): return not line.lstrip().startswith('%')
def load(root, f):
    with open(os.path.join(root, f)) as fh: return fh.read().split('\n')
def save(root, f, lines):
    with open(os.path.join(root, f), 'w') as fh: fh.write('\n'.join(lines))
def count_all(root, f, s):
    return open(os.path.join(root, f)).read().count(s)
def r(root, f, old, new, report):
    L = load(root, f)
    hits = [i for i, l in enumerate(L) if live(l) and old in l]
    occ = sum(L[i].count(old) for i in hits)
    if len(hits) != 1 or occ != 1:
        raise SystemExit(f"NOT UNIQUE/NOT FOUND in {f}: live-line hits={len(hits)} occ={occ}: {old[:80]!r}")
    i = hits[0]
    newline = L[i].replace(old, new)
    out = [TAG + L[i].lstrip()] if True else []
    if newline.strip() != '':
        out.append(newline)
    L[i:i+1] = out
    save(root, f, L)
    report.append((f, i+1, count_all(root, f, old) - 1))  # occurrences left (all in comments)
def block(root, f, start, end, new, report):
    L = load(root, f)
    s = [i for i, l in enumerate(L) if live(l) and start in l]
    if len(s) != 1: raise SystemExit(f"block start not unique {f}: {len(s)} {start[:60]!r}")
    s = s[0]
    e = [i for i, l in enumerate(L) if i >= s and live(l) and end in l]
    if not e: raise SystemExit(f"block end not found {f}: {end[:60]!r}")
    e = e[0]
    out = []
    for l in L[s:e+1]:
        out.append(TAG + l.lstrip() if live(l) else l)
    if new: out.extend(new.split('\n'))
    L[s:e+1] = out
    save(root, f, L)
    report.append((f, s+1, None))
def apply(root, edits):
    rep = []
    for e in edits:
        if e[0] == 'r': r(root, e[1], e[2], e[3], rep)
        elif e[0] == 'block': block(root, e[1], e[2], e[3], e[4], rep)
        else: raise SystemExit('bad edit')
    return rep
