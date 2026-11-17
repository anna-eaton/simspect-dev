#!/usr/bin/env python3
"""vp_lag.py (agent invisispec-fut 2026-11-16) -- read-only: InvisiSpec-Futuristic records where check_footprint's visibility point
(vp = first expose/validate of the seq, else its ROB-head tick; check_footprint.TraceModel.vp) is LATER than gem5's own visibility point
(the LSQ:safe hook, why=prev_insts_completed, lsq_unit_impl.hh:1110). Counts offending events (by any load actor) that fall in
[LSQ:safe, checker vp): footprints the checker flags although gem5 had already declared the load safe; and records whose ONLY offending
events are of that kind. Usage: python3 vp_lag.py --run <firstdet dir> --code <code root> --classes <classes.jsonl> --json out.json
"""
import argparse, collections, gzip, json, shutil, sys, tempfile
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ("--run", "--code", "--classes", "--json"):
    ap.add_argument(k, required=True)
A = ap.parse_args()
sys.path.insert(0, str(Path(A.code) / "STAGE3_gem5"))
import gem5_common as gc
cls = {(r["mode"], r["stem"]): r["sigs"] for r in map(json.loads, open(A.classes))}
res = {(r["mode"], r["stem"]): r for r in map(json.loads, open(Path(A.run) / "results.jsonl"))}
C = collections.Counter(); rows = []
for (mode, stem), sigs in cls.items():
    rawf = Path(A.run) / "raw" / mode / f"{stem}.json"
    gz = Path(A.run) / "traces" / mode / f"{stem}.pipeview.txt.gz"
    if not rawf.exists() or not gz.exists():
        continue
    raw = json.loads(rawf.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="futvp_"))
    try:
        tr = tmp / "pv.txt"
        with gzip.open(gz, "rb") as f, open(tr, "wb") as g:
            shutil.copyfileobj(f, g)
        evs = {e["id"]: e for e in gc.parse_simspect_events(tr)}
        safe = {}
        for e in evs.values():
            if e["struct"] == "LSQ" and e["kind"] == "safe" and e["seq"] is not None:
                safe.setdefault(e["seq"], e["tick"])
        n_all = n_lag = 0
        for o in raw.get("offending") or []:
            vp = o.get("vp") or {}
            for i in o.get("event_ids") or []:
                e = evs.get(i)
                if not e or e["seq"] is None:
                    continue
                n_all += 1
                s = safe.get(e["seq"]); v = (vp.get(str(e["seq"])) or [None])[0]
                if s is not None and e["tick"] >= s and (v is None or e["tick"] < v):
                    n_lag += 1
        key = (res[(mode, stem)].get("cache_setup"), "+".join(sorted(sigs)))
        C[key + ("records",)] += 1
        C[key + ("records_with_lag_events",)] += n_lag > 0
        C[key + ("records_ONLY_lag_events",)] += (n_lag == n_all and n_all > 0)
        rows.append(dict(mode=mode, stem=stem, sigs=sigs, n_offending_events=n_all, n_after_lsq_safe=n_lag))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
Path(A.json).write_text(json.dumps(dict(summary={"|".join(map(str, k)): v for k, v in C.items()}, rows=rows), indent=1))
for k, v in sorted(C.items()):
    print("|".join(map(str, k)), v)
