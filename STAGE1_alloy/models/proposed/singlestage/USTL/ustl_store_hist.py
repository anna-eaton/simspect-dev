#!/usr/bin/env python3
"""ustl_store_hist.py — read-only companion to tools/census_flat.py for the STL flavor (agent singlestage-ustl,
2026-11-09). census_flat's unresolved_brs_hist counts unresolved BRANCHES only; in the stl flavor branches are
forced resolved (fact u_stl_no_branch_speculation) and the speculation source is an unresolved-ADDRESS STORE.
This reports, per run dir and for the union, over DISTINCT programs (the same isomorphism fingerprint census_flat
uses, imported from it unchanged):
  unresolved_stores_hist    # of unresolved stores per program
  unresolved_brs_hist       (sanity: must be {0: n} in the stl flavor)
Usage: ustl_store_hist.py --tools <dir with census_flat.py> [--jobs 8] [--json OUT] RUN_DIR [RUN_DIR ...]"""
import argparse, collections, json, sys
from multiprocessing import Pool
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--tools", required=True); ap.add_argument("--jobs", type=int, default=8)
ap.add_argument("--json"); ap.add_argument("runs", nargs="+"); a = ap.parse_args()
sys.path.insert(0, a.tools)
import census_flat as C  # noqa: E402  (read-only reuse of load + fingerprint)
def job(p):
    try:
        F = C.load(p)
        ust = sum(1 for i in F["order"] if i not in F["res"] and F["kind"][i] == "TStore")
        ubr = sum(1 for i in F["order"] if i not in F["res"] and F["kind"][i] in ("TBranchn", "TBranchx"))
        return C.fingerprint(F), ust, ubr
    except Exception as e:
        return None, repr(e), None
def summ(rows):
    d = {}
    for fp, u, b in rows: d.setdefault(fp, (u, b))
    return dict(instances=len(rows), distinct=len(d),
                unresolved_stores_hist=dict(sorted(collections.Counter(u for u, _ in d.values()).items())),
                unresolved_brs_hist=dict(sorted(collections.Counter(b for _, b in d.values()).items())))
if __name__ == "__main__":
    res, allrows = {}, []
    with Pool(a.jobs) as pool:
        for d in a.runs:
            rows, errs = [], 0
            for fp, u, b in pool.imap_unordered(job, sorted(str(x) for x in Path(d).glob("inst-*.txt")), chunksize=100):
                if fp is None: errs += 1; continue
                rows.append((fp, u, b))
            res[d] = summ(rows); res[d]["parse_errors"] = errs; allrows += rows
    res["UNION"] = summ(allrows)
    t = json.dumps(res, indent=1)
    if a.json: Path(a.json).write_text(t)
    print(t)
