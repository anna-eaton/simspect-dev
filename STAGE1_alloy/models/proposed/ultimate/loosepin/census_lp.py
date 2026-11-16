#!/usr/bin/env python3
"""census_lp.py -- read-only shape census for the loose-pin drafts.

Reads Alloy instances (inst-*.txt from a6CountModels/a6RandomModels, or inst-*.xml when no .txt exists) from one or
more run dirs, dedups by the census_flat.py isomorphism fingerprint (kinds in program order, flags, operand slots with
canonical state sharing, rf and ddi edges, minimized over same-slot operand orders), and counts, over DISTINCT programs:
  sizes, unresolved_brs_hist, n_committed_hist, xm_kinds
  alu_feeds_xmit        an ALU output is read directly by the transmitter's leak operand
  alu_in_cone           an ALU anywhere in the transmitter's backward rf cone (includes ALUs that only compute an access's address)
  alu_on_leak_path      an ALU on a value path load.outreg -> ... -> transmitter leak operand (rf + ddi forward; a load's
                        address has no ddi edge, so address-only ALUs do not count) -- the 'ALU on the transmitter path' class
  otb_merge             an ALU in that cone reads the outputs of >= 2 distinct loads (OTB two-source merge)
  otb_complete          (2026-11-10) an ALU whose output reaches the leak operand has two different inputs fed (rf/ddi
                        paths) by an OLDER load with no unresolved branch before it and a YOUNGER load behind an
                        unresolved branch (the ReCon getOldestTaint shape)
  uv5_pre               a COMMITTED load whose address operand is rf-fed by an earlier instruction (UV5 precondition,
                        same test as STAGE3_gem5/triage/uv5_shape/committed_rf_scan.py 'committed_load_addr_rf_fed')
  uv5_pre_sameword      ... and that load reads the same Mem_s atom as a speculative (uncommitted, behind an
                        unresolved gate) load  (XML-level proxy for 'same line as a speculative load')
  any_rf_into_committed any rf edge into an operand of a committed instruction (committed_rf_scan.py)
  committed_ldld_pair   committed loads L1, L2 with L1.outreg -rf-> L2.inaddr (ReCon reveal pair, R-SA-2..6)
  pair_reload           ... and a later uncommitted load reads L1's Mem_s (the R-SA re-load shape)
  rmw_xmit / rmw_any    the transmitter is an RMW / the program has an RMW (TRmw kind)
  stl_alias             an unresolved store and a later load on the same Mem_s
Plus PAIRWISE_OVERLAP of distinct programs between run dirs and the UNION.
Usage: census_lp.py [--jobs 16] [--json OUT] [--sample N] RUN_DIR [RUN_DIR ...]
"""
import argparse, collections, itertools, json, random, re, sys
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))  # cafe workspace layout ($WS/lp + $WS/tools)
sys.path.insert(0, str(HERE.parents[1] / "singlestage" / "tools"))  # repo layout
import census_flat as cf  # noqa: E402  (load/fingerprint/shape, unchanged)

IFIELDS = {"kind", "idx", "spo", "inreg", "inaddr", "outreg", "inmem", "outmem", "isresolved", "iscommitted", "isxm"}
OFIELDS = {"opstate", "rf", "ddi"}


def load_xml(p):
    inst = ET.parse(p).getroot().find("instance")
    rels = {}
    for s in inst.findall("sig"):
        lab = s.get("label")
        if lab in ("this/Instruction",):
            rels["Instruction"] = [(a.get("label"),) for a in s.findall("atom")]
    for f in inst.findall("field"):
        lab = f.get("label")
        key = f"Instruction<:{lab}" if lab in IFIELDS else f"Operand<:{lab}" if lab in OFIELDS else None
        if key:
            rels[key] = [tuple(a.get("label") for a in t.findall("atom")) for t in f.findall("tuple")]
    return rels


def load_any(p):
    if p.endswith(".txt"):
        return cf.load(p)
    r = load_xml(p); c = lambda n: r.get(n, [])
    I = [x for (x,) in c("Instruction")]; nxt = dict(c("Instruction<:spo"))
    cur = [i for i in I if i not in nxt.values()][0]; order = []
    while cur:
        order.append(cur); cur = nxt.get(cur)
    ops = collections.defaultdict(list)
    for s in cf.SL:
        for i, o in c(f"Instruction<:{s}"):
            ops[(i, s)].append(o)
    return dict(order=order, pos={i: n for n, i in enumerate(order)}, kind={i: k.split("$")[0] for i, k in c("Instruction<:kind")},
                res={i for i, _ in c("Instruction<:isresolved")}, com={i for i, _ in c("Instruction<:iscommitted")},
                xm={i for i, _ in c("Instruction<:isxm")}, ops=ops, st=dict(c("Operand<:opstate")),
                rf=set(c("Operand<:rf")), ddi=set(c("Operand<:ddi")), spo=c("Instruction<:spo"))


def extra(F):
    opi = {o: i for (i, s), l in F["ops"].items() for o in l}
    K, P, com, res = F["kind"], F["pos"], F["com"], F["res"]
    xm = next(iter(F["xm"]), None)
    get = lambda i, s: F["ops"].get((i, s), [])
    ins_of = lambda i: [o for s in ("inreg", "inaddr", "inmem") for o in get(i, s)]
    alu = lambda i: K[i] in ("TOthern", "TOtherx")
    ld = lambda i: K[i] == "TLoad"
    cone, todo = set(), [xm] if xm else []
    while todo:
        i = todo.pop()
        for o in ins_of(i):
            for x, y in F["rf"]:
                if y == o and opi[x] not in cone and opi[x] != xm:
                    cone.add(opi[x]); todo.append(opi[x])
    gates = [i for i in F["order"] if i not in res and K[i] in ("TBranchn", "TBranchx", "TStore")]
    spec = {i for i in F["order"] if i not in com and any(P[g] < P[i] for g in gates)}
    memof = lambda i: {F["st"].get(o) for o in get(i, "inmem")}
    rfdst = {y for _, y in F["rf"]}
    cl = [i for i in F["order"] if ld(i) and i in com]
    uv5 = [i for i in cl if any(o in rfdst for o in get(i, "inaddr"))]
    specld_mem = set().union(*[memof(i) for i in F["order"] if ld(i) and i in spec]) if spec else set()
    pairs = [(a, b) for a in cl for b in cl if a != b and any((x, y) in F["rf"] for x in get(a, "outreg") for y in get(b, "inaddr"))]
    reload = any(any(memof(c) & memof(a) for c in F["order"] if ld(c) and c not in com and P[c] > P[a]) for a, _ in pairs)
    stl = any(any(F["st"].get(o) in memof(l) for o in get(s, "outmem")) for s in F["order"] if K[s] == "TStore" and s not in res
              for l in F["order"] if ld(l) and P[l] > P[s])
    succ = collections.defaultdict(set)
    for x, y in F["rf"] | F["ddi"]:
        succ[x].add(y)
    def reach(srcs):
        seen, todo = set(srcs), list(srcs)
        while todo:
            for y in succ[todo.pop()]:
                if y not in seen: seen.add(y); todo.append(y)
        return seen
    leakops = set(get(xm, "inaddr") + get(xm, "inreg")) if xm else set()
    from_loads = reach([o for i in F["order"] if ld(i) for o in get(i, "outreg")])
    on_leak = any(alu(i) and any(o in from_loads for o in get(i, "inreg")) and (reach(get(i, "outreg")) & leakops)
                  for i in F["order"])
    # OTB-complete (ReCon getOldestTaint shape): an ALU m with two DIFFERENT
    # input operands a, b such that an OLDER load Lo's output reaches a and a YOUNGER load Ly's output reaches b (rf/ddi
    # paths), Lo has no unresolved branch before it (it is behind a resolved branch or none), Ly has an unresolved branch
    # before it, and m's output reaches the transmitter's leak operand.
    ubr = [i for i in F["order"] if i not in res and K[i] in ("TBranchn", "TBranchx")]
    behind = lambda i: any(P[g] < P[i] for g in ubr)
    lds = [i for i in F["order"] if ld(i)]
    lreach = {l: reach(get(l, "outreg")) for l in lds}
    otb_complete = False
    for m in F["order"]:
        if not alu(m) or not (reach(get(m, "outreg")) & leakops):
            continue
        mins = get(m, "inreg")
        for lo in lds:
            if behind(lo):
                continue
            for ly in lds:
                if P[ly] <= P[lo] or not behind(ly):
                    continue
                if any(a != b and a in lreach[lo] and b in lreach[ly] for a in mins for b in mins):
                    otb_complete = True
    return dict(alu_in_cone=any(alu(i) for i in cone), alu_on_leak_path=on_leak, otb_complete=otb_complete, uv5_pre=bool(uv5),
                uv5_pre_sameword=any(memof(i) & specld_mem for i in uv5),
                any_rf_into_committed=any(opi[y] in com for _, y in F["rf"]),
                committed_ldld_pair=bool(pairs), pair_reload=reload,
                rmw_xmit=bool(xm) and K[xm] == "TRmw", rmw_any=any(K[i] == "TRmw" for i in F["order"]),
                stl_alias=stl, n_committed=len(com))


def job(p):
    try:
        F = load_any(p); s = cf.shape(F); s.update(extra(F)); s["fp"] = cf.fingerprint(F); s["file"] = p
        return s
    except Exception as e:
        return {"error": repr(e), "file": p}


FLAGS = ["alu_feeds_xmit", "alu_in_cone", "alu_on_leak_path", "two_load_merge", "otb_complete", "uv5_pre", "uv5_pre_sameword", "any_rf_into_committed",
         "committed_ldld_pair", "pair_reload", "rmw_xmit", "rmw_any", "stl_alias"]


def summarize(rows):
    d = {}
    for r in rows:
        d.setdefault(r["fp"], r)
    u = list(d.values()); n = len(u) or 1
    out = dict(instances=len(rows), distinct=len(u), sizes=dict(sorted(collections.Counter(r["n"] for r in u).items())),
               kind_sequences=len({r["kinds"] for r in u}), xm_kinds=dict(collections.Counter(r["xm_kind"] for r in u)),
               unresolved_brs_hist=dict(sorted(collections.Counter(r["unresolved_brs"] for r in u).items())),
               n_committed_hist=dict(sorted(collections.Counter(r["n_committed"] for r in u).items())),
               unnecessary_avg=round(sum(r["unnecessary"] for r in u) / n, 2))
    for k in FLAGS:
        c = sum(bool(r[k]) for r in u); out[k] = c; out[k + "_pct"] = round(100.0 * c / n, 2)
    out["otb_merge"] = out.pop("two_load_merge"); out["otb_merge_pct"] = out.pop("two_load_merge_pct")
    out["examples"] = {k: [r["file"] for r in u if r[k]][:3] for k in ("uv5_pre_sameword", "committed_ldld_pair", "two_load_merge", "pair_reload", "otb_complete")}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--jobs", type=int, default=16); ap.add_argument("--json")
    ap.add_argument("--sample", type=int, default=0); ap.add_argument("runs", nargs="+"); a = ap.parse_args()
    res, allrows, sets = {}, [], {}
    with Pool(a.jobs) as pool:
        for d in a.runs:
            fs = sorted(str(x) for x in Path(d).glob("inst-*.txt")) or sorted(str(x) for x in Path(d).glob("inst-*.xml"))
            if a.sample and len(fs) > a.sample:
                fs = sorted(random.Random(1).sample(fs, a.sample))
            rows, errs = [], 0
            for s in pool.imap_unordered(job, fs, chunksize=50):
                if "error" in s:
                    errs += 1; continue
                rows.append(s)
            res[d] = summarize(rows); res[d]["parse_errors"] = errs; allrows += rows; sets[d] = {r["fp"] for r in rows}
    if len(a.runs) > 1:
        res["UNION"] = summarize(allrows)
        res["PAIRWISE_OVERLAP"] = {f"{Path(x).name}&{Path(y).name}": len(sets[x] & sets[y]) for x, y in itertools.combinations(a.runs, 2)}
    txt = json.dumps(res, indent=1, default=str, ensure_ascii=False)
    if a.json:
        Path(a.json).write_text(txt)
    print(txt)
