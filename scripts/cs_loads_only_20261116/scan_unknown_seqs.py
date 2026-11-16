import gzip,re,sys,collections,bisect
res=collections.Counter(); per=[]
for fn in sys.argv[1:]:
    info={};cur=None;ev=[]
    for line in gzip.open(fn,'rt',errors='replace'):
        if line.startswith('O3PipeView:fetch:'):
            p=line.rstrip('\n').split(':',6); cur=int(p[5]); info[cur]=[p[6].strip(),None]
        elif line.startswith('O3PipeView:retire:') and cur is not None:
            info[cur][1]=int(line.split(':')[2]); cur=None
        elif line.startswith('O3PipeView:simspect:'):
            m=re.match(r'O3PipeView:simspect:(\d+):(L1D|L2):(miss|fill|hit|repl_touch|evict|upgrade):.*?seq=(\d+):',line)
            if m: ev.append((int(m.group(1)),int(m.group(4)),(re.search(r'req=(\w+)',line) or [0,'-'])[1]))
    ks=sorted(info)
    for t,seq,req in ev:
        if seq in info: continue
        i=bisect.bisect_left(ks,seq); lo=ks[i-1] if i>0 else None; hi=ks[i] if i<len(ks) else None
        lor=info[lo][1] if lo else None; hir=info[hi][1] if hi else None
        committed = bool(lor) and bool(hir)   # both neighbours retired -> seq itself retired (in-order commit)
        res[(req,'neighbours_committed' if committed else 'neighbour_squashed_or_unknown', 'after_lo_retire' if lor and t>=lor else 'before')]+=1
        if not committed: per.append((fn.split('/')[-1],seq,t,req,lo,lor,hi,hir))
print(res); print(per[:20])
