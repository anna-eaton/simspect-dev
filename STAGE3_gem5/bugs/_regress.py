#!/usr/bin/env python3
"""_regress.py: record-by-record regression of bugs/classify.py against the old classifiers' outputs.

  _regress.py classes  <old classes(.rmw).jsonl> <new classes(.rmw).jsonl>        per-idx sigs (and items' causes)
  _regress.py evidence <old cleanupspec_skip_evidence.json> <new ...json>          per-key causes, per-item causes,
                                                                                  `inconsistent` flips (DG-3)
  _regress.py gate     <old gate json> <new gate json>                            whole JSON equality, per key diff
  _regress.py bucket   <old buckets json> <new buckets json>                      per key bucket counts + examples
Prints per-signature counts old vs new and every record whose label changed; exit 1 on any label change.
"""
import collections, gzip, json, sys


def _jl(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def classes(old, new):
    O = {r["idx"]: r for r in _jl(old)}
    N = {r["idx"]: r for r in _jl(new)}
    co, cn = collections.Counter(), collections.Counter()
    for r in O.values():
        co.update(r["sigs"])
    for r in N.values():
        cn.update(r["sigs"])
    print(f"records old {len(O)} new {len(N)}")
    print(f"{'signature':45} {'old':>7} {'new':>7}")
    for s in sorted(set(co) | set(cn)):
        print(f"{s:45} {co[s]:7} {cn[s]:7}{'' if co[s] == cn[s] else '   <-- DIFF'}")
    bad = 0
    for i in sorted(set(O) | set(N)):
        a, b = O.get(i), N.get(i)
        if a is None or b is None or sorted(a["sigs"]) != sorted(b["sigs"]) or \
                (a.get("stem"), a.get("mode")) != (b.get("stem"), b.get("mode")):
            bad += 1
            if bad <= 40:
                print("CHANGED", i, a and (a["mode"], a["stem"], a["sigs"]), "->", b and (b["mode"], b["stem"], b["sigs"]))
            continue
        if "items" in a:
            ca = sorted(x["cause"] for x in a["items"])
            cb = sorted(x["cause"] for x in b.get("items", []))
            if ca != cb:
                bad += 1
                if bad <= 40:
                    print("ITEMS CHANGED", i, a["stem"], ca, "->", cb)
    print(f"records with a changed label: {bad}")
    return bad


def evidence(old, new):
    O, N = json.load(open(old)), json.load(open(new))
    bad, flips = 0, []
    for k in sorted(set(O) | set(N)):
        a, b = O.get(k), N.get(k)
        if a is None or b is None or a["causes"] != b["causes"]:
            bad += 1
            print("CAUSES CHANGED", k, a and a["causes"], "->", b and b["causes"])
            continue
        ia = [[i["cause"] for i in v["items"]] for v in a["variants"]]
        ib = [[i["cause"] for i in v["items"]] for v in b["variants"]]
        if ia != ib:
            bad += 1
            print("ITEM CAUSES CHANGED", k, ia, "->", ib)
        fa = [v.get("inconsistent") for v in a["variants"]]
        fb = [v.get("inconsistent") for v in b["variants"]]
        if fa != fb:
            flips.append((k, fa, fb, a["causes"]))
    print(f"keys old {len(O)} new {len(N)}; changed causes {bad}; inconsistent flag changes {len(flips)}")
    for f in flips:
        print("  INCONSISTENT FLIP", *f)
    return bad


def gate(old, new):
    O, N = json.load(open(old)), json.load(open(new))
    bad = 0
    for row in sorted(set(O["campaigns"]) | set(N["campaigns"])):
        a, b = O["campaigns"].get(row, {}), N["campaigns"].get(row, {})
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                bad += 1
                print("DIFF", row, k, json.dumps(a.get(k))[:300], "->", json.dumps(b.get(k))[:300])
    print(f"gate keys differing: {bad}")
    return bad


def bucket(old, new):
    O, N = json.load(open(old))["buckets"], json.load(open(new))["buckets"]
    bad = 0
    for k in sorted(set(O) | set(N)):
        a, b = O.get(k), N.get(k)
        if a != b:
            bad += 1
            print("DIFF", k, json.dumps(a and a.get("buckets")), "->", json.dumps(b and b.get("buckets")))
    print(f"bucket keys differing: {bad} of {len(O)}")
    return bad


if __name__ == "__main__":
    fn = {"classes": classes, "evidence": evidence, "gate": gate, "bucket": bucket}[sys.argv[1]]
    sys.exit(1 if fn(sys.argv[2], sys.argv[3]) else 0)
