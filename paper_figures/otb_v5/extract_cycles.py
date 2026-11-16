#!/usr/bin/env python3
"""extract_cycles.py -- every cycle drawn in Fig. 8 v5 (tikz/recon_otb_v5_8pt.tex), read from the kept trace of the integer
version of E2w test inst-003908, mispredict_not_taken (agent fig8-otb-v5, 2026-11-16). Cycle = (tick - lc fetch tick) / 500.
Each event names the exact trace line it comes from. Usage: extract_cycles.py runs/int_not_taken_inst-003908 [--json out]"""
import gzip, json, re, sys
from pathlib import Path
W = Path(sys.argv[1]); out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
L = [l.rstrip("\n") for l in gzip.open(W / "pipeview.txt.gz", "rt", errors="replace")]
pv = {}
cur = None
for l in L:
    if l.startswith("O3PipeView:") and not l.startswith("O3PipeView:simspect"):
        p = l.split(":")
        if p[1] == "fetch":
            cur = int(p[5]); pv[cur] = dict(pc=p[3], upc=int(p[4]), dis=":".join(p[6:]).strip(), fetch=int(p[2]))
        elif cur is not None and p[1] in ("decode", "rename", "dispatch", "issue", "complete", "retire"):
            pv[cur][p[1]] = int(p[2])
def first(pat):
    r = re.compile(pat)
    for l in L:
        if r.search(l):
            m = re.match(r"^\s*(?:O3PipeView:simspect:)?(\d+)", l)
            return int(m.group(1)), l.strip()
    raise SystemExit("pattern not found: " + pat)
SN = dict(i2=608, i3=611, i4=621, i6=677, merge=679, cqto=638, i7=684)   # wrip / load / mov micro-ops (pv_table.py)
base = pv[SN["i3"]]["fetch"]                                                # lc = i3 = 0x401c8f fetch
ev = []
def add(row, name, tick, src):
    ev.append(dict(row=row, event=name, tick=tick, cycle=(tick - base) // 500, source=src))
for row, sn in (("i2", 606), ("i3", 611), ("i4", 619), ("i6", 677), ("i7 (merge mov)", 679), ("i7", 682)):
    add(row, "fetch", pv[sn]["fetch"], f"O3PipeView fetch sn {sn} {pv[sn]['pc']} {pv[sn]['dis']}")
for row, sn in (("i2", 608), ("i3", 611), ("i4", 621), ("i6", 677), ("i7 (merge mov)", 679), ("i7", 684)):
    for st in ("decode", "rename", "issue", "complete", "retire"):
        if pv[sn].get(st):
            add(row, st, pv[sn][st], f"O3PipeView {st} sn {sn}")
for row, name, pat in (
    ("i2", "resolve hold (500 cycles)", r"BR:resolve_hold:.*seq=608:"),
    ("i2", "resolves (visible, correct)", r"BR:resolve_visible:.*seq=608:"),
    ("i3", "load executes, request sent", r"Memory request .* from inst \[sn:611\] was sent"),
    ("i4", "resolve hold (2,500 cycles)", r"BR:resolve_hold:.*seq=621:"),
    ("i4", "resolves mispredicted: Commit squash", r"Squashing due to branch mispred PC:0x401ca6 \[sn:621\]"),
    ("i4", "squash lands (rename squashes after sn 621)", r"rename: \[tid:0\] \[squash sn:621\] Squashing instructions"),
    ("i6", "load executes, request sent", r"Memory request .* from inst \[sn:677\] was sent"),
    ("i6", "squashed (LSQ)", r"Load Instruction PC \(0x401cf1=>0x401cf6\).* squashed, \[sn:677\]"),
    ("i7 (merge mov)", "executes", r"Execute: Processing PC \(0x401cf9=>0x401cfc\).*\[sn:679\]"),
    ("i7", "enters delay unit (tainted)", r"Inserting branch \[sn:684\] into delay_unit"),
    ("i7", "released from delay unit", r"Released tainted branch .* from delay_unit"),
    ("i7", "executes, mispredict detected, redirects fetch", r"\[sn:684\] Execute: Redirecting fetch"),
    ("i7", "Commit squash (resolve_visible mispred=1)", r"Squashing due to branch mispred PC:0x401d00 \[sn:684\]"),
):
    t, src = first(pat); add(row, name, t, src)
res = dict(base_tick=base, note="cycle 0 = fetch of lc (i3, 0x401c8f); window = (lc retire, squash lands)", events=ev)
for e in ev:
    print("%-16s %-48s tick %8d  cycle %5d" % (e["row"], e["event"], e["tick"], e["cycle"]))
if out:
    json.dump(res, open(out, "w"), indent=1)
