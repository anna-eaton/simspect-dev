#!/usr/bin/env python3
"""pin_contains.py -- empirical non-vacuity check of the Stage-1 core pin (regen-lp, 2026-11-10).

Re-implements, in Python, what the path-style seed_core asserts (stage_seed.build_pred + make_s15_model.py --pin b):
an injective map of the core's instructions and operands into the instance with the same kinds, relative spo order,
resolved/committed/xm flags, operand slots, Reg/Mem state kind, exact ddi edges, and every core rf edge realized by an
rf (ddi rf)* path. For jobs of core A it reports how many instances contain A (should be all: the generator is sound)
and how many contain each other core B (should be few: the pin is not vacuous).
Usage: pin_contains.py <stage15lp out dir> [--cores N] [--per-core M]  (reads cores.json and jobs/<core>/s*/xml/inst-*.txt)
"""
import argparse, itertools, json, random, sys
from pathlib import Path

SLOTS = ["inreg", "inaddr", "inmem", "outreg", "outmem"]


def parse(path):
    sys.path.insert(0, str(Path(path).parent))
    rels = {}
    for line in open(path):
        line = line.strip()
        if not line.startswith("this/") or "=" not in line:
            continue
        name, body = line[5:].split("=", 1)
        body = body.strip()[1:-1]
        rels[name] = [tuple(x.strip() for x in t.split("->")) for t in body.split(",")] if body.strip() else []
    c = lambda n: rels.get(n, [])
    I = [a for (a,) in c("Instruction")]
    nxt = dict(c("Instruction<:spo"))
    first = [i for i in I if i not in nxt.values()]
    order, cur = [], first[0] if first else None
    while cur:
        order.append(cur); cur = nxt.get(cur)
    pos = {i: n for n, i in enumerate(order)}
    ops = {i: {s: [o for (j, o) in c(f"Instruction<:{s}") if j == i] for s in SLOTS} for i in I}
    st = {o: s.split("$")[0] for (o, s) in c("Operand<:opstate")}
    return dict(I=I, pos=pos, kind={i: k.split("$")[0] for i, k in c("Instruction<:kind")},
                res={i for i, _ in c("Instruction<:isresolved")}, com={i for i, _ in c("Instruction<:iscommitted")},
                xm={i for i, _ in c("Instruction<:isxm")}, ops=ops, st=st, rf=set(c("Operand<:rf")), ddi=set(c("Operand<:ddi")))


def path_reach(F):
    """pairs (a, b) with b in a.rf.*(ddi.rf)"""
    rf = {}
    for a, b in F["rf"]:
        rf.setdefault(a, set()).add(b)
    ddi = {}
    for a, b in F["ddi"]:
        ddi.setdefault(a, set()).add(b)
    out = set()
    for a in list(rf):
        seen, todo = set(), list(rf[a])
        while todo:
            x = todo.pop()
            if x in seen:
                continue
            seen.add(x); out.add((a, x))
            for y in ddi.get(x, ()):
                todo.extend(rf.get(y, ()))
    return out


def contains(C, F, reach):
    ci = sorted(C["I"], key=C["pos"].get)
    def ok_instr(c, f):
        return (C["kind"][c] == F["kind"][f] and (c in C["res"]) == (f in F["res"]) and (c in C["com"]) == (f in F["com"])
                and ((c not in C["xm"]) or f in F["xm"]))
    for fs in itertools.permutations(F["I"], len(ci)):
        if not all(ok_instr(c, f) for c, f in zip(ci, fs)):
            continue
        if not all(F["pos"][fs[k]] < F["pos"][fs[k + 1]] for k in range(len(fs) - 1)):
            continue
        # operand maps per instruction and slot (injective within a slot; slots are disjoint)
        choices, valid = [], True
        for c, f in zip(ci, fs):
            for sl in SLOTS:
                co, fo = C["ops"][c][sl], F["ops"][f][sl]
                if len(co) > len(fo):
                    valid = False; break
                choices.append([dict(zip(co, p)) for p in itertools.permutations(fo, len(co))])
            if not valid:
                break
        if not valid:
            continue
        for combo in itertools.product(*choices):
            m = {}
            for d in combo:
                m.update(d)
            if any(C["st"].get(o) != F["st"].get(m[o]) for o in m):
                continue
            if all((m[x], m[y]) in F["ddi"] for x, y in C["ddi"]) and all((m[x], m[y]) in reach for x, y in C["rf"]):
                return True
    return False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--cores", type=int, default=12)
    ap.add_argument("--per-core", type=int, default=10); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); out = Path(a.out)
    cj = json.loads((out / "cores.json").read_text()); rng = random.Random(a.seed)
    cores = {c["id"]: parse(c["rep"]) for c in cj["cores"]}
    have = [c["id"] for c in cj["cores"] if list((out / "jobs" / c["id"]).glob("s*/xml/inst-*.txt"))]
    pick = rng.sample(have, min(a.cores, len(have)))
    tot_own = tot_own_ok = tot_other = tot_other_hit = 0
    for cid in pick:
        files = sorted((out / "jobs" / cid).glob("s*/xml/inst-*.txt"))
        for f in rng.sample(files, min(a.per_core, len(files))):
            F = parse(str(f)); reach = path_reach(F)
            tot_own += 1; tot_own_ok += contains(cores[cid], F, reach)
            for other in pick:
                if other != cid:
                    tot_other += 1; tot_other_hit += contains(cores[other], F, reach)
    print(json.dumps({"cores_sampled": len(pick), "instances": tot_own, "contain_own_core": tot_own_ok,
                      "other_core_checks": tot_other, "contain_other_core": tot_other_hit}, indent=1))


if __name__ == "__main__":
    main()
