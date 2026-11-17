import sys, re, subprocess
pdf = sys.argv[1]
html = subprocess.run(['pdftotext','-bbox',pdf,'-'],capture_output=True,text=True).stdout
pages = html.split('<page ')[1:]
res=None
for pi,pg in enumerate(pages,1):
    words=[(float(a),float(b),float(c),float(d),t) for a,b,c,d,t in re.findall(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<',pg)]
    rl=[(int(w[4]),w) for w in words if re.fullmatch(r'\d{1,4}',w[4]) and (w[0]<45 or w[0]>560)]
    def row(x):
        left = x[0] < 306
        side=[(n,r) for n,r in rl if (r[0]<45)==left]
        ymid=(x[1]+x[3])/2
        return min(side,key=lambda t:abs((t[1][1]+t[1][3])/2-ymid))[0]
    for i,w in enumerate(words):
        if w[4]=='contents.' and i>0 and words[i-1][4] in ('paper’s',"paper's"):
            res=(pi,row(w))
            for x in words:
                if x[4]=='Acknowledgments': print('ack heading row',row(x))
            break
    if res: break
print('body+ack end: page %d row %d  (over limit by %d)'%(res[0],res[1],res[1]-1276))
