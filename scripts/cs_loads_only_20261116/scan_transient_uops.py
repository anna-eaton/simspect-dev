import gzip,re,sys,collections
# For each CleanupSpec trace: map seq -> (disasm, retire_tick); count L1D/L2 cache events by actor micro-op
# that happen before the actor retires (or actor never retires) = speculative/transient events.
tot=collections.Counter(); ex={}
for fn in sys.argv[1:]:
    seqinfo={}; cur=None; events=[]
    for line in gzip.open(fn,'rt',errors='replace'):
        if line.startswith('O3PipeView:fetch:'):
            p=line.rstrip('\n').split(':',6)
            seq=int(p[5]); cur=seq; seqinfo[seq]=[p[6].strip(),None]
        elif line.startswith('O3PipeView:retire:') and cur is not None:
            p=line.split(':'); seqinfo[cur][1]=int(p[2]); cur=None
        elif line.startswith('O3PipeView:simspect:'):
            m=re.match(r'O3PipeView:simspect:(\d+):(L1D|L2):(\w+):.*?seq=(\d+|-):',line)
            if m and m.group(4)!='-':
                req=re.search(r'req=(\w+)',line)
                events.append((int(m.group(1)),m.group(2),m.group(3),int(m.group(4)),req.group(1) if req else '-'))
    for t,s,k,seq,req in events:
        if k not in ('miss','fill','evict','hit','upgrade','install','repl_touch'):
            continue
        d,ret=seqinfo.get(seq,['?',None])
        transient = (ret is None or ret==0 or t<ret)
        if not transient: continue
        uop=d.split(':',1)[1].split()[0] if ':' in d else d
        macro=d.split(':',1)[0].strip()
        key=(s,k,req,uop)
        tot[key]+=1; ex.setdefault(key,(fn.split('/')[-1],seq,d,t,ret))
for k,v in sorted(tot.items(),key=lambda x:-x[1]): print(v,k,ex[k])
