#!/usr/bin/env python3
"""pv_table.py -- O3PipeView records as a table (one row per micro-op): seq, pc.upc, disasm, and fetch/decode/rename/dispatch/
issue/complete/retire as cycles relative to a base tick (cycle = (tick - base)/500; 0 = not recorded).
Usage: pv_table.py <pipeview.txt.gz> <base_tick> [seq_lo seq_hi]"""
import gzip, sys
pv, base = sys.argv[1], int(sys.argv[2]); lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1 << 60)
recs, cur = [], None
for l in gzip.open(pv, "rt", errors="replace"):
    if not l.startswith("O3PipeView:") or l.startswith("O3PipeView:simspect"):
        continue
    p = l.rstrip("\n").split(":")
    st = p[1]
    if st == "fetch":
        cur = dict(tick=dict(fetch=int(p[2])), pc=p[3], upc=p[4], seq=int(p[5]), dis=":".join(p[6:]).strip()); recs.append(cur)
    elif cur is not None and st in ("decode", "rename", "dispatch", "issue", "complete"):
        cur["tick"][st] = int(p[2])
    elif cur is not None and st == "retire":
        cur["tick"]["retire"] = int(p[2])
c = lambda t: "-" if not t else ("%d" % ((t - base) // 500) if t >= base else "<0")
print("seq  pc.upc        fetch decode rename disp issue compl retire  disasm")
for r in recs:
    if lo <= r["seq"] <= hi:
        t = r["tick"]
        print("%-4d %s.%-3s %6s %6s %6s %5s %5s %5s %6s  %s" % (r["seq"], r["pc"][-6:], r["upc"], c(t.get("fetch")), c(t.get("decode")),
              c(t.get("rename")), c(t.get("dispatch")), c(t.get("issue")), c(t.get("complete")), c(t.get("retire")), r["dis"]))
