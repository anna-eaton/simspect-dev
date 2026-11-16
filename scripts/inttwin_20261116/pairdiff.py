#!/usr/bin/env python3
"""pairdiff.py (agent inttwin 2026-11-16) -- prove an integer twin is faithful to its FPR corpus: for each (mode, stem) diff the
twin .s against the corpus .s and allow ONLY the FPR route lines (brief step 1):
  route        movq %out,%xmmK ; movq $0,%out ; movq %xmmK,%out           (after the load, FPR side only)
  direct       FPR `movq MEM,%xmmK` where the twin has `movq MEM,%out` (same MEM), + movq $0,%out ; movq %xmmK,%out
  *_alu        + pxor %xmmJ,%xmmJ ; por %xmmK,%xmmJ, copy-back from %xmmJ
Any other differing line (fillers, RMW, jmp, register choice, memory offset, branch) is reported as OTHER with the lines.
Also: number of route blocks == len(ann.fpr.routes) and their xmm registers match; twin ann has no 'fpr'; ann vocab_rj, xmit
(pc, kind), fanout_v2 record, branch annotation pcs and stl annotation pcs identical; the address fields are allowed to differ
(the route lines shift every later label: these are the "PC-label offsets").
Usage: pairdiff.py <fpr_corpus_dir> <int_corpus_dir> [--sample N | --frac F] [--seed S] [--json out.json] [--show 5]
Exit 1 if any pair has a disallowed difference.
"""
import argparse, difflib, hashlib, json, os, random, re, sys

MODES = ("mispredict_not_taken", "mispredict_taken", "stl_bypass")
X = r"%xmm(\d+)"; G = r"%(r\w+|e\w+)"
R_TOX = re.compile(rf"^movq\s+{G},\s*{X}$")        # movq %out, %xmmK
R_ZERO = re.compile(rf"^movq\s+\$0,\s*{G}$")        # movq $0, %out
R_BACK = re.compile(rf"^movq\s+{X},\s*{G}$")        # movq %xmmK, %out
R_PXOR = re.compile(rf"^pxor\s+{X},\s*{X}$")
R_POR = re.compile(rf"^por\s+{X},\s*{X}$")
R_DLD = re.compile(rf"^movq\s+(.*\(.*\)),\s*{X}$")  # movq MEM, %xmmK
R_GLD = re.compile(rf"^movq\s+(.*\(.*\)),\s*{G}$")  # movq MEM, %out


def norm(l):
    l = l.split("#", 1)[0].strip()
    return re.sub(r"\s+", " ", l)


def route_line(l):
    return bool(R_TOX.match(l) or R_ZERO.match(l) or R_BACK.match(l) or R_PXOR.match(l) or R_POR.match(l) or R_DLD.match(l))


def diff_s(fs, is_):
    F = [norm(l) for l in fs]; I = [norm(l) for l in is_]
    F = [l for l in F if l]; I = [l for l in I if l]
    other, routes = [], []
    cnt = dict(tox=0, dld=0, zero=0, back=0, pxor=0, por=0)
    for op, a0, a1, b0, b1 in difflib.SequenceMatcher(None, F, I, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        fl, il = F[a0:a1], I[b0:b1]
        # direct form: twin's `movq MEM,%out` <-> FPR `movq MEM,%xmmK`
        il_left = list(il)
        for l in fl:
            m = R_DLD.match(l)
            if m:
                for j, t in enumerate(il_left):
                    g = R_GLD.match(t)
                    if g and g.group(1) == m.group(1):
                        il_left.pop(j); break
        bad_f = [l for l in fl if not route_line(l)]
        if bad_f or il_left:
            other.append({"op": op, "fpr": fl, "int": il})
        else:
            routes += [int(R_BACK.match(l).group(1)) for l in fl if R_BACK.match(l)]
            for nm, rx in (("tox", R_TOX), ("dld", R_DLD), ("zero", R_ZERO), ("back", R_BACK), ("pxor", R_PXOR), ("por", R_POR)):
                cnt[nm] += sum(1 for l in fl if rx.match(l))
    return other, routes, cnt


def _strip_addr(v):
    if isinstance(v, dict):
        return {k: _strip_addr(x) for k, x in v.items() if "addr" not in k}
    if isinstance(v, list):
        return [_strip_addr(x) for x in v]
    return v


def ann_core(a):
    """every ann key except 'fpr', with every address field (key containing 'addr') removed recursively."""
    return {k: _strip_addr(v) for k, v in a.items() if k != "fpr" and "addr" not in k}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("fpr"); ap.add_argument("int"); ap.add_argument("--sample", type=int)
    ap.add_argument("--frac", type=float); ap.add_argument("--seed", default="inttwin-20261116"); ap.add_argument("--json"); ap.add_argument("--show", type=int, default=5)
    a = ap.parse_args()
    pairs = []
    for m in MODES:
        d = os.path.join(a.int, m, "asm")
        if os.path.isdir(d):
            pairs += [(m, f[:-2]) for f in sorted(os.listdir(d)) if f.endswith(".s")]
    stems = sorted({s for _, s in pairs})
    rnd = random.Random(a.seed)
    if a.sample:
        keep = set(rnd.sample(stems, min(a.sample, len(stems))))
    elif a.frac:
        keep = {s for s in stems if int(hashlib.sha256(f"{a.seed}:{s}".encode()).hexdigest()[:8], 16) / 2**32 < a.frac}
    else:
        keep = set(stems)
    pairs = [p for p in pairs if p[1] in keep]
    res = {"fpr": a.fpr, "int": a.int, "programs": len(keep), "pairs": len(pairs), "identical_s": 0, "route_only": 0, "bad": 0,
           "route_blocks": 0, "fpr_routes_ann": 0, "examples_bad": [], "ann_bad": 0, "ann_bad_examples": []}
    for m, s in pairs:
        fs = open(os.path.join(a.fpr, m, "asm", s + ".s")).read().splitlines()
        is_ = open(os.path.join(a.int, m, "asm", s + ".s")).read().splitlines()
        fa = json.load(open(os.path.join(a.fpr, m, "ann", s + ".ann.json")))
        ia = json.load(open(os.path.join(a.int, m, "ann", s + ".ann.json")))
        other, routes, cnt = diff_s(fs, is_)
        rts = (fa.get("fpr") or {}).get("routes", [])
        want = [r.get("alu_xmm", r["xmm"]) for r in rts]
        n_alu = sum(1 for r in rts if str(r.get("form", "route")).endswith("_alu"))
        n_dir = sum(1 for r in rts if str(r.get("form", "route")).startswith("direct"))
        if not (cnt["zero"] == cnt["back"] == len(rts) and cnt["tox"] + cnt["dld"] == len(rts) and cnt["dld"] == n_dir
                and cnt["pxor"] == cnt["por"] == n_alu):
            other.append({"op": "count", "counts": cnt, "routes": len(rts), "alu": n_alu, "direct": n_dir})
        res["route_blocks"] += len(routes); res["fpr_routes_ann"] += len(want)
        prob = []
        if other:
            prob.append("OTHER lines")
        if sorted(routes) != sorted(want):
            prob.append(f"route blocks {sorted(routes)} != ann.fpr.routes {sorted(want)}")
        if "fpr" in ia:
            prob.append("twin ann has fpr")
        ca, cb = ann_core(fa), ann_core(ia)
        if ca != cb:
            res["ann_bad"] += 1
            if len(res["ann_bad_examples"]) < a.show:
                res["ann_bad_examples"].append({"pair": f"{m}/{s}", "diff_keys": [k for k in ca if ca[k] != cb[k]]})
            prob.append("ann core differs: " + ",".join(k for k in ca if ca[k] != cb[k]))
        if prob:
            res["bad"] += 1
            if len(res["examples_bad"]) < a.show:
                res["examples_bad"].append({"pair": f"{m}/{s}", "problems": prob, "other": other[:4]})
        elif fs == is_:
            res["identical_s"] += 1
        else:
            res["route_only"] += 1
    print(json.dumps({k: v for k, v in res.items() if not k.startswith("examples") and k != "ann_bad_examples"}))
    for e in res["examples_bad"]:
        print("BAD", json.dumps(e)[:1500])
    for e in res["ann_bad_examples"]:
        print("ANN", json.dumps(e))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    sys.exit(1 if res["bad"] else 0)


if __name__ == "__main__":
    main()
