#!/usr/bin/env python3
"""core_shapes.py (agent invisispec-fut 2026-11-16) -- read-only: tabulate the speculation SOURCES of Alloy instances.

For every inst-*.txt (Alloy sol.toString() dump, parsed with STAGE1_alloy/stage_seed.parse_txt) under the given dirs:
spo order, kind, resolved / committed / xm flags; the sources = the unresolved instructions spo-before the transmitter
(under the Futuristic contract every one of them makes xm speculative; under the Spectre contract only branches do).
Also per instance: rf_from_unresolved (some rf edge reads an output of an unresolved instruction) and
unresolved_output_feeds_xmit (such an output is in the transmitter's backward rf/ddi cone): on hardware without value
prediction a consumer cannot execute before its producer completes, so these graphs cannot be realized as drawn.
Category per instance: 'branch' (every source is a branch), 'nonbranch' (no source is a branch: needs a non-branch
speculation mechanism to concretize faithfully), 'mixed', or 'none' (no unresolved instruction before xm).

Usage: python3 core_shapes.py --code <code root> --json out.json <dir> [<dir> ...]   (dirs are searched recursively)
Prints a summary table; --json writes per-instance rows + the summary.
"""
import argparse, collections, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--json")
ap.add_argument("dirs", nargs="+")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.code) / "STAGE1_alloy"))
from stage_seed import parse_txt  # noqa: E402

KIND = {"TLoad": "ld", "TStore": "st", "TBranchn": "brn", "TBranchx": "brx", "TOthern": "othn", "TOtherx": "othx"}
rows, summ, srckind, shapes = [], collections.Counter(), collections.Counter(), collections.Counter()
errors = 0
for d in a.dirs:
    for p in sorted(Path(d).rglob("inst-*.txt")):
        try:
            r = parse_txt(p)
            ins = [t[0] for t in r.get("Instruction", [])]
            kind = {i: KIND[k.split("$")[0]] for i, k in r.get("Instruction<:kind", [])}
            nxt = dict(r.get("Instruction<:spo", []))
            first = (set(ins) - set(nxt.values())).pop()
            order = [first]
            while order[-1] in nxt:
                order.append(nxt[order[-1]])
            res = {i for i, _ in r.get("Instruction<:isresolved", [])}
            com = {i for i, _ in r.get("Instruction<:iscommitted", [])}
            xm = [i for i, _ in r.get("Instruction<:isxm", [])][0]
            pos = order.index(xm)
            src = [kind[i] for i in order[:pos] if i not in res]
            br = [k for k in src if k.startswith("br")]
            cat = "none" if not src else ("branch" if len(br) == len(src) else ("nonbranch" if not br else "mixed"))
            opsof = collections.defaultdict(set)
            for rel in ("inreg", "inaddr", "inmem", "outreg", "outmem"):
                for i, o in r.get(f"Instruction<:{rel}", []):
                    opsof[i].add((rel, o))
            outs_unres = {o for i in ins if i not in res for rel, o in opsof[i] if rel.startswith("out")}
            rf = r.get("Operand<:rf", [])
            ddi = r.get("Operand<:ddi", [])
            readers = [b for a_, b in rf if a_ in outs_unres]
            # backward dataflow cone of the transmitter's operands (rf^-1 + ddi^-1)
            back = collections.defaultdict(set)
            for a_, b in rf + ddi:
                back[b].add(a_)
            cone, todo = set(), [o for _, o in opsof[xm]]
            while todo:
                o = todo.pop()
                for q in back[o]:
                    if q not in cone:
                        cone.add(q); todo.append(q)
            rf_unres = bool(readers)
            src_feeds_x = bool(cone & outs_unres)
            shape = " ".join(kind[i] + ("!U" if i not in res else "") + ("C" if i in com else "") + ("*X" if i == xm else "")
                             for i in order)
            rows.append(dict(file=str(p), n=len(order), cat=cat, sources=src, shape=shape,
                             rf_from_unresolved=rf_unres, unresolved_output_feeds_xmit=src_feeds_x))
            summ[cat] += 1
            summ[(cat, "rf_from_unresolved")] += rf_unres
            summ[(cat, "unresolved_output_feeds_xmit")] += src_feeds_x
            for k in set(src):
                srckind[k] += 1
            shapes[shape] += 1
        except Exception as e:  # never silent
            errors += 1
            print(f"ERROR {p}: {e!r}", file=sys.stderr)
n = len(rows)
print(f"instances {n} (parse errors {errors})")
for c in ("branch", "nonbranch", "mixed", "none"):
    print(f"  {c:10s} {summ[c]:7d}  {100 * summ[c] / max(n, 1):5.1f}%   rf read from an unresolved instr: {summ[(c, 'rf_from_unresolved')]}"
          f"   unresolved instr's output in the transmitter's dataflow cone: {summ[(c, 'unresolved_output_feeds_xmit')]}")
print("instances with >=1 source of kind:", dict(srckind))
print("top shapes (!U = unresolved, C = committed, *X = transmitter):")
for s, c in shapes.most_common(15):
    print(f"  {c:6d}  {s}")
if a.json:
    Path(a.json).write_text(json.dumps(dict(summary={str(k): v for k, v in summ.items()}, source_kinds=dict(srckind), n=n, errors=errors,
                                            top_shapes=shapes.most_common(50), rows=rows), indent=1))
