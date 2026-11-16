#!/usr/bin/env python3
"""eval_summary.py -- per campaign / mode / transmitter kind: tests, errors and raw checker hits (issued_in_window) of
the testrun.py campaigns in campaigns.json, optionally restricted to the nested sample_keep(stem, F) subset
(regen-lp, 2026-11-10). Run from the code root. Usage: eval_summary.py [--fraction 0.02] [--names E2_... ...] [--json out]"""
import argparse, glob, json, os, sys
sys.path.insert(0, "STAGE3_gem5")
from gem5_common import sample_keep
ap = argparse.ArgumentParser(); ap.add_argument("--fraction", type=float, default=1.0); ap.add_argument("--names", nargs="*")
ap.add_argument("--json"); a = ap.parse_args()
camps = json.load(open("runconfigs/twostage_lp/eval_20261110/campaigns.json"))
out = {}
for c in camps:
    n = c["results_name"]
    if a.names and n not in a.names:
        continue
    d = os.path.realpath(f"results/{n}__latest")
    if not os.path.isdir(d):
        continue
    out[n] = {}
    for wr in sorted(glob.glob(d + "/mispredict_*/*/window-results.json")):
        mode, kind = wr.split("/")[-3], wr.split("/")[-2]
        x = json.load(open(wr)); recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
        per = {}
        for r in recs:
            if not isinstance(r, dict):
                continue
            s = r["name"].split("__")[0]
            if a.fraction < 1 and not sample_keep(s, a.fraction):
                continue
            p = per.setdefault(s, dict(hit=False, err=False))
            p["hit"] |= bool(r.get("issued_in_window")); p["err"] |= r.get("status") not in (None, "ok")
        out[n][f"{mode}/{kind}"] = dict(tests=len(per), hits=sum(v["hit"] for v in per.values()), errors=sum(v["err"] for v in per.values()))
for n, v in out.items():
    print(n, " | ".join(f"{k}: {x['hits']}/{x['tests']}" + (f" err {x['errors']}" if x['errors'] else "") for k, x in v.items()))
if a.json:
    json.dump(dict(fraction=a.fraction, campaigns=out), open(a.json, "w"), indent=1)
