"""For each (tree, file) whose blob is not identical to the base commit, list upstream commits in whose src/cpu/pred that exact blob appears.
Usage: python3 -I file_lookup.py <hashes.txt> <bare repo> <tree-substring>..."""
import sys, subprocess, collections
hashes, repo, *want = sys.argv[1:]
G = ['/usr/bin/git', '-C', repo]
commits = subprocess.run(G + ['rev-list', '--all', '--', 'src/cpu/pred'], capture_output=True, text=True).stdout.split()
where = collections.defaultdict(list)
for c in commits:
    for l in subprocess.run(G + ['ls-tree', c, 'src/cpu/pred/'], capture_output=True, text=True).stdout.splitlines():
        where[l.split()[2]].append(c)
def d(c): return subprocess.run(G + ['log', '-1', '--format=%h %ad', '--date=short', c], capture_output=True, text=True).stdout.strip()
for ln in open(hashes):
    t, f, h = ln.split()
    if any(w == t for w in want):
        cs = where.get(h, [])
        print(t, f, 'UPSTREAM' if cs else 'not-upstream', (d(cs[-1]) + ' .. ' + d(cs[0])) if cs else '')
