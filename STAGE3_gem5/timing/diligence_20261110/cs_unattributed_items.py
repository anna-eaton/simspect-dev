import json, collections, gzip
F="/tests/simspect_alloy_20261108/firstdet_final/"
for d in ["T2rt_Footprint_6_u_core_lpP_fv3_merged","T2g_Footprint_6_u_core_lpP_fv3_merged"]:
    whys=collections.Counter(); lines=collections.Counter(); ex=[]
    for l in open(F+d+"/classes_rmw.jsonl"):
        c=json.loads(l)
        if "no_evidence" in c["sigs"]: ex.append(("NOEV",c["mode"],c["stem"],c["cache_setup"]))
        for it in c.get("items",[]):
            if it["cause"]=="unattributed":
                lines[it["line"]]+=1; whys[it["why"][:90]]+=1
                if len(ex)<40: ex.append(("UN",c["mode"],c["stem"],c["cache_setup"],it["line"],it["why"][:160]))
    print("==",d); print(" lines",lines.most_common(8)); print(" whys",whys.most_common(6))
    for e in ex[:14]: print("  ",e)
