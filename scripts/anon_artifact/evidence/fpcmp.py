import json, os
res = {}
for r in ("T1g", "T2g", "T3g"):
    new = {(x["mode"], x["stem"]): x for x in map(json.loads, open(f"/tmp/anonchk/out/{r}/results.jsonl"))}
    old = {}
    for l in open(f"/tests/timing_20261115/simspect/{r}_p16/results.jsonl"):
        x = json.loads(l)
        if (x["mode"], x["stem"]) in new:
            old[(x["mode"], x["stem"])] = x
    keys = ["verdict", "issued_in_window", "cache_setup", "stall_points", "status", "kind", "error"]
    same = diff = 0; ex = []
    rawsame = rawn = 0
    for k, x in new.items():
        o = old.get(k)
        if o is None:
            ex.append(("missing_old", k)); continue
        a = {kk: x.get(kk) for kk in keys}; b = {kk: o.get(kk) for kk in keys}
        if a == b: same += 1
        else: diff += 1; ex.append((k, {kk: (b[kk], a[kk]) for kk in keys if a[kk] != b[kk]}))
        pn = f"/tmp/anonchk/out/{r}/raw/{k[0]}/{k[1]}.json"; po = f"/tests/timing_20261115/simspect/{r}_p16/raw/{k[0]}/{k[1]}.json"
        if os.path.exists(pn) and os.path.exists(po):
            rawn += 1
            A = json.load(open(pn)); B = json.load(open(po))
            drop = ("workdir", "elapsed", "cpu", "wall", "time")
            f = lambda d: {kk: v for kk, v in d.items() if not any(s in kk for s in drop)} if isinstance(d, dict) else d
            rawsame += (f(A) == f(B))
    res[r] = dict(compared=len(new), same=same, diff=diff, raw_compared=rawn, raw_identical=rawsame, examples=ex[:3])
print(json.dumps(res, indent=1, default=str))
