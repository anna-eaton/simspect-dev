import re,sys
rows=[]
for l in open(sys.argv[1]):
    m=re.match(r'p(\d+) r(\d+) x\s*([\d.]+)-\s*([\d.]+) h\s*([\d.]+) \| (.*)',l)
    if not m: continue
    p,r,x0,x1,h,t=m.groups(); p=int(p); r=int(r); x0=float(x0); x1=float(x1); h=float(h)
    if not (11.2<h<12.2): continue
    if p>12: continue
    left = x0<306
    edge = 294 if left else 558
    start = 54 if left else 318
    fill=(x1-start)/(edge-start)
    if fill<0.93: print(f"p{p} r{r} fill{fill:4.2f} | {t[:90]}")
