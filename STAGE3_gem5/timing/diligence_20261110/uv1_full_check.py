import json, gzip, collections, os
F="/tests/simspect_alloy_20261108/firstdet_final/T1g_Footprint_6_u_core_lpP_fv3/"
rows={}
for l in open(F+"results.jsonl"):
    r=json.loads(l); rows[r["idx"]]=r
cls=[json.loads(l) for l in open(F+"classes.jsonl")]
sig=collections.Counter(tuple(sorted(c["sigs"])) for c in cls)
print("rows",len(rows),"status",collections.Counter(r["status"] for r in rows.values()),"classified",len(cls))
print("setups", collections.Counter(r["cache_setup"] for r in rows.values()))
print("hit by setup", collections.Counter((r["cache_setup"],r["hit"]) for r in rows.values()))
for k,v in sig.most_common(12): print("  ",v,k)
uv1=[c for c in cls if "UV1" in c["sigs"]]
print("UV1",len(uv1),"UV1 not transient",sum("UV1_transient" not in c["sigs"] for c in uv1),"UV1 by setup",collections.Counter(rows[c["idx"]]["cache_setup"] for c in uv1))
# deep check on first 150 UV1 hits
stats=collections.Counter(); bad=[]
for c in uv1[:150]:
    r=rows[c["idx"]]; raw=json.load(open(f"{F}raw/{r['mode']}/{r['stem']}.json"))
    info=raw["cache_setup_info"]; b=int(info["begin"],16); e=b+int(info["delta"])
    off_ids={i for o in raw["offending"] for i in (o.get("event_ids") or [])}
    evs={}; fetch={}; retire={}; cur=None
    for ln in gzip.open(f"{F}traces/{r['mode']}/{r['stem']}.pipeview.txt.gz","rt"):
        if ln.startswith("O3PipeView:simspect:"):
            p=ln.rstrip().split(":"); kv=dict(x.split("=",1) for x in p[5:] if "=" in x)
            if p[3]=="L1D" and p[4]=="evict" and kv.get("req")=="specld":
                try: evs[int(kv["id"])]=(int(p[2]),kv)
                except: pass
        elif ln.startswith("O3PipeView:fetch:"):
            q=ln.split(":"); cur=int(q[5]); fetch[cur]=int(q[3],16)
        elif ln.startswith("O3PipeView:retire:") and cur is not None:
            retire[cur]=int(ln.split(":")[2]); cur=None
    good=0
    for i in off_ids:
        if i not in evs: continue
        t,kv=evs[i]; seq=int(kv["seq"]); pc=int(kv["pc"],16) if kv.get("pc") not in (None,"-") else fetch.get(seq)
        insetup = pc is not None and b<=pc<e
        sq = retire.get(seq,0)==0
        stats[("setup" if insetup else "test", "squashed" if sq else "committed")]+=1
        if not insetup and sq: good+=1
    stats["hits_with_squashed_test_evict" if good else "hits_WITHOUT"]+=1
    if not good: bad.append((r["mode"],r["stem"]))
print(stats); print(bad[:5])
