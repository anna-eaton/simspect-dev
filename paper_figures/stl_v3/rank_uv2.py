#!/usr/bin/env python3
"""Rank the counted UV2 (A2 STLF bypass, twin evidence) E2w tests by how simple their Alloy execution graph is, for Fig. 7.
Read-only. Run inside cafe3 gem5_dev:  python3 - < rank_uv2.py   (paths below are the E2w campaign's).
Prints one line per not_taken A2 test: #instructions, kinds in program order, and whether a store before the transmitter
takes its address from the same producer (rf) as the transmitter (a static same-address store, the forwarding candidate)."""
import json, re, sys
E = "/tests/bigcorpus_20261115/e2w"; T = "/tests/bigcorpus_20261115/testsets/STT_6_u_core_lpP_s2A"
d = json.load(open(f"{E}/buckets_per_stem.json")); ev = json.load(open(f"{E}/recon_stlf_evidence.json"))
keys = [k for k, v in d.items() if v == "A2 STLF bypass" and k.startswith("mispredict_not_taken/ld/plain/")]
def rel(txt, name):
    m = re.search(r"^this/" + re.escape(name) + r"=\{(.*)\}$", txt, re.M)
    return [tuple(p.split("->")) for p in m.group(1).split(", ")] if m and m.group(1) else []
rows = []
for k in keys:
    s = k.split("/")[-1]; txt = open(f"{T}/xml/{s}.txt").read()
    kind = dict(rel(txt, "Instruction<:kind")); idx = {a: int(b[2:-2]) for a, b in rel(txt, "Instruction<:idx")}
    order = sorted(idx, key=idx.get); pc = {a: i for i, a in enumerate(order)}
    inaddr = {}; [inaddr.setdefault(a, []).append(b) for a, b in rel(txt, "Instruction<:inaddr")]
    outreg = {b: a for a, b in rel(txt, "Instruction<:outreg")}
    rf = {}; [rf.setdefault(b, []).append(a) for a, b in rel(txt, "Operand<:rf")]
    com = {a for a, _ in rel(txt, "Instruction<:iscommitted")}; res = {a for a, _ in rel(txt, "Instruction<:isresolved")}
    xm = [a for a, _ in rel(txt, "Instruction<:isxm")][0]
    def src(i):  # producers of instruction i's address operands
        return {outreg.get(o) for a in inaddr.get(i, []) for o in rf.get(a, [])}
    same = [pc[i] for i in order if kind[i] == "TStore$0" and pc[i] < pc[xm] and src(i) & src(xm) - {None}]
    ks = " ".join(("C" if i in com else "") + kind[i][1:-2] + ("*" if i == xm else "") for i in order)
    e = ev.get(f"mispredict_not_taken/{s}", {})
    rows.append((len(order), len(same) == 0, s, ks, same, e.get("ready_tick"), e.get("ctrl_visible")))
rows.sort(key=lambda r: (r[1], r[0]))
for r in rows[:int(sys.argv[1]) if len(sys.argv) > 1 else 60]:
    print(*r, sep="\t")
print("n", len(rows), "with static same-address store", sum(1 for r in rows if not r[1]))
