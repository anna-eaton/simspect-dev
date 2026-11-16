import argparse
import gzip
import json
import sys
from math import exp, lgamma, log
from pathlib import Path

BUGS = ["UV1", "UV3", "UV4", "UV5", "UV6", "jmp_shadow"]
DEFENSE = {"UV1": "InvisiSpec", "UV3": "CleanupSpec", "UV4": "CleanupSpec", "UV5": "CleanupSpec", "UV6": "SpecLFB",
           "jmp_shadow": "SpecLFB"}
DIR = {"InvisiSpec": "invisispec", "CleanupSpec": "cleanupspec", "SpecLFB": "speclfb"}
INPUTS_PER_PROGRAM = 140
CS_RUNS = [("main", 50232, 1274, 162, 0), ("extra_new", 90932, 1930, 237, 1), ("round1", 50232, 1400, 181, 2),
           ("round2", 50232, 1338, 167, 2), ("round3", 50232, 1346, 172, 0)]
EXPECT = {
    "pooled": (291860, 7288, 919, 5),
    "small": {"invisispec": (4000, {"UV1": 2002}), "speclfb": (4000, {"UV6": 851, "walk_order": 657, "jmp_shadow": 527})},
    "sim_cpu": {"InvisiSpec": 1.344, "CleanupSpec": 1.738, "SpecLFB": 1.2956},
    "amu_cpu": {"InvisiSpec": 0.07304, "CleanupSpec": 0.02337, "SpecLFB": 0.01935},
    "amu_k": {"UV1": 270, "UV3": 236, "UV4": 4, "UV5": 4, "UV6": 150, "jmp_shadow": 47},
    "amu_n": 896000,
    "gen": 0.93,
    "tests_x": {"UV1": 1655.2, "UV3": 94.4, "UV4": 564.9, "UV5": 3.684, "UV6": 1263.6, "jmp_shadow": 2463.4},
    "cpu_x_gen": {"UV1": 53.165, "UV3": 0.827, "UV4": 4.949, "UV5": 0.0323, "UV6": 10.988, "jmp_shadow": 21.422},
    "cpu_x_exec": {"UV1": 89.954, "UV3": 1.270, "UV4": 7.597, "UV5": 0.0497, "UV6": 18.876, "jmp_shadow": 36.799},
    "labels_tests": {"UV1": "1700", "UV3": "94", "UV4": "560", "UV5": "3.7", "UV6": "1300", "jmp_shadow": "2500"},
    "labels_gen": {"UV1": "53", "UV3": "0.83", "UV4": "4.9", "UV5": "0.032", "UV6": "11", "jmp_shadow": "21"},
    "labels_exec": {"UV1": "90", "UV3": "1.3", "UV4": "7.6", "UV5": "0.050", "UV6": "19", "jmp_shadow": "37"},
    "uv5_time_95": (0.0072, 0.169),
    "e2w": (30368, 24, 22, 1690),
}
bad = []


def rows(p):
    p = Path(p)
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def n_ok(d):
    return len({(r["mode"], r["stem"]) for r in rows(d / "results.jsonl.gz") if r.get("status") == "ok"})


def count(d, fname, sig):
    return len({(r["mode"], r["stem"]) for r in rows(d / fname) if sig in r.get("sigs", [])})


def check(label, got, want, tol=0.0, rel=0.0):
    ok = abs(got - want) <= max(tol, rel * abs(want))
    print(f"  {'OK ' if ok else 'BAD'} {label}: {got} (expected {want})")
    if not ok:
        bad.append(label)


def check_eq(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'BAD'} {label}: {got} (expected {want})")
    if not ok:
        bad.append(label)


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


def rlab(r):
    if r >= 1:
        s = f"{float(f'{r:.2g}'):g}"
        if r < 10 and "." not in s:
            s += ".0"
        return s
    s = f"{r:.2g}"
    if len(s.replace("0.", "").lstrip("0")) == 1:
        s += "0"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[2] / "data"))
    a = ap.parse_args()
    D = Path(a.data)
    rec = D / "records"

    print("== CleanupSpec pool (A-UV3 / A-UV4 / A-UV5), classes_rmw.jsonl")
    tot = [0, 0, 0, 0]
    for name, n_w, k3, k4, k5 in CS_RUNS:
        d = rec / name / "cleanupspec"
        n = n_ok(d)
        k = [count(d, "classes_rmw.jsonl.gz", s) for s in ("UV3", "UV4", "UV5")]
        print(f"  {name:10} N={n:,} UV3={k[0]:,} UV4={k[1]:,} UV5={k[2]}")
        check(f"{name} N", n, n_w)
        for s, g, w in zip(("UV3", "UV4", "UV5"), k, (k3, k4, k5)):
            check(f"{name} {s} K", g, w)
        for i, v in enumerate([n] + k):
            tot[i] += v
    for lab, g, w in zip(("pooled N", "pooled A-UV3 K", "pooled A-UV4 K", "pooled A-UV5 K"), tot, EXPECT["pooled"]):
        check(lab, g, w)

    print("== InvisiSpec / SpecLFB, first 4,000 seed-order tests of the main corpus, classes.jsonl")
    small = {}
    for dfn, (n_w, ks) in EXPECT["small"].items():
        d = rec / "main" / dfn
        check(f"{dfn} N", n_ok(d), n_w)
        for s, w in ks.items():
            g = count(d, "classes.jsonl.gz", s)
            small[s] = (g, n_ok(d))
            check(f"{dfn} {s} K", g, w)

    sim = {"UV1": small["UV1"], "UV6": small["UV6"], "jmp_shadow": small["jmp_shadow"],
           "UV3": (tot[1], tot[0]), "UV4": (tot[2], tot[0]), "UV5": (tot[3], tot[0])}
    kn = json.load(open(D / "kn.json"))["pooled"]
    for b in BUGS:
        check_eq(f"kn.json {b}", (kn[b][1], kn[b][2]), sim[b])

    print("== SimSpect fast-path CPU-s per test (1,000-test sample)")
    sim_cpu = {}
    for dfn, w in EXPECT["sim_cpu"].items():
        d = D / "timing" / "simspect" / DIR[dfn]
        ok = [r for r in rows(d / "results.jsonl.gz") if r.get("status") == "ok"]
        startup = sum(r.get("startup_cpu_s", 0) for r in rows(d / "fastpath_workers.jsonl") if r.get("event") == "spawn")
        v = sum(r["total_cpu_s"] for r in ok) / len(ok) + startup / len(ok)
        sim_cpu[dfn] = v
        check(f"{dfn} CPU-s/test (n={len(ok)})", round(v, 4), w, tol=0.0006)

    print("== AMuLeT CPU-s per test case (clean re-time)")
    amu_cpu = {}
    for dfn, w in EXPECT["amu_cpu"].items():
        s = json.load(open(D / "amulet" / "timing" / dfn / "t5_summary.json"))
        v = s["total_cpu_s_instances"] / s["total_programs"] / INPUTS_PER_PROGRAM
        amu_cpu[dfn] = v
        check(f"{dfn} ({s['instances']} instances, {s['total_programs']} programs, {s['total_cpu_s_instances']:.1f} CPU-s)",
              round(v, 5), w, tol=0.000006)

    print("== AMuLeT K / N (campaign: 32 instances x 200 programs x 140 inputs per defense)")
    pb = json.load(open(D / "amulet" / "hits" / "perbug_summary.json"))
    amuK = {}
    for b in BUGS:
        r = pb[DEFENSE[b]]
        amuK[b] = r["violations_with_jmp_shadow"] if b == "jmp_shadow" else r["per_bug"][b]["violations_with_bug"]
        check(f"AMuLeT K {b}", amuK[b], EXPECT["amu_k"][b])
    progs = {dfn: json.load(open(D / "amulet" / "hits" / dfn / "t5_summary.json"))["total_programs"] for dfn in DIR}
    for dfn, p in progs.items():
        check(f"AMuLeT N {dfn}", p * INPUTS_PER_PROGRAM, EXPECT["amu_n"])
    NA = EXPECT["amu_n"]

    print("== generation CPU-s per test")
    g = json.load(open(D / "timing" / "generation.json"))
    rt = g["retime"]
    alloy = g["stage15_alloy_job_wall_s_sum_loaded"] * rt["solver_wall_s_idle"] / rt["solver_wall_s_loaded"] / g["tests"]
    s2 = g["stage2_cpu_s"] / g["tests"]
    gen = round(alloy + s2, 2)
    print(f"  Alloy {alloy:.3f} + Stage 2 {s2:.3f}")
    check("generation CPU-s/test", gen, EXPECT["gen"])

    print("== multiples, AMuLeT / SimSpect, estimator (N+1)/(K+1) on both sides")
    print(f"  {'bug':10} {'S K/N':>15} {'S tests':>9} {'A tests':>9} {'tests x':>8} {'CPU x +gen':>11} {'CPU x exec':>11}")
    for b in BUGS:
        dfn = DEFENSE[b]
        k, n = sim[b]
        ka = amuK[b]
        st, at = (n + 1) / (k + 1), (NA + 1) / (ka + 1)
        tx = at / st
        a_s = at * amu_cpu[dfn]
        xg = a_s / (st * (sim_cpu[dfn] + gen))
        xe = a_s / (st * sim_cpu[dfn])
        print(f"  {b:10} {k:>6,}/{n:<8,} {st:9.2f} {at:9.1f} {tx:8.1f} {xg:11.3f} {xe:11.3f}")
        check(f"{b} tests multiple", tx, EXPECT["tests_x"][b], rel=0.001)
        check(f"{b} CPU multiple with generation", xg, EXPECT["cpu_x_gen"][b], rel=0.005)
        check(f"{b} CPU multiple execution only", xe, EXPECT["cpu_x_exec"][b], rel=0.005)
        check_eq(f"{b} tests multiple, label", rlab(tx) + "x", EXPECT["labels_tests"][b] + "x")
        check_eq(f"{b} CPU multiple with generation, label", rlab(xg) + "x", EXPECT["labels_gen"][b] + "x")
        check_eq(f"{b} CPU multiple execution only, label", rlab(xe) + "x", EXPECT["labels_exec"][b] + "x")
    k, n = sim["UV5"]
    tlo, thi = ratio_ci(k, n, amuK["UV5"], NA)
    f = amu_cpu["CleanupSpec"] / (sim_cpu["CleanupSpec"] + gen)
    print(f"  A-UV5 tests multiple 95%: {tlo:.3f}-{thi:.2f}x; CPU multiple with generation 95%: {tlo * f:.4f}-{thi * f:.3f}x")
    check("A-UV5 CPU multiple 95% low", tlo * f, EXPECT["uv5_time_95"][0], rel=0.01)
    check("A-UV5 CPU multiple 95% high", thi * f, EXPECT["uv5_time_95"][1], rel=0.01)

    print("== E2w (ReCon-STT on STT_6_u_A)")
    bk = json.load(open(rec / "e2w" / "recon_stt" / "buckets.json"))["buckets"]
    tests = sum(v["tests"] for kk, v in bk.items() if kk.endswith("/plain") or kk.endswith("/rmw"))
    otc = sum(c for v in bk.values() for lb, c in v["buckets"].items() if lb.startswith("oldest-taint candidate"))
    stlf = sum(c for v in bk.values() for lb, c in v["buckets"].items() if lb.startswith("STLF bypass"))
    tr = json.load(open(rec / "e2w" / "recon_stt" / "oldest_taint_rerun.json"))
    pos = sum(1 for v in tr.values() if v.get("oldest_taint_signature"))
    for lab, gv, w in zip(("E2w tests", "E2w oldest-taint candidate tests", "E2w oldest-taint signature-positive reruns",
                           "E2w STLF bypass tests"), (tests, otc, pos, stlf), EXPECT["e2w"]):
        check(lab, gv, w)

    print("\nALL MATCH" if not bad else f"\nMISMATCH: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
