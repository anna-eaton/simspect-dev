import json, collections, sys
sys.path.insert(0, "/tests/simspect_alloy_20261108/firstdet_final/code/STAGE3_gem5/timing")
import uv5_estimate as u
F = "/tests/simspect_alloy_20261108/firstdet_final/"
M = F + "T2g_Footprint_6_u_core_lpP_fv3_merged"
C = set(open(F + "uv5diag/C_stems_nt.txt").read().split()); D = set(open(F + "uv5diag/D_stems_nt.txt").read().split())
rows = [json.loads(l) for l in open(M + "/results.jsonl")]
cls = {json.loads(l)["idx"]: json.loads(l)["sigs"] for l in open(M + "/classes_rmw.jsonl")}
pend = [r for r in rows if r["hit"] and r["idx"] not in cls]
isC = lambda r: r["mode"] == "mispredict_not_taken" and r["stem"] in C
N = len(rows); K = sum("UV5" in cls.get(r["idx"], []) for r in rows)
c_rows = [r for r in rows if isC(r)]; nc_rows = [r for r in rows if not isC(r)]
Kc = sum("UV5" in cls.get(r["idx"], []) for r in c_rows); Knc = sum("UV5" in cls.get(r["idx"], []) for r in nc_rows)
hits = [(r["mode"], r["stem"], r["cache_setup"], r.get("timing_point"), "D" if r["stem"] in D and r["mode"].endswith("not_taken") else ("C" if isC(r) else "nonC")) for r in rows if "UV5" in cls.get(r["idx"], [])]
print("T2g tests run (both hosts):", N, "of 50232; pending-classification hits:", len(pend))
print("status", dict(collections.Counter(r["status"] for r in rows)))
print("UV5 K =", K, "of N =", N, "-> expected", round((N + 1) / (K + 1), 1), "multiple", round(224000 / ((N + 1) / (K + 1)), 2), "CI95 rate", u.cp_interval(K, N))
print("C tests run:", len(c_rows), "of", len(C), "UV5 in C:", Kc, "| non-C tests run:", len(nc_rows), "UV5 in non-C:", Knc)
lo, hi = u.cp_interval(Kc, 50232)
e = (50232 + 1) / (Kc + 1)
print("C-assumption estimate: K=%d / N=50232 -> expected %.0f, multiple %.1fx, 95%% multiple [%.2f, %.1f]" % (Kc, e, 224000 / e, 224000 * lo, 224000 * hi))
print("UV5 hits:", hits)
for b in ("UV3", "UV4"):
    k = sum(b in cls.get(r["idx"], []) for r in rows)
    print(b, "in T2g (priority order, not a seed prefix):", k, "/", N)
print("setups of all T2g tests:", dict(collections.Counter(r["cache_setup"] for r in rows)))
