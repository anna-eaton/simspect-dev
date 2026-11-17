import sys, os, re, importlib.util
SC='/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0, SC+'/tools'); from reasons import REASONS
def load(n, f):
    s=importlib.util.spec_from_file_location(n, SC+'/tools/'+f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
pm = load('p2','patches2.py')
base = SC+'/base3'
def code(t):
    if t == '': return '*(cut)*'
    n = max([len(x) for x in re.findall(r'`+', t)] + [0]) + 1
    d = '`'*n; pad = ' ' if (t.startswith('`') or t.endswith('`')) else ''
    return f'{d}{pad}{t}{pad}{d}'
def where(f, old):
    L = open(os.path.join(base, f)).read().split('\n')
    ln = [i+1 for i,l in enumerate(L) if not l.lstrip().startswith('%') and old in l]
    allc = open(os.path.join(base, f)).read().count(old)
    return (ln[0] if ln else None), allc
res = {}
for l in open(SC+'/runs/final3.log'):
    m = re.match(r'(\d\d) (\S+) (\S+) row (\d+) delta (-?\d+)', l)
    if m: res[m.group(1)] = (int(m.group(4)), int(m.group(5)))
out = []
for pid, name, tier, edits in pm.PATCHES:
    row, d = res.get(pid, (None, None))
    out.append(f'#### Patch {pid} `{pid}_{name}.patch` ({tier}; measured {d:+d} rows, body end row {row})' if row else f'#### Patch {pid} {name} ({tier})')
    out.append('')
    for k, e in enumerate(edits):
        f = e[1]; old = e[2]; new = e[3] if e[0] != 'block' else e[4]
        if e[0] == 'block':
            ln, c = where(f, old); old_disp = f'from {code(e[2])} through {code(e[3])} (lines {ln}ff.)'
        else:
            ln, c = where(f, old); old_disp = code(old)
        twin = '' if c == 1 else f' (live line; {c-1} %-commented copy also in the file)'
        out.append(f'- {pid}.{k+1} `{f}` (line {ln}){twin}: {old_disp} → {code(new)}. *Why:* {REASONS.get((pid,k),"")}.')
    out.append('')
open(SC+'/percut.md','w').write('\n'.join(out))
print(len(out))
