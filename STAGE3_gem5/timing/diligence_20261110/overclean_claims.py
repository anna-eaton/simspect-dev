import json, os, glob, collections
F="/tests/simspect_alloy_20261108/firstdet_final/"
for d in sorted(glob.glob(F+"T2*")):
    if not os.path.isdir(d) or not os.path.exists(d+"/results.jsonl"): continue
    c=collections.Counter(); ex=[]
    for l in open(d+"/results.jsonl"):
        try: r=json.loads(l)
        except: continue
        if not r.get("hit"): continue
        p=f"{d}/raw/{r['mode']}/{r['stem']}.json"
        if not os.path.exists(p): c["noraw"]+=1; continue
        rec=json.load(open(p))
        oc=[o for o in rec.get("offending",[]) if o["term"]=="over_clean"]
        if not oc: continue
        pl={(x["struct"],x["line"]):x for x in rec.get("per_line",[])} if isinstance(rec.get("per_line"),list) else {}
        claimed=all(pl.get((o["struct"],o["line"]),{}).get("claimed_by_older",0)>0 for o in oc)
        c["over_clean_claimed" if claimed else "over_clean_NOCLAIM"]+=1
        if not claimed: ex.append((r["mode"],r["stem"],r.get("cache_setup"),r.get("terms_fired"),[(o["struct"],o["line"]) for o in oc]))
    print(os.path.basename(d), dict(c)); [print("   ",e) for e in ex]
