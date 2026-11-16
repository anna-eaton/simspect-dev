"""Stratified UV5 estimate (main estimator): stratum 1 = C(+D) not_taken stems (all run),
stratum 2 = every other test (run in seed order = a uniform sample), scaled to its total. No shape assumption."""
import json, math, sys, collections
F = "/tests/simspect_alloy_20261108/firstdet_final/"
M = F + "T2g_Footprint_6_u_core_lpP_fv3_merged"
NTOT = 50232
C = set(open(F + "uv5diag/C_stems_nt.txt").read().split())
rows = [json.loads(l) for l in open(M + "/results.jsonl")]
cls = {json.loads(l)["idx"]: json.loads(l)["sigs"] for l in open(M + "/classes_rmw.jsonl")}
pend = sum(1 for r in rows if r["hit"] and r["idx"] not in cls)
s1 = lambda r: r["mode"] == "mispredict_not_taken" and r["stem"] in C
N1_total = len(C); N2_total = NTOT - N1_total
r1 = [r for r in rows if s1(r)]; r2 = [r for r in rows if not s1(r)]
K1 = sum("UV5" in cls.get(r["idx"], []) for r in r1); K2 = sum("UV5" in cls.get(r["idx"], []) for r in r2)
N1, N2 = len(r1), len(r2)
def chi2_ppf(p, k):  # Poisson exact via bisection on the gamma CDF (series)
    pass
def pois_cdf(k, lam):
    s, t = 0.0, math.exp(-lam)
    for i in range(k + 1):
        if i > 0: t *= lam / i
        s += t
    return s
def pois_ci(k, a=0.05):
    def bis(f, lo, hi):
        for _ in range(200):
            m = (lo + hi) / 2
            if f(m): hi = m
            else: lo = m
        return (lo + hi) / 2
    lo = 0.0 if k == 0 else bis(lambda l: 1 - pois_cdf(k - 1, l) >= a / 2, 0.0, 100.0 + 10 * k)
    hi = bis(lambda l: pois_cdf(k, l) <= a / 2, 0.0, 100.0 + 10 * k)
    return lo, hi
scale = N2_total / N2 if N2 else float("inf")
EK = K1 * (N1_total / N1 if N1 else 0) + K2 * scale
lo2, hi2 = pois_ci(K2)
s1scale = N1_total / N1 if N1 else 0
EKlo, EKhi = K1 * s1scale + lo2 * scale, K1 * s1scale + hi2 * scale
rate = EK / NTOT
def mult(ek): return 224000 * ek / NTOT
hits = [(r["mode"], r["stem"], r["cache_setup"], r.get("timing_point"), "S1" if s1(r) else "S2") for r in rows if "UV5" in cls.get(r["idx"], [])]
res = dict(estimator="stratified: E[UV5 count] = K1*(N1_total/N1_run) + K2*(N2_total/N2_run); S1 = static same-line (class C, includes D) not_taken stems, S2 = all other tests (seed-order sample)",
           K1=K1, N1_run=N1, N1_total=N1_total, K2=K2, N2_run=N2, N2_total=N2_total, hits_pending_classification=pend,
           expected_uv5_in_corpus=round(EK, 2), rate=rate, expected_tests=round(1 / rate, 1) if rate else None,
           multiple=round(mult(EK), 2), ci95_note="Poisson exact interval on K2, scaled by N2_total/N2_run, plus K1 (scaled by N1_total/N1_run)",
           expected_uv5_ci95=[round(EKlo, 2), round(EKhi, 2)],
           expected_tests_ci95=[round(NTOT / EKhi, 1) if EKhi else None, round(NTOT / EKlo, 1) if EKlo else None],
           multiple_ci95=[round(mult(EKlo), 2), round(mult(EKhi), 2)], uv5_hits=hits,
           T2g_tests_run=len(rows), setups=dict(collections.Counter(r["cache_setup"] for r in rows)))
open(F + "report/uv5_latest.json", "w").write(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
