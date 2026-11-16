import json, collections, sys
F="/tests/simspect_alloy_20261108/firstdet_final/"
for d in ["T2rt_Footprint_6_u_core_lpP_fv3_merged","T2g_Footprint_6_u_core_lpP_fv3_merged"]:
    res={}
    for l in open(F+d+"/results.jsonl"):
        r=json.loads(l); res[(r["mode"],r["stem"])]=r
    st=collections.Counter(r["status"] for r in res.values())
    hits=[k for k,r in res.items() if r.get("hit")]
    cls={}
    for l in open(F+d+"/classes_rmw.jsonl"):
        c=json.loads(l); cls[(c["mode"],c["stem"])]=c
    print("==",d,"rows",len(res),st,"hits",len(hits),"classified",len(cls), "hits not classified", len(set(hits)-set(cls)))
    sig=collections.Counter(tuple(sorted(c["sigs"])) for c in cls.values())
    for k,v in sig.most_common(): print("  ",v,k)
    causes=collections.Counter((i.get("cause"),i["term"],i["struct"]) for c in cls.values() for i in c.get("items",[]))
    print("  item causes:"); [print("    ",v,k) for k,v in causes.most_common()]
    un=[c for c in cls.values() if any(s not in ("UV3","UV4","UV5") for s in c["sigs"])]
    bys=collections.Counter((tuple(sorted(c["sigs"])),c.get("cache_setup")) for c in un)
    print("  non-UV3/4/5 by setup:", dict(bys))
    for c in un[:0]: print(c)
