import json, re, sys, hashlib, collections, itertools
from pathlib import Path
from multiprocessing import Pool
WS = Path('/tests/simspect_alloy_20261108')
sys.path.insert(0, str(WS/'STAGE1_alloy'))
import stage_seed
SLOTS = ['inreg','inaddr','inmem','outreg','outmem']
def corefp(path):
    r = stage_seed.parse_txt(str(path)); col = lambda n: r.get(n, [])
    instrs = [a for (a,) in col('Instruction')]; nxt = dict(col('Instruction<:spo'))
    cur = [i for i in instrs if i not in nxt.values()][0]; order = []
    while cur: order.append(cur); cur = nxt.get(cur)
    pc = {i:n for n,i in enumerate(order)}
    kind = {i:k.split('$')[0] for i,k in col('Instruction<:kind')}
    res = {i for i,_ in col('Instruction<:isresolved')}; com = {i for i,_ in col('Instruction<:iscommitted')}; xm = {i for i,_ in col('Instruction<:isxm')}
    ops = collections.defaultdict(list)
    for s in SLOTS:
        for i,o in col(f'Instruction<:{s}'): ops[i].append((s,o))
    st = dict(col('Operand<:opstate')); rf = col('Operand<:rf'); ddi = col('Operand<:ddi')
    per = []
    for i in order:
        g = collections.defaultdict(list)
        for s,o in ops[i]: g[s].append(o)
        keys = sorted(g); per.append([dict(zip(keys,ch)) for ch in itertools.product(*[list(itertools.permutations(g[k])) for k in keys])])
    best = None
    for combo in itertools.product(*per):
        name = {}
        for i,d in zip(order,combo):
            for s,l in d.items():
                for k,o in enumerate(l): name[o] = (pc[i],s,k)
        canon = {}; rows = []
        for i in order:
            sl = []
            for o,nm in sorted(((o,name[o]) for s,o in ops[i]), key=lambda x:x[1]):
                s = st.get(o); sl.append((nm[1],nm[2], None if s is None else canon.setdefault(s,(s.split('_')[0],len(canon)))))
            rows.append((kind[i], i in res, i in com, i in xm, tuple(sl)))
        t = repr((tuple(rows), tuple(sorted((name[a],name[b]) for a,b in rf)), tuple(sorted((name[a],name[b]) for a,b in ddi))))
        if best is None or t < best: best = t
    return best, len(order)

def merge_stats(fam, corefam, ws=WS):
    print(f'\n=== {fam} (cores {corefam}) ===')
    v = collections.Counter(); inst = {}
    for l in (ws/'s15'/fam/'results.jsonl').read_text().splitlines():
        r = json.loads(l); v[r['verdict']] += 1; inst[r['key']] = (r['instances'], r['verdict'], r['secs'])
    print('verdicts', dict(v), 'per_core', json.loads((ws/'s15'/fam/'PROVENANCE.json').read_text())['per_core'])
    cf = {}
    for p in sorted((ws/'out'/corefam).glob('*/stage1_xml/inst-*.txt')):
        cf[f'{p.parent.parent.name}__{p.stem}'] = corefp(p)
    print('cores', len(cf), 'canonically distinct', len({a for a,_ in cf.values()}), 'sizes', dict(collections.Counter(n for _,n in cf.values())))
    T = Path(ws/'testsets_twostage'/fam) if (ws/'testsets_twostage'/fam).exists() else WS/'testsets_twostage'/fam
    name2core = {}; kept = collections.Counter()
    for l in open(T/'merge_map.jsonl'):
        r = json.loads(l); name2core[r['name']] = r['core']; kept[r['core']] += 1
    dup_same = dup_diff = 0; mult = collections.Counter()
    for l in open(T/'merge_dups.jsonl'):
        r = json.loads(l); c = Path(r['source']).parent.name; k = name2core[r['duplicate_of']]
        mult[r['duplicate_of']] += 1
        if cf[c][0] == cf[k][0]: dup_same += 1
        else: dup_diff += 1
    print('kept', sum(kept.values()), 'dups', dup_same+dup_diff, ': copy of an instance kept from a canonically IDENTICAL core', dup_same, '; from a different core', dup_diff)
    h = collections.Counter(min(m+1, 10) for m in mult.values()); h[1] = sum(kept.values()) - len(mult)
    print('copies per distinct instance (10 = 10+):', dict(sorted(h.items())))
    order = sorted(cf); fr = [(kept[c], inst.get(c,(0,))[0]) for c in order]
    print('cores that kept 0 new instances:', sum(1 for k,_ in fr if k == 0), '; kept<10%:', sum(1 for k,n in fr if n and k < 0.1*n))
    print('kept/produced for the first 12 and last 12 cores in merge order:', fr[:12], fr[-12:])
    ex = [(c, inst[c][0]) for c in order if c in inst and inst[c][1] == 'EXHAUSTED']
    print('EXHAUSTED cores:', len(ex), 'instances min/median/max', (min(n for _,n in ex), sorted(n for _,n in ex)[len(ex)//2], max(n for _,n in ex)) if ex else None)

RX = re.compile(r'inst[-_]\d{6}(?:_v\d+)?')
def h_asm(p):
    p = Path(p); s = p.read_text(errors='replace')
    s = '\n'.join(l for l in RX.sub('X', s).splitlines() if not l.lstrip().startswith(('.file','.ident','#')))
    a = p.parent.parent/'ann'/(p.stem+'.ann.json')
    at = RX.sub('X', a.read_text()) if a.exists() else ''
    return hashlib.md5(s.encode()).hexdigest(), hashlib.md5((s+at).encode()).hexdigest()
def asm_stats(ts, mode='mispredict_not_taken'):
    files = sorted(str(x) for x in (WS/'testsets_twostage'/ts/mode/'asm').glob('*.s'))
    with Pool(12) as pool: hs = pool.map(h_asm, files, chunksize=500)
    print(f'\nasm {ts}/{mode}: {len(files)} tests; distinct asm text {len({a for a,_ in hs})}; distinct (asm+ann) {len({b for _,b in hs})}')

if __name__ == '__main__':
    merge_stats('STT_6', 'STT_6_core_ri')
    merge_stats('STT_6_stl', 'STT_6_stl_core')
    for ts in ('STT_6_fv2', 'Recon_6_u_base', 'STT_6_u_fv2'):
        try: asm_stats(ts)
        except Exception as e: print('asm', ts, 'ERR', repr(e))
    fp = {}
    for fam in ('STT_6','STT_6_u','Recon_6_u'):
        fp[fam] = {json.loads(l)['fp'] for l in open(WS/'testsets_twostage'/fam/'merge_map.jsonl')}
    print('\nXML fingerprint overlap: STT_6∩STT_6_u', len(fp['STT_6']&fp['STT_6_u']), 'of', len(fp['STT_6']), len(fp['STT_6_u']), '; STT_6_u∩Recon_6_u', len(fp['STT_6_u']&fp['Recon_6_u']), 'of', len(fp['STT_6_u']), len(fp['Recon_6_u']))
