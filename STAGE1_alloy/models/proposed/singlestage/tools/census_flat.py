#!/usr/bin/env python3
"""census_flat.py — read-only census of flat enumeration output (inst-*.txt), per run dir and for their union.
Per run and for the union it reports: instances, distinct programs (isomorphism fingerprint: kinds in program
order, resolved/committed/xm flags, operand slots with canonical state sharing, rf and ddi edges), size histogram,
distinct kind sequences, and shape counts:
  alu_feeds_xmit      an other_n/other_x output is read by the transmitter's leak operand
  two_load_merge      an ALU on the transmitter's backward cone reads the outputs of >= 2 distinct loads (OTB-like)
  unnecessary         instructions that are NOT the transmitter, NOT in its backward dataflow cone (rf/ddi), and NOT
                      an unresolved branch/store before it  (avg per program + histogram)
  bare                instructions with no operands (avg)
  unresolved_brs      histogram of unresolved branches per program
With --cores DIR (+ --stage1 <STAGE1_alloy dir>): how many distinct programs contain a Stage-1 core under the exact
pin and under the path pin (flat_core_coverage.py semantics).
Usage: census_flat.py [--cores DIR --stage1 DIR] [--jobs 8] [--json OUT.json] RUN_DIR [RUN_DIR ...]
"""
import argparse, collections, itertools, json, os, sys
from multiprocessing import Pool
from pathlib import Path
import re
SL = ['inreg', 'inaddr', 'inmem', 'outreg', 'outmem']
PAT = re.compile(r'this/([A-Za-z_]+(?:<:[A-Za-z_]+)?)=\{(.*)\}')
def parse_txt(path):
    rels = {}
    for line in open(path):
        m = PAT.match(line.strip())
        if m:
            b = m.group(2).strip()
            rels[m.group(1)] = [tuple(x.strip() for x in t.split('->')) for t in b.split(',')] if b else []
    return rels
def load(p):
    r = parse_txt(p); c = lambda n: r.get(n, [])
    I = [x for (x,) in c('Instruction')]; nxt = dict(c('Instruction<:spo'))
    cur = [i for i in I if i not in nxt.values()][0]; order = []
    while cur: order.append(cur); cur = nxt.get(cur)
    ops = collections.defaultdict(list)
    for s in SL:
        for i, o in c(f'Instruction<:{s}'): ops[(i, s)].append(o)
    return dict(order=order, pos={i: n for n, i in enumerate(order)}, kind={i: k.split('$')[0] for i, k in c('Instruction<:kind')},
                res={i for i, _ in c('Instruction<:isresolved')}, com={i for i, _ in c('Instruction<:iscommitted')},
                xm={i for i, _ in c('Instruction<:isxm')}, ops=ops, st=dict(c('Operand<:opstate')),
                rf=set(c('Operand<:rf')), ddi=set(c('Operand<:ddi')), spo=c('Instruction<:spo'))
def fingerprint(F):
    per = []
    for i in F['order']:
        g = {s: F['ops'][(i, s)] for s in SL if F['ops'].get((i, s))}
        keys = sorted(g); per.append([dict(zip(keys, ch)) for ch in itertools.product(*[list(itertools.permutations(g[k])) for k in keys])])
    best = None
    for combo in itertools.product(*per):
        name = {}
        for i, d in zip(F['order'], combo):
            for s, l in d.items():
                for k, o in enumerate(l): name[o] = (F['pos'][i], s, k)
        canon, rows = {}, []
        for i, d in zip(F['order'], combo):
            sl = []
            for o, nm in sorted(((o, name[o]) for l in d.values() for o in l), key=lambda x: x[1]):
                s = F['st'].get(o); sl.append((nm[1], nm[2], None if s is None else canon.setdefault(s, (s.split('_')[0], len(canon)))))
            rows.append((F['kind'][i], i in F['res'], i in F['com'], i in F['xm'], tuple(sl)))
        t = repr((tuple(rows), tuple(sorted((name[x], name[y]) for x, y in F['rf'])), tuple(sorted((name[x], name[y]) for x, y in F['ddi']))))
        if best is None or t < best: best = t
    return best
def shape(F):
    opi = {o: i for (i, s), l in F['ops'].items() for o in l}
    xm = next(iter(F['xm']), None)
    ins_of = lambda i: [o for s in ('inreg', 'inaddr', 'inmem') for o in F['ops'].get((i, s), [])]
    alu = lambda i: F['kind'][i] in ('TOthern', 'TOtherx')
    cone, todo = set(), [xm] if xm else []
    while todo:
        i = todo.pop()
        for o in ins_of(i):
            for x, y in F['rf']:
                if y == o and opi[x] not in cone and opi[x] != xm:
                    cone.add(opi[x]); todo.append(opi[x])
    xleak = [o for s in ('inaddr', 'inreg') for o in F['ops'].get((xm, s), [])] if xm else []
    alu_feeds = any(alu(opi[x]) for x, y in F['rf'] if y in xleak)
    merge = any(alu(i) and len({opi[x] for x, y in F['rf'] if y in ins_of(i) and F['kind'][opi[x]] == 'TLoad'}) >= 2 for i in cone)
    gate = {i for i in F['order'] if i not in F['res'] and F['kind'][i] in ('TBranchn', 'TBranchx', 'TStore') and xm and F['pos'][i] < F['pos'][xm]}
    unnec = [i for i in F['order'] if i != xm and i not in cone and i not in gate]
    bare = sum(1 for i in F['order'] if not any(F['ops'].get((i, s)) for s in SL))
    ubr = sum(1 for i in F['order'] if i not in F['res'] and F['kind'][i] in ('TBranchn', 'TBranchx'))
    return dict(n=len(F['order']), kinds=tuple(F['kind'][i] for i in F['order']), alu_feeds_xmit=alu_feeds, two_load_merge=merge,
                unnecessary=len(unnec), bare=bare, unresolved_brs=ubr, xm_kind=F['kind'].get(xm))
def reach(F, a):
    out = {y for x, y in F['rf'] if x == a}; todo = list(out)
    while todo:
        x = todo.pop()
        for d0, d1 in F['ddi']:
            if d0 == x:
                for r0, r1 in F['rf']:
                    if r0 == d1 and r1 not in out: out.add(r1); todo.append(r1)
    return out
def contains(F, C, path):
    co = C['order']; cops = [(i, s, o) for (i, s), l in C['ops'].items() for o in l]
    for tup in itertools.permutations(F['order'], len(co)):
        m = dict(zip(co, tup))
        if any(C['kind'][x] != F['kind'][y] or ((x in C['res']) != (y in F['res'])) or ((x in C['com']) != (y in F['com'])) or (x in C['xm'] and y not in F['xm']) for x, y in m.items()): continue
        if any(F['pos'][m[y]] <= F['pos'][m[x]] for x, y in C['spo']): continue
        cands = [F['ops'].get((m[i], s), []) for i, s, o in cops]
        if any(not c for c in cands): continue
        for ch in itertools.product(*cands):
            if len(set(ch)) != len(ch): continue
            om = {o: f for (i, s, o), f in zip(cops, ch)}
            if any(o in C['st'] and (F['st'].get(om[o]) or '').split('_')[0] != C['st'][o].split('_')[0] for o in om): continue
            if all(((om[y] in reach(F, om[x])) if path else ((om[x], om[y]) in F['rf'])) for x, y in C['rf']) and all((om[x], om[y]) in F['ddi'] for x, y in C['ddi']): return True
    return False
CORES = []
def init(cd):
    global CORES
    if cd:
        seen = {}
        for p in sorted(Path(cd).glob('**/inst-*.txt')):
            C = load(p); seen.setdefault(fingerprint(C), C)
        CORES = list(seen.values())
def job(p):
    try:
        F = load(p); s = shape(F); s['fp'] = fingerprint(F)
        if CORES:
            s['cov_exact'] = any(contains(F, C, False) for C in CORES)
            s['cov_path'] = s['cov_exact'] or any(contains(F, C, True) for C in CORES)
        return p, s
    except Exception as e:
        return p, {'error': repr(e)}
def summarize(rows):
    d = {}
    for r in rows: d.setdefault(r['fp'], r)
    u = list(d.values()); n = len(u) or 1
    out = dict(instances=len(rows), distinct=len(u), sizes=dict(sorted(collections.Counter(r['n'] for r in u).items())),
               kind_sequences=len({r['kinds'] for r in u}), xm_kinds=dict(collections.Counter(r['xm_kind'] for r in u)),
               alu_feeds_xmit=sum(r['alu_feeds_xmit'] for r in u), two_load_merge=sum(r['two_load_merge'] for r in u),
               unnecessary_avg=round(sum(r['unnecessary'] for r in u) / n, 2), unnecessary_hist=dict(sorted(collections.Counter(r['unnecessary'] for r in u).items())),
               bare_avg=round(sum(r['bare'] for r in u) / n, 2), unresolved_brs_hist=dict(sorted(collections.Counter(r['unresolved_brs'] for r in u).items())))
    if u and 'cov_exact' in u[0]:
        out.update(contain_core_exact_pin=sum(r['cov_exact'] for r in u), contain_core_path_pin=sum(r['cov_path'] for r in u),
                   no_core_even_path_pin_examples=[r['file'] for r in u if not r['cov_path']][:10])
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--cores'); ap.add_argument('--stage1'); ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--json'); ap.add_argument('runs', nargs='+'); a = ap.parse_args()
    res, allrows, sets = {}, [], {}
    with Pool(a.jobs, initializer=init, initargs=(a.cores,)) as pool:
        for d in a.runs:
            rows, errs = [], 0
            for p, s in pool.imap_unordered(job, sorted(str(x) for x in Path(d).glob('inst-*.txt')), chunksize=100):
                if 'error' in s: errs += 1; continue
                s['file'] = p; rows.append(s)
            res[d] = summarize(rows); res[d]['parse_errors'] = errs; allrows += rows; sets[d] = {r['fp'] for r in rows}
    res['UNION'] = summarize(allrows)
    res['PAIRWISE_OVERLAP'] = {f'{Path(x).name}∩{Path(y).name}': len(sets[x] & sets[y]) for x, y in itertools.combinations(a.runs, 2)}
    txt = json.dumps(res, indent=1, default=str, ensure_ascii=False)
    if a.json: Path(a.json).write_text(txt)
    print(txt)
