import sys, re, subprocess, html as H
pdf=sys.argv[1]; maxpage=int(sys.argv[2]) if len(sys.argv)>2 else 13
out=subprocess.run(['pdftotext','-bbox-layout','-l',str(maxpage),pdf,'-'],capture_output=True,text=True).stdout
pages=out.split('<page ')[1:]
for pi,pg in enumerate(pages,1):
    # ruler
    words=re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',pg)
    ruler=[(float(a),(float(b)+float(d))/2,int(t)) for a,b,c,d,t in words if re.fullmatch(r'\d{1,4}',t) and (float(a)<45 or float(a)>560)]
    L=[r for r in ruler if r[0]<45]; R=[r for r in ruler if r[0]>560]
    for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>',pg,re.S):
        x0,y0,x1,y1=map(float,m.groups()[:4])
        ws=re.findall(r'>([^<]*)</word>',m.group(5))
        txt=H.unescape(' '.join(ws))
        if x0<45 or x0>560: continue
        side=L if x0<306 else R
        if not side: continue
        ym=(y0+y1)/2
        row=min(side,key=lambda r:abs(r[1]-ym))[2]
        print(f"p{pi} r{row} x{x0:5.0f}-{x1:5.0f} h{y1-y0:4.1f} | {txt}")
