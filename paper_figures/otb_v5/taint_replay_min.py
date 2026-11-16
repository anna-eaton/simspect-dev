#!/usr/bin/env python3
"""taint_replay_min.py -- minimal replay of gem5-recon's rename-time taint propagation for one test body (agent fig8-otb-v5).
Rules as in gem5-recon-modded src/cpu/o3/rename.cc:714-720 and secure_scheme/taint_tracker.cc:44-131: a speculative load
inserts its own taint on its destinations; any other micro-op with a tainted source gives every destination the taint of its
OLDEST tainted source (getOldestTaint); flat phys reg 16 is skipped; std::map insert does not overwrite. Counterfactual UNION:
destinations get the set of all tainted sources. Speculative loads = the loads given on the command line (the body's loads
under an unresolved branch at rename); no taint is freed during the replayed span (it ends before the first free).
Prints every micro-op in [lo, hi] whose OLDEST taint or UNION set is non-empty, and marks merges (>= 2 distinct roots).
Usage: taint_replay_min.py <pipeview.txt.gz> <lo sn> <hi sn> <spec load sn> [...]"""
import gzip, re, sys
R_PROC = re.compile(r"rename: \[tid:0\] Processing instruction \[sn:(\d+)\]")
R_SRC = re.compile(r"Looking up (\w+?)RegClass arch reg (\d+), got phys reg (\d+) \((\w+?)RegClass\)")
R_FLAT = re.compile(r"Register (\d+) \(flat: (\d+)\) \((\w+?)RegClass\)")
R_DST = re.compile(r"Renaming arch reg (\d+) \((\w+?)RegClass\) to physical reg (\d+) \((\d+)\)")
R_FETCH = re.compile(r"^O3PipeView:fetch:(\d+):0x([0-9a-f]+):(\d+):(\d+):\s+(.*)$")
pv, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); spec = {int(x) for x in sys.argv[4:]}
ren, cur, dis, order = {}, None, {}, []
for l in gzip.open(pv, "rt", errors="replace"):
    m = R_FETCH.match(l.rstrip("\n"))
    if m:
        dis.setdefault(int(m.group(4)), "0x%s.%s %s" % (m.group(2)[-6:], m.group(3), m.group(5).strip())); continue
    m = R_PROC.search(l)
    if m:
        cur = int(m.group(1))
        if cur in ren:      # re-renamed after a squash: keep the first (pre-squash) instance only
            cur = None; continue
        ren[cur] = dict(src=[], dst=[]); order.append(cur); continue
    if cur is None:
        continue
    m = R_SRC.search(l)
    if m:
        ren[cur]["src"].append((m.group(1), int(m.group(3)))); continue
    m = R_DST.search(l)
    if m:
        ren[cur]["dst"].append((m.group(2), int(m.group(3)), int(m.group(4)))); continue
oldest, union = {}, {}
for sn in order:
    if not (lo <= sn <= hi):
        continue
    r = ren[sn]
    srcs = [s for s in r["src"]]
    if sn in spec:
        o, u = sn, {sn}
    else:
        ts = [oldest[s] for s in srcs if s in oldest]
        o = min(ts) if ts else None
        u = set().union(*[union[s] for s in srcs if s in union]) if any(s in union for s in srcs) else set()
    for cls, phys, flat in r["dst"]:
        if flat == 16 and cls == "Int":
            continue
        k = (cls, phys)
        if o is not None:
            oldest.setdefault(k, o)
        if u:
            union.setdefault(k, set(u))
    roots = sorted({oldest[s] for s in srcs if s in oldest})
    if o is not None or u:
        tag = "  MERGE: sources carry roots %s, oldest keeps %s" % (roots, o) if len(roots) >= 2 else ""
        print("[sn:%d] %-55s OLDEST=%-5s UNION=%s%s" % (sn, dis.get(sn, "?")[:55], o, sorted(u), tag))
