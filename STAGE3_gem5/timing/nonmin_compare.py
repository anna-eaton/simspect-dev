#!/usr/bin/env python3
"""nonmin_compare.py -- minimal vs non-minimal footprint corpus, first detection with ONE estimator on both sides.

Read-only. Inputs: firstdet_report.py JSONs (the 'bugs' block: K, N per bug) for the minimal corpus (complete run,
Footprint_6_u_core_lpP_fv3) and the non-minimal corpus (Footprint_6_u_core_lpN_fv3).
Estimator (brief, same on both tools): expected tests to first detection = (N+1)/(K+1).
  SimSpect: N, K from the report.  AMuLeT: N = 896,000 test cases per defense (6,400 programs x 140 inputs, T5),
  K = AMuLeT's per-bug violation counts (UV1 270, UV3 236, UV4 4, UV5 4, UV6 150, jmp shadow 47).
  multiple = AMuLeT expected / SimSpect expected.
Also: per-bug rate K/N with a 95% Clopper-Pearson interval, and the multiple's interval from SimSpect's interval only
(AMuLeT fixed), and the ratio of non-minimal to minimal rates.
Usage: nonmin_compare.py --minimal complete.json --nonmin nonmin.json [--json OUT] [--md OUT]
"""
import argparse, json, math
from pathlib import Path

AMULET_N = 896000
AMULET_K = {"UV1": 270, "UV3": 236, "UV4": 4, "UV5": 4, "UV6": 150, "jmp_shadow": 47}
KNOWN = ["UV1", "UV3", "UV4", "UV5", "UV6"]


def binom_cdf(k, n, p):
    if p <= 0: return 1.0
    if p >= 1: return 0.0 if k < n else 1.0
    s = 0.0
    for i in range(0, k + 1):
        s += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * math.log(p) + (n - i) * math.log1p(-p))
    return min(1.0, s)


def cp(k, n, a=0.05):
    """Clopper-Pearson by bisection (k small enough for the direct sum; large k uses the normal approximation)."""
    if k > 2000:
        p = k / n; h = 1.96 * math.sqrt(p * (1 - p) / n); return max(0, p - h), min(1, p + h)
    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid): hi = mid
            else: lo = mid
        return (lo + hi) / 2
    lo = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) >= a / 2)
    hi = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) <= a / 2)
    return lo, hi


def row(bug, b):
    K, N = b["K"], b["N"]
    sim = (N + 1) / (K + 1); am = (AMULET_N + 1) / (AMULET_K[bug] + 1)
    lo, hi = cp(K, N)
    return {"K": K, "N": N, "rate": K / N if N else None, "rate_ci95": [lo, hi], "simspect_expected": sim,
            "amulet_expected": am, "multiple": am / sim,
            "multiple_ci95_simspect_only": [am * lo, am * hi] if K else [0, am * hi],   # multiple ~ am*rate for small rates
            "first_seed_order": b.get("first_seed_order"), "det_setups": b.get("det_setups")}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--minimal", required=True); ap.add_argument("--nonmin", required=True)
    ap.add_argument("--json"); ap.add_argument("--md"); a = ap.parse_args()
    M, X = json.loads(Path(a.minimal).read_text())["bugs"], json.loads(Path(a.nonmin).read_text())["bugs"]
    out = {"estimator": "(N+1)/(K+1) both tools; AMuLeT N=896000, K=" + json.dumps(AMULET_K), "bugs": {}}
    lines = ["| bug | minimal K/N | minimal multiple | non-minimal K/N | non-minimal rate 95% CI | non-minimal multiple (95% CI, SimSpect side) | rate ratio nonmin/min | first det. (seed order) min / nonmin |",
             "|---|---|---|---|---|---|---|---|"]
    for bug in AMULET_K:
        if bug not in M or bug not in X:
            continue
        rm, rx = row(bug, M[bug]), row(bug, X[bug])
        ratio = (rx["rate"] / rm["rate"]) if rm["rate"] else None
        out["bugs"][bug] = {"minimal": rm, "nonmin": rx, "rate_ratio": ratio}
        lines.append(f"| {bug} | {rm['K']:,}/{rm['N']:,} | {rm['multiple']:,.1f}x | {rx['K']:,}/{rx['N']:,} | "
                     f"{rx['rate_ci95'][0]:.2e}-{rx['rate_ci95'][1]:.2e} | {rx['multiple']:,.1f}x ({rx['multiple_ci95_simspect_only'][0]:,.1f}-{rx['multiple_ci95_simspect_only'][1]:,.1f}) | "
                     f"{ratio:.2f} | #{rm['first_seed_order']} / #{rx['first_seed_order']} |" if ratio is not None else f"| {bug} | ... |")
    for side in ("minimal", "nonmin"):
        ms = [(b, out["bugs"][b][side]["multiple"]) for b in KNOWN if b in out["bugs"]]
        out[f"minimum_{side}"] = min(ms, key=lambda t: t[1]) if ms else None
    lines.append("")
    lines.append(f"Minimum over the five known bugs: minimal {out['minimum_minimal'][0]} {out['minimum_minimal'][1]:,.1f}x; non-minimal {out['minimum_nonmin'][0]} {out['minimum_nonmin'][1]:,.1f}x.")
    md = "\n".join(lines)
    print(md)
    if a.json: Path(a.json).write_text(json.dumps(out, indent=1))
    if a.md: Path(a.md).write_text(md + "\n")


if __name__ == "__main__":
    main()
