#!/usr/bin/env python3
"""status_node.py (agent inttwin2 2026-11-16) -- read-only status of the inttwin loops on one node, one JSON line on stdout.
Run on the Mac:  ssh <node> "docker exec -i gem5_dev python3 - <node>" < scripts/inttwin_20261116/status_node.py
For each queue name served by the node (cafe3 also serves cafe3ra): queue .last (items/done/running, age), every row's cls/<row>/DONE,
the post-steps (rsa8 'ALL DONE <row>' in logs/rsa8.log, stl_ot cls/<row>/OT_DONE, cafe2 UV6 cls/uv6_confirm_int/ALLDONE) and whether the
loop processes are alive. 'finished' = everything done; 'stalls' = a loop that is not alive while its work is not done, or a queue whose
.last is older than 45 min while unfinished. Used by watch_done.sh."""
import json, os, re, subprocess, sys, time

O = "/tests/inttwin_20261116"
node = sys.argv[1]
qnames = {"cafe3": ["cafe3", "cafe3ra"]}.get(node, [node])
camps = json.load(open(f"{O}/code/runconfigs/inttwin_20261116/campaigns.json"))
ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
now = time.time()
st = {"node": node, "t": time.strftime("%F %T", time.gmtime()), "queues": {}, "rows": {}, "post": {}, "stalls": []}
fin = True
for q in qnames:
    p = f"{O}/logs/queue_{q}.last"
    try:
        s = open(p).read().split(); age = now - os.path.getmtime(p)
        items, done, running = int(s[s.index("items") + 1]), int(s[s.index("done") + 1]), int(s[s.index("running") + 1])
    except Exception as e:
        items = done = running = -1; age = 1e9
    qdone = items > 0 and done == items and running == 0
    st["queues"][q] = dict(items=items, done=done, running=running, age_min=round(age / 60, 1), finished=qdone)
    alive_q = re.search(rf"run_queue.py --node {q}( |$)", ps, re.M)
    alive_c = re.search(rf"classify_node.py --node {q}( |$)", ps, re.M)
    if not qdone:
        fin = False
        if not alive_q:
            st["stalls"].append(f"run_queue {q} not running, queue unfinished")
        elif age > 45 * 60:
            st["stalls"].append(f"queue {q} .last {age/60:.0f} min old")
    rows = sorted({c["row"] for c in camps if c["node"] == q})
    for r in rows:
        d = os.path.exists(f"{O}/cls/{r}/DONE"); st["rows"][r] = d
        if not d:
            fin = False
            if not alive_c:
                st["stalls"].append(f"classify_node {q} not running, {r} has no DONE")
rsa8 = open(f"{O}/logs/rsa8.log").read() if os.path.exists(f"{O}/logs/rsa8.log") else ""
post = {"cafe1": dict(rsa8=["E2_STT_6_u_core_lpP_s2A"], ot=["E2wstl_Recon_6_u_stl_core_lpP_s2A"]),
        "cafe2": dict(rsa8=["E6_Recon_6_u_core_lpP_s2A"], ot=[], uv6=True),
        "cafe3": dict(rsa8=["E2w_STT_6_u_core_lpP_s2A", "E2w_STT_6_u_core_lpP_s2A_ra"], ot=["E2wstl_Recon_6_u_stl_core_lpP_s2A_ra"])}[node]
for r in post["rsa8"]:
    d = f"ALL DONE {r}\n" in rsa8 or rsa8.rstrip().endswith(f"ALL DONE {r}"); st["post"][f"rsa8 {r}"] = d
    if not d:
        fin = False
        if f"rsa8_node.sh {r}" not in ps and not re.search(rf"for r in [^;]*{r}\b", ps):
            st["stalls"].append(f"rsa8 loop for {r} not running")
for r in post["ot"]:
    d = os.path.exists(f"{O}/cls/{r}/OT_DONE"); st["post"][f"ot {r}"] = d
    if not d:
        fin = False
        if f"stl_ot_node.sh {r}" not in ps:
            st["stalls"].append(f"stl_ot loop for {r} not running")
if post.get("uv6"):
    d = os.path.exists(f"{O}/cls/uv6_confirm_int/ALLDONE"); st["post"]["uv6"] = d
    if not d:
        fin = False
        if "confirm_uv6_twin.sh" not in ps and "uv6_confirm" not in ps:
            st["stalls"].append("uv6 loop not running")
try:
    v = os.statvfs("/tests"); st["tests_free_gb"] = round(v.f_bavail * v.f_frsize / 1e9)
except Exception:
    pass
st["finished"] = fin
print(json.dumps(st))
