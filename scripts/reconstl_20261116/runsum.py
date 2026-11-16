# reconstlhook: summary of the store-shadow row's raw records (all shards): status, gate failures, hits per kind / rmw|plain,
# release vs squash tick, transient-X real sends the data-obtained gate scores as not obtained.
import json,glob,sys,collections,os
R=sys.argv[1]; row=sys.argv[2]; rmwf=sys.argv[3]
rmw={l.split("\t")[0] for l in open(rmwf).read().splitlines()[1:] if l}
recs={}
for d in sorted(glob.glob(f"{R}/{row}_sh*__latest")):
    for f in glob.glob(os.path.realpath(d)+"/stl_bypass/_sweep_raw/*.json"):
        try: x=json.load(open(f))
        except Exception: continue
        for r in x if isinstance(x,list) else []:
            recs[r["name"].split("__")[0]]=r
C=collections.Counter(); ex=collections.defaultdict(list)
for s,r in recs.items():
    k=r.get("xmit_kind"); rp="rmw" if s in rmw else "plain"; key=f"{k}/{rp}"
    C[(key,"tests")]+=1; C[(key,"status="+str(r.get("status")))]+=1
    st=r.get("stl") or {}
    for g in ("stl_hold","stl_pred","stl_bypass","stl_squash"):
        if st.get(g) is False: C[(key,"fail_"+g)]+=1
    if r.get("issued_in_window"): C[(key,"HIT")]+=1
    for p in st.get("per_store",[]):
        if p.get("release_tick") and p.get("squash_tick"):
            C[(key,"release==squash" if p["release_tick"]==p["squash_tick"] else "release!=squash")]+=1
    rel=min([p["release_tick"] for p in st.get("per_store",[]) if p.get("release_tick")] or [0])
    t=st.get("xmit_sent_tick") or 0
    if k=="ld" and r.get("status")=="ok" and t and rel and t<rel and not r.get("issued_in_window"):
        C[(key,"sent_in_window_not_obtained")]+=1; ex["sent_not_obtained"].append(s)
print("records", len(recs))
for key in sorted({k for k,_ in C}):
    print(key, {m:n for (k,m),n in sorted(C.items()) if k==key})
json.dump(dict(counts={f"{k}|{m}":n for (k,m),n in C.items()}, examples={k:v[:50] for k,v in ex.items()}), open(sys.argv[4],"w"), indent=1)
