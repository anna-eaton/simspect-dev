import json, collections, sys, os
F="/tests/simspect_alloy_20261108/firstdet_final/"
D=set(open(F+"uv5diag/D_stems_nt.txt").read().split())
dirs=[F+"T2rt_Footprint_6_u_core_lpP_fv3", F+"T2rt_Footprint_6_u_core_lpP_fv3_cafe1"]
rows=[]
for d in dirs:
    for l in open(d+"/results.jsonl"):
        r=json.loads(l); r["_d"]=d; rows.append(r)
cls={}
m=F+"T2rt_Footprint_6_u_core_lpP_fv3_merged/classes_rmw.jsonl"
if os.path.exists(m):
    for l in open(m):
        c=json.loads(l); cls[(c["mode"],c["stem"])]=c["sigs"]
def raw(r):
    p="%s/raw/%s/%s.json"%(r["_d"],r["mode"],r["stem"])
    return json.load(open(p)) if os.path.exists(p) else None
def scan(rec):
    oc=0; cbo=0; inv=0
    for it in rec.get("offending") or []:
        if it.get("term")=="over_clean": oc+=1
        for pl in (it.get("per_line") or {}).values() if isinstance(it.get("per_line"),dict) else (it.get("per_line") or []):
            if isinstance(pl,dict):
                cbo+= (pl.get("claimed_by_older") or 0)>0
    s=json.dumps(rec)
    return oc, cbo, s.count('"claimed_by_older": 1')+s.count('"claimed_by_older": 2'), s.count("over_clean")
print("CleanupSpec rows (cafe3+cafe1):",len(rows))
dn=[r for r in rows if r["mode"]=="mispredict_not_taken" and r["stem"] in D]
print("(a) D-shaped not_taken tests run:",len(dn),"of 690; by setup:",dict(collections.Counter(r.get("cache_setup") for r in dn)))
print("    D-shaped hits by setup:",dict(collections.Counter(r.get("cache_setup") for r in dn if r.get("hit"))))
cold=[r for r in dn if r.get("cache_setup")=="cold"]
print("(b) D-shaped cold:",len(cold),"hits:",sum(r["hit"] for r in cold))
for r in cold:
    if r.get("hit"):
        rec=raw(r); sc=scan(rec) if rec else None
        print("   ",r["stem"],"terms",r.get("terms_fired"),"sigs",cls.get((r["mode"],r["stem"])),"over_clean items/claimed_by_older lines/raw mentions",sc,
              "n_offending",len((rec or {}).get("offending") or []))
terms=collections.Counter(t for r in rows for t in (r.get("terms_fired") or []))
print("(c) terms_fired over all CleanupSpec rows:",dict(terms))
oc=0; cb=0; nraw=0
for r in rows:
    if r.get("hit"):
        rec=raw(r)
        if rec: nraw+=1; s=json.dumps(rec); oc+=sum(1 for it in rec.get("offending") or [] if it.get("term")=="over_clean"); cb+=('claimed_by_older": 0' not in s and "claimed_by_older" in s)
print("    over_clean offending items in raw hit records:",oc,"(raw records read:",nraw,"); records with nonzero claimed_by_older mention:",cb)
print("    UV5 in classes_rmw:",sum("UV5" in v for v in cls.values()),"of",len(cls),"classified hits")
