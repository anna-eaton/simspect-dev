#!/usr/bin/env python3
"""flat_core_coverage.py — read-only. For every flat instance (inst-*.txt), does it contain a Stage-1 core
under exactly the semantics of stage_seed.build_pred (the Stage-1.5 pin)?  Reports covered / uncovered and the
kind-sequences of uncovered instances, and how many distinct cores each instance contains.
Usage: flat_core_coverage.py <stage_seed dir> <cores dir> <flat xml dir> [jobs]"""
import sys, itertools, collections
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, sys.argv[1])
import stage_seed
SL = ['inreg','inaddr','inmem','outreg','outmem']
def load(p):
    r = stage_seed.parse_txt(str(p)); c = lambda n: r.get(n, [])
    I = [a for (a,) in c('Instruction')]; nxt = dict(c('Instruction<:spo'))
    cur = [i for i in I if i not in nxt.values()][0]; order = []
    while cur: order.append(cur); cur = nxt.get(cur)
    pos = {i:n for n,i in enumerate(order)}
    ops = collections.defaultdict(list)
    for s in SL:
        for i,o in c(f'Instruction<:{s}'): ops[(i,s)].append(o)
    st = {o:s.split('_')[0] for o,s in c('Operand<:opstate')}
    return dict(order=order,pos=pos,kind={i:k.split('$')[0] for i,k in c('Instruction<:kind')},
        res={i for i,_ in c('Instruction<:isresolved')},com={i for i,_ in c('Instruction<:iscommitted')},
        xm={i for i,_ in c('Instruction<:isxm')},ops=ops,st=st,rf=set(c('Operand<:rf')),ddi=set(c('Operand<:ddi')),
        spo=c('Instruction<:spo'))
import os
PATH_PIN = os.environ.get('PATH_PIN') == '1'   # pin (b): a core rf edge may be split through added instructions: rf.*(ddi.rf)
def reach(F, a):
    out = {y for x,y in F['rf'] if x == a}; todo = list(out)
    while todo:
        x = todo.pop()
        for d0,d1 in F['ddi']:
            if d0 == x:
                for r0,r1 in F['rf']:
                    if r0 == d1 and r1 not in out: out.add(r1); todo.append(r1)
    return out
def contains(F, C):
    co = C['order']
    cops = [(i,s,o) for (i,s),l in C['ops'].items() for o in l]
    for tup in itertools.permutations(F['order'], len(co)):
        m = dict(zip(co, tup))
        if any(C['kind'][a] != F['kind'][b] or ((a in C['res']) != (b in F['res'])) or ((a in C['com']) != (b in F['com'])) or (a in C['xm'] and b not in F['xm']) for a,b in m.items()): continue
        if any(F['pos'][m[b]] <= F['pos'][m[a]] for a,b in C['spo']): continue
        cands = [F['ops'].get((m[i],s), []) for i,s,o in cops]
        if any(not c for c in cands): continue
        for ch in itertools.product(*cands):
            if len(set(ch)) != len(ch): continue
            om = {o:f for (i,s,o),f in zip(cops, ch)}
            if any(o in C['st'] and F['st'].get(om[o]) != C['st'][o] for o in om): continue
            if all(((om[b] in reach(F, om[a])) if PATH_PIN else ((om[a],om[b]) in F['rf'])) for a,b in C['rf']) and all((om[a],om[b]) in F['ddi'] for a,b in C['ddi']): return True
    return False
CORES = None
def init(cd):
    global CORES; CORES = [load(p) for p in sorted(Path(cd).glob('inst-*.txt'))]
def job(p):
    F = load(p); hit = [n for n,C in enumerate(CORES) if contains(F, C)]
    return Path(p).stem, hit, tuple(F['kind'][i] for i in F['order'])
if __name__ == '__main__':
    files = sorted(str(x) for x in Path(sys.argv[3]).glob('inst-*.txt'))
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 8, initializer=init, initargs=(sys.argv[2],)) as pool:
        res = pool.map(job, files, chunksize=200)
    unc = [(s,k) for s,h,k in res if not h]
    print(f'flat instances {len(res)}; contain >=1 core {len(res)-len(unc)}; contain NO core {len(unc)}')
    print('cores contained per instance (raw cores, incl. isomorphic copies):', dict(sorted(collections.Counter(len(h) for _,h,_ in res).items())))
    init(sys.argv[2]); print('cores never contained in any flat instance:', sorted(set(range(len(CORES))) - {n for _,h,_ in res for n in h}))
    if len(sys.argv) > 5:
        for s_,k in unc[:int(sys.argv[5])]:
            print('---', s_, k); print(''.join(l for l in open(Path(sys.argv[3])/(s_+'.txt')) if 'Instruction<:' in l or 'Operand<:' in l))
    kc = collections.Counter(k for _,k in unc)
    print('uncovered kind sequences (top 15):', kc.most_common(15)); print('first uncovered stems:', [s for s,_ in unc[:15]])
