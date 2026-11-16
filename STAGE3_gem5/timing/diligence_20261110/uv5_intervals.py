import math, random
def gammainc(a,x):  # regularized lower P(a,x)
    if x<=0: return 0.0
    if x<a+1:
        s=t=1.0/a; n=a
        for _ in range(10000):
            n+=1; t*=x/n; s+=t
            if t<s*1e-15: break
        return s*math.exp(-x+a*math.log(x)-math.lgamma(a))
    b=x+1-a; c=1e300; d=1/b; h=d
    for i in range(1,10000):
        an=-i*(i-a); b+=2; d=an*d+b; d=1/d if d else 1e300; c=b+an/c; h*=d*c
        if abs(d*c-1)<1e-15: break
    return 1-math.exp(-x+a*math.log(x)-math.lgamma(a))*h
def gppf(p,a,scale=1.0):
    lo,hi=0.0,1000.0
    for _ in range(200):
        m=(lo+hi)/2
        if gammainc(a,m)<p: lo=m
        else: hi=m
    return (lo+hi)/2*scale
def pc(k): return (gppf(0.025,k) if k else 0.0, gppf(0.975,k+1))
N=50232; A=224000
K1,N1,N1t=2,10849,10849; K2,N2,N2t=1,12277,39383
w1=N1t/N1; w2=N2t/N2
y=K1*w1+K2*w2; v=K1*w1**2+K2*w2**2; wM=max(w1,w2)
lo=gppf(0.025, y*y/v, v/y); hi=gppf(0.975,(y+wM)**2/(v+wM**2),(v+wM**2)/(y+wM))
print("EK %.2f  Fay-Feuer EK CI %.2f-%.2f  multiple %.1f (%.1f-%.1f)  tests %.0f (%.0f-%.0f)"%(y,lo,hi,A*y/N,A*lo/N,A*hi/N,N/y,N/hi,N/lo))
l2,h2=pc(K2); print("existing (K1 fixed): EK %.2f-%.2f multiple %.1f-%.1f"%(K1+l2*w2,K1+h2*w2,A*(K1+l2*w2)/N,A*(K1+h2*w2)/N))
# Bayesian Jeffreys MC
random.seed(1); s=[]
for _ in range(200000):
    s.append(random.gammavariate(K1+0.5,1)*w1+random.gammavariate(K2+0.5,1)*w2)
s.sort(); print("Jeffreys MC EK 95%% %.2f-%.2f multiple %.1f-%.1f"%(s[5000],s[195000],A*s[5000]/N,A*s[195000]/N))
for K,n,lab in [(3,23126,"T2g naive (biased: C-first)"),(2,32267,"T2rt pre-priority, stream order")]:
    l,h=pc(K); exp=(n+1)/(K+1); print("%s: exp %.0f mult %.1f, MLE mult %.1f, 95%% mult %.1f-%.1f"%(lab,exp,A/exp,A*K/n,A*l/n,A*h/n))
# program-cluster: 2 distinct programs (inst-021207, inst-007645) among 25116 programs
for cpu in (6.45,):
    for gen in (0,3.02):
        print("UV5 CPU multiple (cpu/test %.2f + gen %.2f): %.3f"%(cpu,gen,6171/(N/y*(cpu+gen))))
print("programs-unit multiples: UV1 %.1f UV3 %.2f UV4 %.1f UV5 %.2f UV6 %.1f jmp %.1f"%(23.7/2.05,27.1/24.2,1600/81.5,1600/(N/y),42.7/4.98,136/6.74))
print("UV5 multiple with AMuLeT non-exclusive (1280 prog): %.1f; UV4 non-excl (1067): %.0f"%(1280*140/(N/y),1067*140/81.5))
