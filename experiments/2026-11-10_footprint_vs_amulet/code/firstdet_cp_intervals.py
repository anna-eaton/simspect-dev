"""95% Clopper-Pearson intervals for the ISCA-27 first-detection figure (tikz/firstdet_bars_v2_body.tex), tests per detection = 1/rate.
K/N from wiki/state/EVAL_MANIFEST.md part 7 "Complete run" (SimSpect) and AMuLeT K of 896,000 pooled test cases. Pure Python (no scipy). Run: python3 -I firstdet_cp_intervals.py"""
from math import lgamma, log, exp, log10

def binom_cdf(k, n, p):
    # P(X <= k), X ~ Bin(n, p), summed in log space
    if p <= 0: return 1.0
    if p >= 1: return 1.0 if k >= n else 0.0
    lp, lq = log(p), log(1 - p)
    base = lgamma(n + 1)
    terms = [base - lgamma(i + 1) - lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(k + 1)]
    m = max(terms)
    return min(1.0, exp(m) * sum(exp(t - m) for t in terms))

def solve(f, target, lo=1e-12, hi=1 - 1e-12):
    # f decreasing in p; find p with f(p) = target (bisection in log p)
    a, b = log(lo), log(hi)
    for _ in range(200):
        mid = (a + b) / 2
        if f(exp(mid)) > target: a = mid
        else: b = mid
    return exp((a + b) / 2)

def cp(k, n, alpha=0.05):
    hi = solve(lambda p: binom_cdf(k, n, p), alpha / 2)
    lo = 0.0 if k == 0 else solve(lambda p: binom_cdf(k - 1, n, p), 1 - alpha / 2)
    return lo, hi

sim = {'UV1': (2002, 4000), 'UV3': (1861, 50232), 'UV4': (599, 50232), 'UV5': (4, 50232), 'UV6': (861, 4000), 'jmp': (555, 4000)}
amuK = {'UV1': 270, 'UV3': 236, 'UV4': 4, 'UV5': 4, 'UV6': 150, 'jmp': 47}
NA = 896000
for b in sim:
    for side, (k, n) in (('S', sim[b]), ('A', (amuK[b], NA))):
        est = (n + 1) / (k + 1)
        lo, hi = cp(k, n)
        print(f"{b:4} {side} K={k:5} N={n:6} est={est:9.2f} log={log10(est):.4f} 95%=[{1/hi:9.1f},{1/lo:9.1f}] log=[{log10(1/hi):.4f},{log10(1/lo):.4f}]")
