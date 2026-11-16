import json,collections,os,sys
F="/tests/simspect_alloy_20261108/firstdet_final/"
m=F+"T2u5_Footprint_6_u_core_lpP_fv3_merged"
rows=[json.loads(l) for l in open(m+"/results.jsonl")]
cls={}
for fn in ("classes.jsonl","classes_rmw.jsonl"):
    if os.path.exists(m+"/"+fn):
        for l in open(m+"/"+fn):
            c=json.loads(l); cls.setdefault(fn,{})[(c["mode"],c["stem"])]=c["sigs"]
print("tests",len(rows),"status",dict(collections.Counter(r["status"] for r in rows)))
print("timing x setup:",dict(collections.Counter((r.get("timing_mode"),r.get("cache_setup")) for r in rows)))
for r in rows:
    if r["hit"]:
        p="%s/raw/%s/%s.json"%(m,r["mode"],r["stem"]); rec=json.load(open(p)) if os.path.exists(p) else {}
        s=json.dumps(rec)
        print("HIT",r["idx"],r["stem"],r.get("timing_mode"),r.get("cache_setup"),r.get("stall_points"),"terms",r.get("terms_fired"),
              "sigs",cls.get("classes.jsonl",{}).get((r["mode"],r["stem"])),cls.get("classes_rmw.jsonl",{}).get((r["mode"],r["stem"])),
              "over_clean items",sum(1 for it in rec.get("offending") or [] if it.get("term")=="over_clean"),
              "claimed_by_older>0",[k for k in ("claimed_by_older\": 1","claimed_by_older\": 2","claimed_by_older\": 3") if k in s])
terms=collections.Counter(t for r in rows for t in (r.get("terms_fired") or []))
print("terms over all 690:",dict(terms))
