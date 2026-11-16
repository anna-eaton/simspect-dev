#!/usr/bin/env python3
"""Read-only scan: find tests in a two-stage testset whose Alloy instance has the Fig. 2 chain
(unresolved Branchn before an uncommitted Load L; ddi L.inmem->L.outreg; rf L.outreg -> Othern O.inreg;
rf O.outreg -> xmit Load inaddr), then report per mode: xmm in the asm between L's label and the xmit,
jmp_insert, filler count, RMW, instruction count. Usage: scan_fig2_chain.py <testset_root> > out.tsv"""
import sys, os, re, json, glob
root = sys.argv[1]
def rel(txt, name):
    m = re.search(r'^this/Instruction<:%s=\{(.*)\}$' % name, txt, re.M) or re.search(r'^this/Operand<:%s=\{(.*)\}$' % name, txt, re.M)
    if not m or not m.group(1).strip(): return []
    return [tuple(p.strip().split('->')) for p in m.group(1).split(',')]
print('\t'.join(['stem','mode','n_instr','L_pc','O_pc','X_pc','O_ninreg','xmm_in_chain','xmm_any_pc','jmp_insert','n_fillers','fpr_routes','rmw','routes']))
for f in sorted(glob.glob(os.path.join(root, 'xml', 'inst-*.txt'))):
    stem = os.path.basename(f)[:-4]
    t = open(f).read()
    kind = dict(rel(t, 'kind')); idx = {a: int(b[2]) for a, b in rel(t, 'idx')}
    res = {a for a, _ in rel(t, 'isresolved')}; com = {a for a, _ in rel(t, 'iscommitted')}
    xm = [a for a, _ in rel(t, 'isxm')]
    if len(xm) != 1 or not kind.get(xm[0], '').startswith('TLoad'): continue
    X = xm[0]
    inreg = rel(t, 'inreg'); inaddr = dict(rel(t, 'inaddr')); outreg = dict(rel(t, 'outreg')); inmem = dict(rel(t, 'inmem'))
    rf = set(rel(t, 'rf')); ddi = set(rel(t, 'ddi'))
    owner_in = {}
    for i, op in inreg: owner_in.setdefault(op, i)
    hit = None
    for O, oo in outreg.items():
        if not kind[O].startswith('TOthern') or (oo, inaddr.get(X)) not in rf: continue
        for L, lo in outreg.items():
            if not kind[L].startswith('TLoad') or L in com or (inmem.get(L), lo) not in ddi: continue
            for op in [o for i, o in inreg if i == O]:
                if (lo, op) in rf and (op, oo) in ddi:
                    br = [b for b in kind if kind[b].startswith('TBranchn') and b not in res and idx[b] < idx[L]]
                    if br and idx[L] < idx[O] < idx[X]: hit = (L, O)
    if not hit: continue
    L, O = hit
    for mode in ('mispredict_not_taken', 'mispredict_taken'):
        s = os.path.join(root, mode, 'asm', stem + '.s'); a = os.path.join(root, mode, 'ann', stem + '.ann.json')
        if not (os.path.exists(s) and os.path.exists(a)): continue
        lines = open(s).read().splitlines(); ann = json.load(open(a))
        def lab(pc):
            for k, l in enumerate(lines):
                if l.strip() == '__litmus_%s_pc%d:' % (stem.replace('-', '_'), pc): return k
            return None
        lk, xk = lab(idx[L]), lab(idx[X])
        chain = lines[lk:xk + 2] if lk is not None and xk is not None else []
        xmm_chain = any('xmm' in l for l in chain)
        p0 = lab(0); xmm_any = any('xmm' in l for l in lines[p0:xk + 2]) if p0 is not None and xk is not None else None
        fv = ann.get('fanout_v2', {}) or {}
        nf = len(fv.get('fillers', []) or [])
        rts = (ann.get('fpr', {}) or {}).get('routes', []) or []; fr = len(rts)
        rd = ';'.join('pc%s:xmm%s:%s%s' % (r.get('pc'), r.get('xmm'), r.get('form'), (':alu%s' % r['alu_xmm']) if 'alu_xmm' in r else '') for r in rts)
        rmw = 'rmw' in json.dumps(ann).lower() and bool(ann.get('rmw'))
        print('\t'.join(map(str, [stem, mode, len(kind), idx[L], idx[O], idx[X], sum(1 for i, _ in inreg if i == O), xmm_chain, xmm_any, bool(ann.get('jmp_insert')), nf, fr, rmw, rd])))
