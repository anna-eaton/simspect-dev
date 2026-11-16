#!/usr/bin/env python3
"""audit_core_dups.py — read-only: how many Stage-1 cores are duplicates of each other, at 4 levels.
Usage: audit_core_dups.py <stage1_xml dir> [...]
Levels (each coarser than the last):
  exact   : isomorphism incl. which operands share a State (what find_duplicates.canonicalize aims at)
  seed    : what stage_seed.build_pred actually pins (operand state only as Reg/Mem, no state sharing)
  noflag  : seed, with the resolved flag dropped on instructions that are not branches or stores
"""
import sys, itertools, collections
from pathlib import Path
sys.path.insert(0, 'STAGE1_alloy')
import stage_seed

SLOTS = ['inreg', 'inaddr', 'inmem', 'outreg', 'outmem']

def load(path):
    r = stage_seed.parse_txt(str(path))
    col = lambda n: r.get(n, [])
    instrs = [a for (a,) in col('Instruction')]
    nxt = dict(col('Instruction<:spo'))
    first = [i for i in instrs if i not in nxt.values()]
    order = []
    cur = first[0]
    while cur:
        order.append(cur); cur = nxt.get(cur)
    assert len(order) == len(instrs), path
    pc = {i: n for n, i in enumerate(order)}
    kind = {i: k.split('$')[0] for i, k in col('Instruction<:kind')}
    res = {i for i, _ in col('Instruction<:isresolved')}
    com = {i for i, _ in col('Instruction<:iscommitted')}
    xm = {i for i, _ in col('Instruction<:isxm')}
    ops = collections.defaultdict(list)   # instr -> [(slot, opatom)]
    for s in SLOTS:
        for i, o in col(f'Instruction<:{s}'):
            ops[i].append((s, o))
    st = dict(col('Operand<:opstate'))
    return dict(order=order, pc=pc, kind=kind, res=res, com=com, xm=xm, ops=ops, st=st,
                rf=col('Operand<:rf'), ddi=col('Operand<:ddi'))

def fp(c, level):
    # choose an ordering of same-slot operands per instruction; minimise over all choices
    per = []
    for i in c['order']:
        groups = collections.defaultdict(list)
        for s, o in c['ops'][i]:
            groups[s].append(o)
        choices = [list(itertools.permutations(v)) for s, v in sorted(groups.items())]
        keys = sorted(groups)
        per.append([dict(zip(keys, ch)) for ch in itertools.product(*choices)])
    best = None
    for combo in itertools.product(*per):
        name = {}
        for i, d in zip(c['order'], combo):
            for s, lst in d.items():
                for k, o in enumerate(lst):
                    name[o] = (c['pc'][i], s, k)
        canon = {}
        rows = []
        for i in c['order']:
            k = c['kind'][i]
            r = i in c['res']
            if level == 'noflag' and k not in ('TBranchn', 'TBranchx', 'TStore'):
                r = None
            slots = []
            for o, nm in sorted(((o, name[o]) for s, o in c['ops'][i]), key=lambda x: x[1]):
                s = c['st'].get(o)
                if s is None: sv = None
                elif level == 'exact': sv = canon.setdefault(s, (s.split('_')[0], len(canon)))
                else: sv = s.split('_')[0]
                slots.append((nm[1], nm[2], sv))
            rows.append((k, r, i in c['com'], i in c['xm'], tuple(slots)))
        t = (tuple(rows), tuple(sorted((name[a], name[b]) for a, b in c['rf'])),
             tuple(sorted((name[a], name[b]) for a, b in c['ddi'])))
        t = repr(t)
        if best is None or t < best: best = t
    return best

for d in sys.argv[1:]:
    files = sorted(Path(d).glob('inst-*.txt'))
    cores = [load(f) for f in files]
    sizes = collections.Counter(len(c['order']) for c in cores)
    print(f"\n{d}: {len(cores)} cores; size histogram {dict(sorted(sizes.items()))}")
    for lv in ('exact', 'seed', 'noflag'):
        groups = collections.defaultdict(list)
        for f, c in zip(files, cores):
            groups[fp(c, lv)].append(f.stem)
        by = collections.Counter()
        for k, v in groups.items():
            by[len(cores[files.index(next(x for x in files if x.stem == v[0]))]['order'])] += 1
        print(f"  {lv:7s}: {len(groups)} distinct ({100*(1-len(groups)/len(cores)):.0f}% redundant), by size {dict(sorted(by.items()))}")
