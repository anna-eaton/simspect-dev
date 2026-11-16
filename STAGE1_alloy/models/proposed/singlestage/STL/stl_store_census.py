#!/usr/bin/env python3
"""stl_store_census.py — read-only STL supplement to ../tools/census_flat.py (singlestage-stl agent, 2026-11-09).
census_flat's unresolved_brs_hist counts branches only; in the STL models every branch is resolved
(fact stl_no_unresolved_branches), so the speculation source is the unresolved-address STORE. Per run dir and for
the union, over DISTINCT programs (census_flat.fingerprint, imported unchanged), this reports:
  unresolved_strs_hist         unresolved stores per program
  unresolved_strs_before_xm    unresolved stores strictly before the transmitter in program order
  stores_hist                  all stores per program
  alias_pairs_hist             (unresolved store, younger load at or before xm) pairs naming the same Mem_s atom
                               (opstate), i.e. the Recon_6_stl atom-based alias; an rf-edge pair also counts
Usage: stl_store_census.py [--jobs 8] [--json OUT] RUN_DIR [RUN_DIR ...]
"""
import argparse, collections, json, sys
from multiprocessing import Pool
from pathlib import Path
for _d in (Path(__file__).resolve().parent.parent / 'tools', Path(__file__).resolve().parents[2] / 'tools'):  # repo layout, cafe2 layout
    if (_d / 'census_flat.py').exists(): sys.path.insert(0, str(_d)); break
import census_flat as cf  # noqa: E402  (read-only import; tools/ is not edited)

def job(p):
    try:
        F = cf.load(p); xm = next(iter(F['xm']), None)
        st = [i for i in F['order'] if F['kind'][i] == 'TStore']
        ust = [i for i in st if i not in F['res']]
        before = [i for i in ust if xm and F['pos'][i] < F['pos'][xm]]
        pairs = 0
        for s in ust:
            souts = F['ops'].get((s, 'outmem'), [])
            sst = {F['st'].get(o) for o in souts} - {None}
            for l in F['order']:
                if F['kind'][l] != 'TLoad' or not xm or not (F['pos'][s] < F['pos'][l] <= F['pos'][xm]): continue
                lin = F['ops'].get((l, 'inmem'), [])
                if ({F['st'].get(o) for o in lin} & sst) or any((o, q) in F['rf'] for o in souts for q in lin): pairs += 1
        return p, dict(fp=cf.fingerprint(F), stores=len(st), ustores=len(ust), ubefore=len(before), pairs=pairs)
    except Exception as e:
        return p, {'error': repr(e)}

def summ(rows):
    u = {}
    for r in rows: u.setdefault(r['fp'], r)
    u = list(u.values()); H = lambda k: dict(sorted(collections.Counter(r[k] for r in u).items()))
    return dict(instances=len(rows), distinct=len(u), unresolved_strs_hist=H('ustores'), unresolved_strs_before_xm_hist=H('ubefore'),
                stores_hist=H('stores'), alias_pairs_hist=H('pairs'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--jobs', type=int, default=8); ap.add_argument('--json'); ap.add_argument('runs', nargs='+')
    a = ap.parse_args(); res, allrows = {}, []
    with Pool(a.jobs) as pool:
        for d in a.runs:
            rows, errs = [], 0
            for p, s in pool.imap_unordered(job, sorted(str(x) for x in Path(d).glob('inst-*.txt')), chunksize=100):
                if 'error' in s: errs += 1; continue
                rows.append(s)
            res[d] = summ(rows); res[d]['parse_errors'] = errs; allrows += rows
    res['UNION'] = summ(allrows)
    txt = json.dumps(res, indent=1)
    if a.json: Path(a.json).write_text(txt)
    print(txt)
