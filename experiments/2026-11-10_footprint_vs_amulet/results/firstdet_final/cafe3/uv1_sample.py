import json,hashlib,os,sys
src,dst,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
os.makedirs(dst,exist_ok=True)
rows=[json.loads(l) for l in open(src+"/results.jsonl")]
rows=[r for r in rows if r.get("status")=="ok"]
rows.sort(key=lambda r: hashlib.sha256(("uv1sample:%s:%s"%(r["mode"],r["stem"])).encode()).hexdigest())
pick=rows[:n]
with open(dst+"/results.jsonl","w") as f:
    for r in pick: f.write(json.dumps(r)+"\n")
for d in ("raw","traces"):
    if not os.path.exists(dst+"/"+d): os.symlink(src+"/"+d, dst+"/"+d)
print(len(rows),"ok rows; sampled",len(pick),"hits",sum(r["hit"] for r in pick),"setups",{s:sum(1 for r in pick if r.get("cache_setup")==s) for s in ("warm","full")})
