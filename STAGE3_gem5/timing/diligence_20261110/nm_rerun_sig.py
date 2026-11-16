import json,sys,gzip,hashlib
W,M=sys.argv[1],sys.argv[2]
camp={}
for l in open(M+"/results.jsonl"):
    d=json.loads(l); camp[(d["mode"],d["stem"])]=d
def evhash(p):
    h=hashlib.md5(); n=0
    with gzip.open(p,"rt",errors="replace") as f:
        for ln in f:
            if ln.startswith("O3PipeView:simspect:"): h.update(ln.encode()); n+=1
    return h.hexdigest()[:10],n
for line in open(W+"/only8.tsv"):
    m,s=line.split()
    c=camp[(m,s)]
    out=[m[11:]+" "+s]
    for src,base in (("camp",M),("r1",W+"/rerun_1"),("r2",W+"/rerun_2")):
        r=json.load(open(f"{base}/raw/{m}/{s}.json"))
        pl={(p["struct"],p["line"]):p for p in r["per_line"]}
        sig=[]
        for o in r["offending"]:
            p=pl.get((o["struct"],o["line"]),{})
            sig.append(f"{o['struct']}:{o['line']}:{o['term']}:cbo={p.get('claimed_by_older')}:inv={p.get('invalidated')}:dI={p.get('d_install')}:claims={[(x.get('actor_seq'),x.get('owner_seq')) for x in p.get('claims',[])]}")
        tr = c["trace"] if src=="camp" else f"{base}/traces/{m}/{s}.pipeview.txt.gz"
        try: eh=evhash(tr)
        except Exception as e: eh=("ERR",str(e)[:60])
        out.append(f"{src}: leak={r.get('leak')} inc={r.get('inconsistent')} lc={r['lc_retire']} fnc={r['fnc_retire']} ev={eh} {sig}")
    print("\n  ".join(out))
