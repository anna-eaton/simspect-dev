import json, os, calendar, time, collections
F="/tests/simspect_alloy_20261108/firstdet_final/"
cut=calendar.timegm(time.strptime("2026-11-10 11:19:50","%Y-%m-%d %H:%M:%S"))
C=set(open(F+"uv5diag/C_stems_nt.txt").read().split())
D=set(open(F+"uv5diag/D_stems_nt.txt").read().split())
tot=collections.Counter(); hits=[]
cpu=[]
for d,host in (("T2rt_Footprint_6_u_core_lpP_fv3","cafe3"),("T2rt_Footprint_6_u_core_lpP_fv3_cafe1","cafe1")):
    for l in open(F+d+"/results.jsonl"):
        r=json.loads(l)
        pre = r["t_start"]<cut
        tot[(host,"pre" if pre else "post",r["status"])]+=1
        if r.get("hit") and "over_clean" in (r.get("terms_fired") or []):
            rec=json.load(open(f"{F}{d}/raw/{r['mode']}/{r['stem']}.json"))
            hits.append((host,"pre" if pre else "post",r["mode"],r["stem"],r["cache_setup"],r.get("stall_points"),"C" if r["stem"] in C and r["mode"].endswith("not_taken") else "-", "D" if r["stem"] in D and r["mode"].endswith("not_taken") else "-"))
print(tot); [print(h) for h in hits]
pre=[1 for k,v in tot.items() for _ in range(0)]
print("pre total", sum(v for k,v in tot.items() if k[1]=="pre"), "post total", sum(v for k,v in tot.items() if k[1]=="post"))
