#!/usr/bin/env python3
"""residue_profile.py (agent invisispec-fut 2026-11-16) -- read-only: describe every InvisiSpec record whose classes are only other_*
(the unexplained residue): per offending event (struct, kind, req) and its actor: the transmitter, a load micro-op with a pipeview
record, or an actor with no pipeview record (op class unknown, kept by W-3), and the actor's checker vp basis. Lists, never filters.
Usage: python3 residue_profile.py --run <firstdet dir> --code <code root> --classes <classes.jsonl> --json out.json
"""
import argparse, collections, gzip, json, shutil, sys, tempfile
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ("--run", "--code", "--classes", "--json"):
    ap.add_argument(k, required=True)
A = ap.parse_args()
sys.path.insert(0, str(Path(A.code) / "STAGE3_gem5"))
import gem5_common as gc
C = collections.Counter(); per = collections.Counter(); rows = []
for r in map(json.loads, open(A.classes)):
    if not r["sigs"] or not all(s.startswith("other_") for s in r["sigs"]):
        continue
    mode, stem = r["mode"], r["stem"]
    raw = json.loads((Path(A.run) / "raw" / mode / f"{stem}.json").read_text())
    tmp = Path(tempfile.mkdtemp(prefix="futres_"))
    try:
        tr = tmp / "pv.txt"
        with gzip.open(Path(A.run) / "traces" / mode / f"{stem}.pipeview.txt.gz", "rb") as f, open(tr, "wb") as g:
            shutil.copyfileobj(f, g)
        evs = {e["id"]: e for e in gc.parse_simspect_events(tr)}
        pv = gc.parse_pipeview_by_seq(tr)
        xpc = int(raw["xmit_pc"], 16) if raw.get("xmit_pc") else None
        kinds = set()
        for o in raw.get("offending") or []:
            vp = o.get("vp") or {}
            for i in o.get("event_ids") or []:
                e = evs.get(i)
                if not e:
                    continue
                q = pv.get(e["seq"])
                actor = "no_pipeview_record" if q is None else ("transmitter" if q["pc"] == xpc else
                        ("load_retired" if q["retire"] else "load_squashed"))
                basis = (vp.get(str(e["seq"])) or [None, None])[1]
                key = f"{e['struct']}:{e['kind']}:req={e.get('req')}|{actor}|vp={basis}"
                C[key] += 1; kinds.add(key)
        for k in kinds:
            per[k] += 1
        rows.append(dict(mode=mode, stem=stem, sigs=r["sigs"], cache_setup=raw.get("cache_setup"), event_kinds=sorted(kinds)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
Path(A.json).write_text(json.dumps(dict(n_records=len(rows), records_with_kind=dict(per), events=dict(C), rows=rows), indent=1))
print("records", len(rows))
for k, v in per.most_common(25):
    print(f"{v:6d} records  {C[k]:7d} events  {k}")
