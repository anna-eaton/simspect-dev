import json,sys,collections
d=json.load(open(sys.argv[1]))
tot=collections.Counter(); stems=collections.defaultdict(set); rsa=collections.Counter()
for k,v in d.items():
    parts=k.split('/'); stem=parts[-1]
    tot['all']+=1
    if v.startswith('R-SA-13'):
        rsa[v]+=1; tot['rsa13']+=1; stems['rsa13'].add(stem)
        tot['rsa13_'+parts[0]]+=1; tot['rsa13_kind_'+parts[1]+'/'+parts[2]]+=1
        if v=='R-SA-13' or 'via FP elsewhere' in v or 'replay' in v: tot['rsa13_twinverified']+=1
    stems['all'].add(stem)
print(dict(tot)); print(dict(rsa)); print('programs all',len(stems['all']),'programs rsa13',len(stems['rsa13']))
