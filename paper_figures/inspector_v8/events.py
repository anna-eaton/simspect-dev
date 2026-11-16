#!/usr/bin/env python3
"""events.py (agent stt-int-fig, 2026-11-16) -- print every event the Inspector figure v8/v8b draws, read from one kept gem5 trace.
Usage: events.py <pipeview.txt> <lc_pc> <fnc_pc> <xmit_pc>   (pcs in hex, from the check_ld record)
Prints, per O3PipeView record whose pc is in the test body (lc .. xmit), the stage ticks; then the BR: hook lines of fnc, the LSQUnit
lines that mention the xmit pc or its seq, and Commit squash lines. Cycle = (tick - lc fetch tick) / 500.
"""
import re, sys
P, LC, FNC, XM = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4], 16)
recs, cur, other = [], None, []
for ln in open(P, errors="replace"):
    s = ln.strip()
    m = re.search(r"O3PipeView:(fetch|decode|rename|dispatch|issue|complete|retire):(\d+)(?::(0x[0-9a-f]+):(\d+):(\d+):\s*(.*))?", s)
    if m and m.group(1) == "fetch":
        cur = dict(fetch=int(m.group(2)), pc=int(m.group(3), 16), upc=int(m.group(4)), seq=int(m.group(5)), dis=m.group(6).strip())
        recs.append(cur); continue
    if m and cur is not None:
        cur[m.group(1)] = int(m.group(2)); continue
    other.append(s)
lcf = [r for r in recs if r["pc"] == LC]
lcf = [r for r in lcf if r.get("retire", 0) > 0][-1]
T0 = lcf["fetch"]; cyc = lambda t: (t - T0) / 500 if t else None
print(f"T0 = lc fetch tick {T0} (seq {lcf['seq']})")
body = [r for r in recs if LC <= r["pc"] <= XM + 8 and r["seq"] >= lcf["seq"] and r["fetch"] < T0 + 2_000_000]
for r in body:
    st = " ".join(f"{k}={r[k]}({cyc(r[k]):g})" for k in ("fetch", "decode", "rename", "dispatch", "issue", "complete", "retire") if r.get(k))
    tag = " <lc" if r["pc"] == LC else (" <fnc" if r["pc"] == FNC else (" <xmit" if r["pc"] == XM else ""))
    print(f"seq {r['seq']:5d} pc {r['pc']:#x}.{r['upc']} {r['dis'][:44]:44s} {st}{tag}")
xseqs = {r["seq"] for r in body if r["pc"] == XM}
print("--- BR hook lines (fnc pc) ---")
for s in other:
    if "BR:" in s and f"pc={FNC:#x}" in s:
        t = int(re.search(r"simspect:(\d+)", s).group(1)); print(f"{t} ({cyc(t):g}) {s[s.find('BR:'):][:150]}")
print("--- LSQUnit / Commit lines about xmit (pc or seq) and squashes, ticks >= T0 ---")
for s in other:
    m = re.match(r"\s*(\d+):", s)
    if not m: continue
    t = int(m.group(1))
    if t < T0: continue
    if (f"{XM:#x}" in s) or any(f"[sn:{q}]" in s for q in xseqs) or ("Squashing due to branch mispred" in s and t < T0 + 3_000_000):
        print(f"{t} ({cyc(t):g}) {s[:220]}")
