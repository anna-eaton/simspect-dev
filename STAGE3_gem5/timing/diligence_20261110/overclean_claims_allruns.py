import json, os, glob, collections
roots=glob.glob("/tests/simspect_alloy_20261108/oldfanout/runs/*")+glob.glob("/tests/simspect_alloy_20261108/results_fv2/T2*")
for d in sorted(set(roots)):
    if os.path.islink(d) or not os.path.isdir(d+"/raw"): continue
    n=0; noc=[]
    for p in glob.glob(d+"/raw/*/*.json"):
        if os.path.islink(p): continue
        try: rec=json.load(open(p))
        except: continue
        oc=[o for o in rec.get("offending",[]) if o.get("term")=="over_clean"]
        if not oc: continue
        n+=1
        pl={(x["struct"],x["line"]):x for x in rec.get("per_line",[])}
        bad=[o for o in oc if pl.get((o["struct"],o["line"]),{}).get("claimed_by_older",0)==0]
        if bad: noc.append((p.split("/raw/")[1], rec.get("cache_setup"), [(o["struct"],o["line"]) for o in bad], [pl.get((o["struct"],o["line"])) for o in bad][:1]))
    if n: print(d, "over_clean recs", n, "no-claim", len(noc)); [print("   ",x) for x in noc]
