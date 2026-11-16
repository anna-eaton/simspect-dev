import argparse
import glob
import sys
import json
import os
import statistics
from math import exp, lgamma, log

BUGS = ["UV1", "UV3", "UV4", "UV5", "UV6", "jmp_shadow"]
DEFENSE = {"UV1": "InvisiSpec", "UV3": "CleanupSpec", "UV4": "CleanupSpec", "UV5": "CleanupSpec", "UV6": "SpecLFB",
           "jmp_shadow": "SpecLFB"}
ROW = {"InvisiSpec": "T1g", "CleanupSpec": "T2g", "SpecLFB": "T3g"}
INPUTS_PER_PROGRAM = 140


def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = log(p), log(1 - p)
    base = lgamma(n + 1)
    terms = [base - lgamma(i + 1) - lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(k + 1)]
    m = max(terms)
    return min(1.0, exp(m) * sum(exp(t - m) for t in terms))


def solve(f, target, lo=1e-12, hi=1 - 1e-12):
    a, b = log(lo), log(hi)
    for _ in range(200):
        mid = (a + b) / 2
        if f(exp(mid)) > target:
            a = mid
        else:
            b = mid
    return exp((a + b) / 2)


def cp(k, n, alpha=0.05):
    hi = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p), alpha / 2)
    lo = 0.0 if k == 0 else solve(lambda p: binom_cdf(k - 1, n, p), 1 - alpha / 2)
    return lo, hi


def ratio_ci(ks, ns, ka, na):
    plo, phi = cp(ks, ks + ka)
    odds = lambda p: p / (1 - p)
    return odds(plo) * na / ns, odds(phi) * na / ns


def simspect_cpu(root, row, suffix):
    d = os.path.join(root, "simspect", f"{row}_p16{suffix}")
    rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl")) if l.strip()]
    ok = [r["total_cpu_s"] for r in rows if r.get("total_cpu_s") is not None]
    startup = 0.0
    wj = os.path.join(d, "fastpath_workers.jsonl")
    if os.path.exists(wj):
        startup = sum(json.loads(l).get("startup_cpu_s", 0) for l in open(wj) if '"spawn"' in l)
    return statistics.mean(ok) + startup / len(ok)


def amulet_cpu(root, D):
    runs = sorted(glob.glob(os.path.join(root, "amulet", "runs", f"{D}_r*", "t5_summary.json")))
    if not runs:
        sys.exit(f"compare: no AMuLeT timing run summary for {D} under {root}/amulet/runs (run make amulet-timing first)")
    return json.load(open(runs[-1]))["cpu_s_per_program"] / INPUTS_PER_PROGRAM


def amulet_kn(hits_root):
    pb = os.path.join(hits_root, "perbug", "perbug_summary.json")
    if not os.path.exists(pb):
        sys.exit(f"compare: no AMuLeT per-bug summary at {pb} (run make amulet-hits first)")
    rep = json.load(open(pb))
    k = {}
    for b in BUGS:
        D = DEFENSE[b]
        r = rep.get(D, {})
        v = r.get("violations_with_jmp_shadow") if b == "jmp_shadow" else r.get("per_bug", {}).get(b, {}).get("violations_with_bug")
        if v is None:
            sys.exit(f"compare: {pb} has no count for {b} ({D})")
        k[b] = v
    progs = []
    for D in ("InvisiSpec", "CleanupSpec", "SpecLFB"):
        s = sorted(glob.glob(os.path.join(hits_root, "runs", f"{D}_r*", "t5_summary.json")))
        if not s:
            sys.exit(f"compare: no AMuLeT hits run summary for {D} under {hits_root}/runs")
        progs.append(json.load(open(s[-1]))["total_programs"])
    if len(set(progs)) != 1:
        sys.exit(f"compare: AMuLeT hits runs differ in program count {progs}")
    return k, progs[0] * INPUTS_PER_PROGRAM, pb


def compute(sim, amuK, NA, sim_cpu, amu_cpu, gen):
    out = []
    for b in BUGS:
        D = DEFENSE[b]
        k, n = sim[b]
        ka = amuK[b]
        st, at = (n + 1) / (k + 1), (NA + 1) / (ka + 1)
        slo, shi = cp(k, n)
        alo, ahi = cp(ka, NA)
        s_int, a_int = (1 / shi, 1 / slo), (1 / ahi, 1 / alo)
        ex, tot, am = sim_cpu[D], sim_cpu[D] + gen, amu_cpu[D]
        rlo, rhi = ratio_ci(k, n, ka, NA)
        out.append(dict(bug=b, defense=D, K=k, N=n, simspect_tests=st, simspect_tests_95=s_int, amulet_K=ka, amulet_N=NA,
                        amulet_test_cases=at, amulet_test_cases_95=a_int, tests_ratio=at / st, tests_ratio_95=[rlo, rhi],
                        simspect_cpu_per_test=ex, generation_cpu_per_test=gen, amulet_cpu_per_test_case=am,
                        simspect_s_exec=st * ex, simspect_s_with_gen=st * tot, amulet_s=at * am,
                        time_ratio_exec=(at * am) / (st * ex), time_ratio_with_gen=(at * am) / (st * tot),
                        time_ratio_with_gen_95=[rlo * am / tot, rhi * am / tot]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timing_root")
    ap.add_argument("--kn-json", required=True)
    ap.add_argument("--amulet-hits", required=True)
    ap.add_argument("--gen", type=float, required=True)
    ap.add_argument("--suffix", default="_fast")
    ap.add_argument("--out", required=True)
    ap.add_argument("--txt", required=True)
    a = ap.parse_args()
    kn = json.load(open(a.kn_json))
    kn = next(iter(kn.values()))
    sim = {b: (kn[b][1], kn[b][2]) for b in BUGS}
    sim_cpu = {D: simspect_cpu(a.timing_root, ROW[D], a.suffix) for D in ROW}
    amu_cpu = {D: amulet_cpu(a.timing_root, D) for D in ROW}
    amuK, NA, src = amulet_kn(a.amulet_hits)
    rows = compute(sim, amuK, NA, sim_cpu, amu_cpu, a.gen)
    json.dump(dict(simspect_cpu=sim_cpu, amulet_cpu=amu_cpu, amulet_K_source=src, gen=a.gen, rows=rows), open(a.out, "w"), indent=1)
    L = [f"{'bug':10} {'defense':11} {'K/N':>16} {'S tests':>9} {'A tests':>9} {'tests x':>9} {'S s exec':>10} {'S s +gen':>10} {'A s':>9} {'time x exec':>11} {'time x +gen':>11}"]
    for r in rows:
        L.append(f"{r['bug']:10} {r['defense']:11} {r['K']:>7,}/{r['N']:<8,} {r['simspect_tests']:9.2f} {r['amulet_test_cases']:9.1f} "
                 f"{r['tests_ratio']:9.1f} {r['simspect_s_exec']:10.1f} {r['simspect_s_with_gen']:10.1f} {r['amulet_s']:9.1f} "
                 f"{r['time_ratio_exec']:11.3f} {r['time_ratio_with_gen']:11.3f}")
    open(a.txt, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
