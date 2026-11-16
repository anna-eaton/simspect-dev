#!/usr/bin/env python3
"""uv5_estimate.py: CleanupSpec UV5 rate under the final protocol.

K = UV5 detections (classify_cs_rmw / classify_hits sig "UV5") among the UV5-shaped (class D, not_taken) tests run
    under the final protocol: the main corpus's D stems in the T2g run dirs + every ext-corpus test in T2g_ext.
N = all tests generated: main corpus pairs (50,232) + ext-corpus tests generated, the ext part scaled by the share
    of its published D stems that have run (so K and N cover the same generated material).
ASSUMPTION (stated with every number): tests without the D shape cannot produce UV5 (uv5-footprint: the mechanism
needs the D shape), so all of a generated batch's UV5 detections lie in its D stems.
Reports K/N, the rate, expected tests (N+1)/(K+1), the multiple vs AMuLeT's 224,000 pooled test cases per UV5
violation, and a 95% Clopper-Pearson interval on the rate (and the matching expected-test and multiple ranges).
Any UV5 outside the D set is listed separately.

    python3 uv5_estimate.py --main-dirs d1 d2 --ext-dir d3 --d-list D_pairs_nt.tsv --main-n 50232 \
        --ext-total X --ext-published Y [--json out.json]
"""
import argparse, json, math, sys
from pathlib import Path

AMULET_UV5 = 1600 * 140


def jl(p: Path):
    out = []
    if p.exists():
        for l in p.read_text().splitlines():
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0 if k < n else 1.0
    lp, lq = math.log(p), math.log1p(-p)
    s, logc = 0.0, 0.0
    for i in range(0, k + 1):
        if i > 0:
            logc += math.log(n - i + 1) - math.log(i)
        s += math.exp(logc + i * lp + (n - i) * lq)
    return min(1.0, s)


def cp_interval(k, n, a=0.05):
    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    lo = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) >= a / 2, 0.0, 1.0)
    hi = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) <= a / 2, 0.0, 1.0)
    return lo, hi


def uv5_rows(d: Path):
    rows = {r["idx"]: r for r in jl(d / "results.jsonl")}
    cls = {c["idx"]: set(c["sigs"]) for c in jl(d / "classes_rmw.jsonl")} or \
          {c["idx"]: set(c["sigs"]) for c in jl(d / "classes.jsonl")}
    hits_pending = [i for i, r in rows.items() if r.get("hit") and i not in cls]
    return rows, cls, hits_pending


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-dirs", nargs="+", required=True)
    ap.add_argument("--ext-dir", required=True)
    ap.add_argument("--d-list", required=True)
    ap.add_argument("--main-n", type=int, default=50232)
    ap.add_argument("--ext-total", type=int, default=0, help="all tests generated in the ext corpus (shaped or not)")
    ap.add_argument("--ext-published", type=int, default=0, help="ext D tests published so far (MANIFEST)")
    ap.add_argument("--json")
    a = ap.parse_args()
    D = set()
    for l in Path(a.d_list).read_text().splitlines():
        f = l.split("\t")
        if len(f) >= 2:
            D.add((f[0], f[1].strip()))
    K, nD, pending, outside, first = 0, 0, 0, [], []
    for d in a.main_dirs:
        rows, cls, pend = uv5_rows(Path(d))
        pending += len(pend)
        for i, r in rows.items():
            k = (r["mode"], r["stem"])
            uv5 = "UV5" in cls.get(i, set())
            if k in D:
                nD += 1
                if uv5:
                    K += 1; first.append(("main", r["stem"], r.get("cache_setup"), r.get("timing_point")))
            elif uv5:
                outside.append(("main", r["mode"], r["stem"], r.get("cache_setup")))
    rows, cls, pend = uv5_rows(Path(a.ext_dir))
    pending += len(pend)
    n_ext = len(rows)
    for i, r in rows.items():
        if "UV5" in cls.get(i, set()):
            K += 1; first.append(("ext", r["stem"], r.get("cache_setup"), r.get("timing_point")))
    frac = (n_ext / a.ext_published) if a.ext_published else 0.0
    N = a.main_n + round(a.ext_total * min(1.0, frac))
    lo, hi = cp_interval(K, N)
    res = dict(K=K, N=N, main_D_tests_run=nD, main_D_total=len(D), ext_tests_run=n_ext, ext_published=a.ext_published,
               ext_total=a.ext_total, ext_share_run=round(frac, 4), hits_pending_classification=pending,
               rate=K / N if N else None, expected_tests=round((N + 1) / (K + 1), 1),
               multiple=round(AMULET_UV5 / ((N + 1) / (K + 1)), 2),
               rate_ci95=[lo, hi],
               expected_ci95=[round(1 / hi, 1) if hi else None, (round(1 / lo, 1) if lo else None)],
               multiple_ci95=[round(AMULET_UV5 * lo, 2), round(AMULET_UV5 * hi, 2)],
               uv5_hits=first, uv5_outside_D=outside,
               assumption="tests without the class-D shape cannot produce UV5 (uv5-footprint); K counts D tests only, "
                          "N counts every generated test")
    js = json.dumps(res, indent=1)
    if a.json:
        Path(a.json).write_text(js)
    print(js)


if __name__ == "__main__":
    main()
