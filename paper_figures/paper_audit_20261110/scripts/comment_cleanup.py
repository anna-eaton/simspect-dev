"""Delete verified-stale comments from ISCA-27 sections (2026-11-11). Writes deletions TSV."""
import sys, re, json, os
ROOT = os.path.expanduser('~/trippel/ISCA-27/sections')
def R(a, b=None): return list(range(a, (b or a) + 1))
DEL = {
 'abstract.tex': R(5,11)+R(14)+R(18,19)+R(22,25),
 'intro.tex': [2,5,14,16,18]+R(24,28)+[35,44,45,65,79,81],
 'background.tex': [37],
 'model.tex': R(16,22)+R(27,28)+[32]+R(38,39)+[55]+R(71,72)+R(75,76)+R(79,80)+[93,103]+R(105,121),
 'pipeline.tex': [4,5,16,17,20,41,48,49,50,93,125,168,249,257,269,274],
 'results.tex': [1,34,65,85]+R(87,122)+R(180,182)+R(184,187),
}
INLINE = {'related.tex': {94: ' % \\todo{add other contract/SNI works}', 211: ' % \\todo{add Spectre litmus benchmark + fuzzing cites}'}}
ok_kinds = re.compile(r'^\s*(%|\\anna\{|\\urgentbr|\\notebr|\\labbr|\\labnote\{|\\auditnote\{|\\urgentnote\{|\\iffalse|\\fi\b|$)')
log = []
dry = '--apply' not in sys.argv
for fn, lines in DEL.items():
    p = os.path.join(ROOT, fn); src = open(p).read().split('\n')
    dels = set(lines)
    # lines inside an \iffalse..\fi block may be anything; check block bounds
    inblk = False
    for n in sorted(dels):
        s = src[n-1]
        if s.startswith('\\iffalse'): inblk = True
        if not inblk and not ok_kinds.match(s):
            sys.exit(f'REFUSE {fn}:{n} not a comment/note line: {s[:80]}')
        if inblk and s.startswith('\\fi'): inblk = False
        log.append((fn, n, s[:100].replace('|','/')))
    out = []; deleted_since = False
    for i, s in enumerate(src, 1):
        if i in dels: deleted_since = True; continue
        if deleted_since and s.strip() == '' and out and out[-1].strip() == '': deleted_since = False; continue
        deleted_since = False if s.strip() else deleted_since
        out.append(s)
    if not dry: open(p, 'w').write('\n'.join(out))
for fn, m in INLINE.items():
    p = os.path.join(ROOT, fn); src = open(p).read().split('\n')
    for n, frag in m.items():
        assert src[n-1].endswith(frag), (fn, n, src[n-1])
        log.append((fn, n, frag.strip()))
        src[n-1] = src[n-1][:-len(frag)]
    if not dry: open(p, 'w').write('\n'.join(src))
print(json.dumps(log, indent=0) if dry else f'applied {len(log)} line deletions/edits')
