#!/usr/bin/env python3
"""dataflow_trace.py -- register dataflow of one micro-op from a gem5 Rename debug trace (agent fig8-otb-v5, 2026-11-16).
For a target sn, walks the Rename lines backwards: each source phys reg -> the sn that renamed it as a destination (the
latest writer before the reader), recursively, and prints the tree with each node's disasm and whether it is a load
(LSQ "Inserting load"). Flags (CC) registers are included, as gem5's rename prints them. The walk stops at registers
with no in-trace writer (initial state) and at a depth limit.
Usage: dataflow_trace.py <pipeview.txt.gz> <target sn> [max_depth]"""
import gzip, re, sys
R_PROC = re.compile(r"rename: \[tid:0\] Processing instruction \[sn:(\d+)\]")
R_SRC = re.compile(r"Looking up (\w+?)RegClass arch reg (\d+), got phys reg (\d+) \((\w+?)RegClass\)")
R_DST = re.compile(r"Renaming arch reg (\d+) \((\w+?)RegClass\) to physical reg (\d+) \((\d+)\)")
R_SQ = re.compile(r"rename: \[tid:0\] \[squash sn:(\d+)\]")
R_LD = re.compile(r"lsq\.thread0: Inserting load PC .*\[sn:(\d+)\]")
R_FETCH = re.compile(r"^O3PipeView:fetch:(\d+):0x([0-9a-f]+):(\d+):(\d+):\s+(.*)$")
pv, target = sys.argv[1], int(sys.argv[2]); maxd = int(sys.argv[3]) if len(sys.argv) > 3 else 12
srcs, writer_hist, cur, loads, dis = {}, {}, None, set(), {}
order = []
for l in gzip.open(pv, "rt", errors="replace"):
    m = R_FETCH.match(l.rstrip("\n"))
    if m:
        dis.setdefault(int(m.group(4)), "0x%s.%s %s" % (m.group(2)[-6:], m.group(3), m.group(5).strip())); continue
    m = R_PROC.search(l)
    if m:
        cur = int(m.group(1)); srcs[cur] = []; order.append(cur); continue
    if cur is not None:
        m = R_SRC.search(l)
        if m and "Looking up" in l:
            srcs[cur].append((m.group(1), int(m.group(2)), int(m.group(3)))); continue
        m = R_DST.search(l)
        if m:
            writer_hist.setdefault((m.group(2), int(m.group(3))), []).append((cur, int(m.group(1)))); continue
    m = R_LD.search(l)
    if m:
        loads.add(int(m.group(1)))
def writer(cls, phys, before):
    best = None
    for sn, arch in writer_hist.get((cls, phys), []):
        if sn < before and (best is None or sn > best[0]):
            best = (sn, arch)
    return best
seen = set()
def walk(sn, d, pre):
    tag = " LOAD" if sn in loads else ""
    print("%s[sn:%d] %s%s" % (pre, sn, dis.get(sn, "?"), tag))
    if d >= maxd or sn in seen:
        if sn in seen and srcs.get(sn): print(pre + "    (see above)")
        return
    seen.add(sn)
    uniq = []
    for s in srcs.get(sn, []):
        if s not in uniq: uniq.append(s)
    for cls, arch, phys in uniq:
        w = writer(cls, phys, sn)
        if w is None:
            print("%s    <- %s arch %d phys %d: no writer in trace (initial)" % (pre, cls, arch, phys)); continue
        print("%s    <- %s arch %d phys %d from:" % (pre, cls, arch, phys))
        walk(w[0], d + 1, pre + "      ")
walk(target, 0, "")
