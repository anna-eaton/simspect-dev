import gzip,sys,re
# usage: pv.py trace.gz line seq1,seq2,...  -> per seq: pc, disasm, retire tick; plus hook events on line (non-hit/touch noise filtered)
tr,line,seqs=sys.argv[1],sys.argv[2],[int(x) for x in sys.argv[3].split(",") if x]
info={}; cur=None; evs=[]
with gzip.open(tr,"rt",errors="replace") as f:
    for ln in f:
        if ln.startswith("O3PipeView:fetch:"):
            p=ln.rstrip("\n").split(":",6)
            cur=int(p[5]); info[cur]={"pc":p[3],"dis":p[6].strip(),"fetch":int(p[2]),"retire":None}
        elif ln.startswith("O3PipeView:retire:") and cur is not None:
            info[cur]["retire"]=int(ln.split(":")[2])
        elif ln.startswith("O3PipeView:simspect:") and ("line="+line+":") in ln:
            if any(k in ln for k in (":fill:",":cleanup",":inv:",":hit:",":miss:",":evict",":coh:")) and ":LSQ:" not in ln and "L2:miss" not in ln:
                evs.append(ln.strip()[len("O3PipeView:simspect:"):])
for s in seqs:
    i=info.get(s); print("seq",s,i)
for e in evs:
    print("  ",re.sub(r":victim=-:cause=-|:sq=-|:size=\d+","",e)[:200])
