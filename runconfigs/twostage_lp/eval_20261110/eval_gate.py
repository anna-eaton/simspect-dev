#!/usr/bin/env python3
"""eval_gate.py -- gated hit rates for the testrun.py campaigns of campaigns.json (regen-lp, 2026-11-10).

Per campaign / mode / transmitter kind, from the raw per-record checker output (<campaign>/<mode>/_sweep_raw/*.json):
  raw hit   = issued_in_window (what window-results.json counts);
  gate      = check_ld's canonical data-obtained gate (CLAUDE.md "Leak criteria"; same rule as classify_hits.py's STT
              gate): a hit whose record has data_obtained == False is disq_not_obtained(<cache_fate>), not a leak;
              data_obtained None (br_x, or no LSQ record) stays ungated;
  RMW split = transmitter test listed in the corpus rmw_stems.tsv for that mode;
  S1_xmm4   = (STT builds, E3/E4) the transmitter's backward register slice touches %xmm4
              (triage/diag/_fv2_slice.transmitter_slice, the static half of diag_stt_xmm4_skip.py, as classify_hits.py);
  R-SA-13_static = (Recon builds, E2/E6) the slice ends at a direct SSE load: the static half of diag_recon_sse_load_producer.py
              (its twin / rerun-evidence half is not run here, so this is a candidate class, not an attribution);
  other     = the rest of the gated hits (unexplained here), with example stems.
Restricted to the nested sample_keep(stem, --fraction) subset. Run from the code root.
Usage: eval_gate.py [--fraction 0.02] [--names ...] [--json out] [--examples 3]"""
import argparse, collections, glob, json, os, sys
sys.path.insert(0, "STAGE3_gem5"); sys.path.insert(0, "STAGE3_gem5/triage/diag")
from gem5_common import sample_keep
import _fv2_slice as fs
ap = argparse.ArgumentParser(); ap.add_argument("--fraction", type=float, default=1.0); ap.add_argument("--names", nargs="*")
ap.add_argument("--json"); ap.add_argument("--examples", type=int, default=3); a = ap.parse_args()
camps = json.load(open("runconfigs/twostage_lp/eval_20261110/campaigns.json"))
OUT = {}
for c in camps:
    n = c["results_name"]
    if "_sh" in n.split("_fv3")[-1]:
        continue
    if a.names and n not in a.names:
        continue
    dirs = [os.path.realpath(x) for x in [f"results/{n}__latest"] + sorted(glob.glob(f"results/{n}_sh*__latest"))]
    dirs = [x for x in dirs if os.path.isdir(x)]
    if not dirs:
        continue
    ts = os.path.join("/tests/simspect_alloy_20261108/testsets_twostage", c["model"])
    stt = n.split("_")[0] in ("E3", "E4")
    rmw = collections.defaultdict(set)
    for l in open(os.path.join(ts, "rmw_stems.tsv")).read().splitlines()[1:]:
        p = l.split("\t")
        if len(p) > 1:
            rmw[p[0]].add(p[1])
    res = {}
    for mode in ("mispredict_not_taken", "mispredict_taken"):
        recs, owner, dups = {}, {}, set()
        for d in dirs:   # main campaign + shard runs (shard_eval.py); a stem in two runs is a duplicate (reported)
            for f in sorted(glob.glob(os.path.join(d, mode, "_sweep_raw", "*.json"))):
                try:
                    x = json.load(open(f))
                except Exception:
                    continue
                for r in (x if isinstance(x, list) else []):
                    if isinstance(r, dict) and r.get("name"):
                        st = r["name"].split("__")[0]
                        if owner.get(st, d) != d:
                            dups.add(st)
                        owner[st] = d; recs[st] = r
        exp = {f[:-9] for f in os.listdir(os.path.join(ts, mode, "ann")) if a.fraction >= 1 or sample_keep(f[:-9], a.fraction)}
        miss = sorted(exp - set(recs))
        res.setdefault(f"{mode}/_merge", dict(runs=len(dirs), stems=len(recs), duplicates=len(dups), duplicate_examples=sorted(dups)[:5],
                                              expected=len(exp), missing=len(miss), missing_examples=miss[:5]))
        for s, r in recs.items():
            if not isinstance(r, dict):
                continue
            if a.fraction < 1 and not sample_keep(s, a.fraction):
                continue
            kind = r.get("xmit_kind") or "?"
            isr = s in rmw[mode]
            key = f"{mode}/{kind}/{'rmw' if isr else 'plain'}"
            e = res.setdefault(key, dict(tests=0, raw_hits=0, gated_hits=0, classes=collections.Counter(), examples={}))
            e["tests"] += 1
            if not r.get("issued_in_window"):
                continue
            e["raw_hits"] += 1
            if r.get("data_obtained") is False:
                cl = f"disq_not_obtained({r.get('cache_fate')})"
            else:
                e["gated_hits"] += 1
                cl = "other"
                sl = fs.transmitter_slice(s, __import__("pathlib").Path(ts) / mode)
                if sl.get("err"):
                    cl = "other(slice_err)"
                elif stt:
                    cl = "S1_xmm4" if sl["xmm4"] else "other"
                else:   # Recon-group builds (E2, E6): static half of diag_recon_sse_load_producer (R-SA-13) only
                    cl = ("R-SA-13_static(SSE-load producer)" if sl.get("sse_producer")
                          else "other(xmm on slice)" if sl.get("xmms") else "other(GPR slice)")
            e["classes"][cl] += 1
            if len(e["examples"].setdefault(cl, [])) < a.examples:
                e["examples"][cl].append(s)
    OUT[n] = {k: (dict(v, classes=dict(v["classes"])) if "classes" in v else v) for k, v in sorted(res.items())}
for n, v in OUT.items():
    print(f"== {n}")
    for k, e in v.items():
        if k.endswith("/_merge"):
            print(f"  {k:42} runs {e['runs']}  stems {e['stems']} / expected {e['expected']}  MISSING {e['missing']} {e['missing_examples']}  DUPLICATES {e['duplicates']} {e['duplicate_examples']}"); continue
        print(f"  {k:42} tests {e['tests']:5}  raw {e['raw_hits']:4}  gated {e['gated_hits']:4}  {e['classes']}")
        for cl, ex in e["examples"].items():
            if not cl.startswith("disq"):
                print(f"      {cl}: {ex}")
if a.json:
    json.dump(dict(fraction=a.fraction, campaigns=OUT), open(a.json, "w"), indent=1)
