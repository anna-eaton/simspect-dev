#!/usr/bin/env python3
"""TIME-1 (agent timing, 2026-11-15): per-phase load statistics from the host load monitor (loadmon_host.sh log).

For each phase window (label=START,END in UTC 'YYYY-mm-dd HH:MM:SS'), averages the samples strictly inside it (first and
last 60 s dropped as ramp): 1-min loadavg mean/max, busy hardware threads = (us + sy + ni) / 100 x 64, and flags any sample
whose top-6 list contains a non-root, non-acbeaton process above 50 %CPU (another user's load).
Usage: loadstats.py <loadmon.log> 'T1g=2026-11-15 22:27:14,2026-11-15 22:31:26' ...
"""
import re, sys, statistics as st
from datetime import datetime, timedelta

F = "%Y-%m-%d %H:%M:%S"
samples = []
for l in open(sys.argv[1]):
    m = re.match(r"(\S+ \S+) load=(\S+) \S+ \S+ R=(\d+) \| %Cpu\(s\):\s*([\d.]+) us,\s*([\d.]+) sy,\s*([\d.]+) ni.*?\|\s*(.*)$", l.strip())
    if m:
        t = datetime.strptime(m.group(1), F)
        busy = (float(m.group(4)) + float(m.group(5)) + float(m.group(6))) / 100 * 64
        others = [x for x in m.group(7).split(";") if x.strip() and x.strip().split("/")[0] not in ("root", "acbeaton")
                  and float(x.strip().split("/")[-1] or 0) > 50]
        samples.append((t, float(m.group(2)), int(m.group(3)), busy, others))
print("| phase | window (UTC) | samples | 1-min load mean (max) | busy hw threads mean (min-max) | other users' processes >50% |")
print("|---|---|---|---|---|---|")
for arg in sys.argv[2:]:
    lab, w = arg.split("=", 1)
    a, b = (datetime.strptime(x.strip(), F) for x in w.split(","))
    s = [x for x in samples if a + timedelta(seconds=60) <= x[0] <= b - timedelta(seconds=60)]
    if not s:
        print(f"| {lab} | {a:%H:%M:%S}-{b:%H:%M:%S} | 0 | | | |"); continue
    oth = sorted({o.strip() for x in s for o in x[4]})
    print(f"| {lab} | {a:%H:%M:%S}-{b:%H:%M:%S} | {len(s)} | {st.mean(x[1] for x in s):.1f} ({max(x[1] for x in s):.1f}) | "
          f"{st.mean(x[3] for x in s):.1f} ({min(x[3] for x in s):.1f}-{max(x[3] for x in s):.1f}) | {', '.join(oth) or 'none'} |")
