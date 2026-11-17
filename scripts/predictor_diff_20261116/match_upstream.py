"""For each build tree's src/cpu/pred, find the upstream gem5 commit whose src/cpu/pred matches best (by git blob hash).
Usage: python3 -I match_upstream.py <hashes.txt> <bare upstream repo>"""
import sys, subprocess, collections
hashes, repo = sys.argv[1], sys.argv[2]
G = ['/usr/bin/git', '-C', repo]
trees = collections.defaultdict(dict)
for ln in open(hashes):
    t, f, h = ln.split(); trees[t][f] = h
commits = subprocess.run(G + ['rev-list', '--all', '--', 'src/cpu/pred'], capture_output=True, text=True).stdout.split()
snap = {}
for c in commits:
    out = subprocess.run(G + ['ls-tree', c, 'src/cpu/pred/'], capture_output=True, text=True).stdout
    snap[c] = {l.split('\t')[1].rsplit('/', 1)[1]: l.split()[2] for l in out.splitlines() if l.split()[1] == 'blob'}
def desc(c):
    return subprocess.run(G + ['log', '-1', '--format=%h %ad %s', '--date=short', c], capture_output=True, text=True).stdout.strip()
for t, files in trees.items():
    best = max(snap, key=lambda c: (sum(files.get(f) == h for f, h in snap[c].items()) - len(set(files) ^ set(snap[c])), -0))
    s = snap[best]
    match = sorted(f for f in files if s.get(f) == files[f])
    diff = sorted(f for f in files if f in s and s[f] != files[f])
    only_build = sorted(set(files) - set(s)); only_up = sorted(set(s) - set(files))
    print(f'== {t}\n  best pred-tree commit: {desc(best)} ({best[:10]})\n  identical {len(match)}/{len(files)}; differ: {diff}; only in build: {only_build}; only upstream: {only_up}')
