#!/usr/bin/env python3
"""evidence_keys.py -- write the "<mode>/<stem>" keys of a row's gated hits in the given static classes (default: every
class starting with "other", i.e. hits the static rules do not explain), optionally only one kind and skipping keys
already in an evidence JSON (regen-lp, 2026-11-10). Usage: evidence_keys.py --gate g.json --row R --out keys.txt
[--kind ld] [--classes other ...] [--skip evidence.json]"""
import argparse, json
ap = argparse.ArgumentParser(); ap.add_argument("--gate", required=True); ap.add_argument("--row", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--kind", default="ld"); ap.add_argument("--classes", nargs="*", default=["other"])
ap.add_argument("--skip"); a = ap.parse_args()
g = json.load(open(a.gate))["campaigns"][a.row]
skip = set(json.load(open(a.skip))) if a.skip else set()
keys = set()
for k, v in g.items():
    if k.endswith("_merge") or "examples" not in v:
        continue
    m, kind, rp = k.split("/")
    if a.kind and kind != a.kind:
        continue
    for cl, ex in v["examples"].items():
        if any(cl.startswith(c) for c in a.classes):
            keys |= {f"{m}/{s}" for s in ex}
new = sorted(keys - skip)
open(a.out, "w").write("\n".join(new) + "\n"); print(len(keys), "keys,", len(new), "new")
