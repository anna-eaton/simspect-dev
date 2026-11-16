import json, os, collections
F="/tests/simspect_alloy_20261108/firstdet_final/"
def load(p):
    out={}
    for l in open(p):
        try: r=json.loads(l)
        except: continue
        out.setdefault((r["mode"],r["stem"]),[]).append(r)
    return out
for T in ["T2rt","T2g"]:
    a=load(F+T+"_Footprint_6_u_core_lpP_fv3/results.jsonl")
    b=load(F+T+"_Footprint_6_u_core_lpP_fv3_cafe1/results.jsonl")
    m=load(F+T+"_Footprint_6_u_core_lpP_fv3_merged/results.jsonl")
    dupa=sum(len(v)>1 for v in a.values()); dupb=sum(len(v)>1 for v in b.values())
    both=set(a)&set(b)
    print(T,"cafe3",len(a),"dup",dupa,"cafe1",len(b),"dup",dupb,"overlap",len(both),"union",len(set(a)|set(b)),"merged",len(m), "merged dups",sum(len(v)>1 for v in m.values()))
    print("  in union not merged", len((set(a)|set(b))-set(m)), " merged not in union", len(set(m)-(set(a)|set(b))))
    # disagreement in overlap
    dis=[k for k in both if a[k][-1].get("hit")!=b[k][-1].get("hit")]
    print("  overlap hit disagreements",len(dis), dis[:5])
    for k in both:
        if a[k][-1].get("hit") or b[k][-1].get("hit"):
            pass
    # over_clean hits per host
    for name,h in (("cafe3",a),("cafe1",b)):
        for k,v in h.items():
            if v[-1].get("hit") and "over_clean" in (v[-1].get("terms_fired") or []):
                print("  over_clean",name,k,v[-1].get("cache_setup"),v[-1].get("timing_point") or v[-1].get("stall_points"), "in merged:", k in m, "merged hit:", m.get(k,[{}])[-1].get("hit"))
    print("  merge.log tail:"); os.system(f"tail -3 {F}{T}_Footprint_6_u_core_lpP_fv3_merged/merge.log")
