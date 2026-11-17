"""(e = d re-scored with W-3 loads-only footprints + RG-1 resolved-branch gate, agent fprescore 2026-11-16: InvisiSpec / SpecLFB K/N re-derived by offline trace replay of the T1g/T3g first-4,000 runs with the current checker; K/N UNCHANGED: UV1 2,002/4,000, UV6 851/4,000, jmp 527/4,000; CleanupSpec pool unchanged (its rule is unchanged, the resolved gate never applies to footprint records); AMuLeT inputs unchanged. Evidence: wiki/state/EVAL_MANIFEST.md "Re-score with W-3 + RG-1 (2026-11-16)") (d = c with AMuLeT CPU from the clean cafe3 re-time, 2026-11-16) (c = b + timing-variant rows for the split and three-bar panels) Values for the two ISCA-27 results figures, FINAL 2026-11-16 numbers (b: full CleanupSpec pool + fast-path CPU):
  tests per detection   tikz/firstdet_bars_v5_body.tex  (fig:firstdetv2)
  seconds per detection tikz/timedet_bars_v4_body.tex   (fig:timedet)
Copy of figvalues_20261116.py with only the inputs changed (main session, 2026-11-16):
  CleanupSpec = the full unified-pipeline pool, 291,860 tests = main 50,232 + extra-corpus new programs 90,932 + 3 random
    re-concretization rounds x 50,232 (BC-7 stopping rule K_UV5 >= 4), counts from each run's classes_rmw.jsonl:
    UV3 1,274 + 1,930 + 1,400 + 1,338 + 1,346 = 7,288; UV4 162 + 237 + 181 + 167 + 172 = 919; UV5 0 + 1 + 2 + 2 + 0 = 5 (all verified).
  SimSpect per-test CPU = FAST PATH (Anna 2026-11-16, TIME-4), cafe3 gem5_dev:/tests/timing_20261115/retime_fast/summary.json:
    T1g 1.344, T2g 1.738, T3g 1.2956 CPU-s per test (same 1,000-test TIME-1 sample; records identical to production).
  AMuLeT inputs unchanged.
A pure-Python copy-and-adapt of firstdet_cp_intervals.py + timedet_values.py (same Clopper-Pearson code, no scipy).
Run: python3 -I figvalues_20261116.py   (prints every value and the paste-ready \\foreach rows)

Inputs (simspect wiki/state/EVAL_MANIFEST.md, read 2026-11-16):
  SimSpect K/N, unified recipe A only ("Big corpus bug coverage (2026-11-15)"):
    InvisiSpec (A-UV1) and SpecLFB (A-UV6, jmp shadow): the first 4,000 seed-20261109 tests of Footprint_6_u_nov10_s2A
      ("MAIN NUMBER RESULTS" table): UV1 2,002/4,000, UV6 851/4,000, jmp 527/4,000.
    CleanupSpec (A-UV3, A-UV4, A-UV5): "Combined unified pool" bullet, main 50,232 + extra-corpus new programs 90,932 = 141,164 tests:
      UV3 1,274 + 1,930 = 3,204; UV4 162 + 237 = 399; UV5 0 + 1 = 1 (inst-061878, verified, reproduced 2/2).
  AMuLeT: N = 896,000 test cases per defense (T5: 6,400 programs x 140), K = UV1 270, UV3 236, UV4 4, UV5 4, UV6 150, jmp 47.
  Per-test CPU (TIME-1, dedicated node cafe2, "Dedicated CPU timing (TIME-1, 2026-11-15)"), exact values from
    cafe2 gem5_dev:/tests/timing_20261115/time1_summary.json (md5 60d0db27efa20fe1c9b0f19ac63d6814, read 2026-11-16):
    SimSpect total_mean per test (build + gem5 + checker): T1g InvisiSpec 3.693926, T2g CleanupSpec 3.736506, T3g SpecLFB 2.783872;
    AMuLeT cpu_per_test_case: InvisiSpec 0.07611062885, CleanupSpec 0.02156127701, SpecLFB 0.01472440318;
    SimSpect generation 0.93 CPU-s per test ("Generation CPU (big corpus, re-timed)"), added to every SimSpect test.
Estimator (N+1)/(K+1) on both sides (DG-2). Ratio = AMuLeT / SimSpect (> 1: SimSpect better).
Error bars: 95% Clopper-Pearson on each side's K/N, drawn as 1/rate (times the fixed time per test in the time figure).
A-UV5 ratio interval, both sides' uncertainty: conditional binomial. Given K_s + K_a detections, K_s ~ Bin(K_s + K_a, p) with
p = r_s N_s / (r_s N_s + r_a N_a); Clopper-Pearson on p, then rate ratio r_s / r_a = odds(p) x N_a / N_s (= AMuLeT tests per
detection / SimSpect tests per detection). The time ratio multiplies that by AMuLeT s per test case / SimSpect s per test.
Checked first against the 2026-11-11 caption (K_s = 4 of 50,232, K_a = 4 of 896,000: 3.3-96x).
"""
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
    hi = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p), alpha / 2)
    lo = 0.0 if k == 0 else solve(lambda p: binom_cdf(k - 1, n, p), 1 - alpha / 2)
    return lo, hi


def ratio_ci(ks, ns, ka, na):
    """95% interval for (tests per detection, AMuLeT) / (tests per detection, SimSpect), both sides' uncertainty."""
    plo, phi = cp(ks, ks + ka)
    odds = lambda p: p / (1 - p)
    return odds(plo) * na / ns, odds(phi) * na / ns


def lab(v):
    # bar label: 2 significant figures below 10, an integer below 1,000, then k (2 s.f. below 100k, whole k above)
    if v < 10: return f"{v:.1f}"
    if v < 1000: return f"{v:.0f}"
    if v < 1e5:
        s = f"{v / 1000:.2g}"
        return s + "k"
    return f"{v / 1000:.0f}k"


def rlab(r):
    # ratio label, 2 significant figures, thousands separator in TeX
    s = f"{float(f'{r:.2g}'):g}" if r >= 1 else f"{r:.2g}"
    if r >= 1000: s = f"{int(float(f'{r:.2g}')):,}".replace(",", "{,}")
    if r >= 1 and r < 10 and "." not in s: s += ".0"
    if r < 1 and len(s.replace("0.", "").lstrip("0")) == 1: s += "0"
    return s + "$\\times$"


bugs = ['UV1', 'UV3', 'UV4', 'UV5', 'UV6', 'jmp']
xlab = {'UV1': 'A-UV1', 'UV3': 'A-UV3', 'UV4': 'A-UV4', 'UV5': '{A-UV5$^{\\textstyle\\dagger}$}', 'UV6': 'A-UV6',
        'jmp': '{jmp$^{\\textstyle *}$}'}
defense = {'UV1': 'InvisiSpec', 'UV3': 'CleanupSpec', 'UV4': 'CleanupSpec', 'UV5': 'CleanupSpec', 'UV6': 'SpecLFB', 'jmp': 'SpecLFB'}
NS_CS = 50232 + 90932 + 3 * 50232
sim = {'UV1': (2002, 4000),  # W-3 + RG-1 re-score (fprescore 2026-11-16): unchanged
       'UV3': (1274 + 1930 + 1400 + 1338 + 1346, NS_CS), 'UV4': (162 + 237 + 181 + 167 + 172, NS_CS), 'UV5': (0 + 1 + 2 + 2 + 0, NS_CS),
       'UV6': (851, 4000), 'jmp': (527, 4000)}
NA = 896000
amuK = {'UV1': 270, 'UV3': 236, 'UV4': 4, 'UV5': 4, 'UV6': 150, 'jmp': 47}
GEN = 0.93
sim_cpu = {'InvisiSpec': 1.344, 'CleanupSpec': 1.738, 'SpecLFB': 1.2956}  # fast path (retime_fast/summary.json)
amu_cpu = {'InvisiSpec': 0.07304113351785714, 'CleanupSpec': 0.023373997761904765, 'SpecLFB': 0.019354087832417582}  # clean cafe3 re-time, matched ~16 busy threads (R=14/15/13), cafe3 /tests/timing_20261115/clean_summary.json
AXIS_TOP = 6.2  # log10 of the drawn axis top (the 1M gridline is 6.0); error bars above it are clipped with an arrow

assert NS_CS == 291860

# ---- check: the 2026-11-11 caption's A-UV5 ratio interval (K_s = 4 of 50,232) ----
lo, hi = ratio_ci(4, 50232, 4, NA)
print(f"check, old A-UV5 tests-ratio interval (K_s=4/50,232, K_a=4/896,000): {lo:.2f}-{hi:.1f}x  (caption 2026-11-11: 3.3-96x)")
assert abs(lo - 3.3) < 0.05 and abs(hi - 96) < 0.5

rows_t, rows_s = [], []
print("\n=== tests per detection, (N+1)/(K+1); 95% Clopper-Pearson as tests per detection ===")
print(f"{'bug':4} {'defense':11} {'S K/N':>13} {'S tests':>9} {'S 95%':>21} {'A K':>4} {'A tests':>9} {'A 95%':>21} {'ratio':>8}")
print_s = []
for b in bugs:
    D = defense[b]
    k, n = sim[b]; ka = amuK[b]
    st = (n + 1) / (k + 1); at = (NA + 1) / (ka + 1)
    slo, shi = cp(k, n); alo, ahi = cp(ka, NA)
    s_int = (1 / shi, 1 / slo); a_int = (1 / ahi, 1 / alo)
    r = at / st
    print(f"{b:4} {D:11} {k:>6,}/{n:<6,} {st:9.2f} [{s_int[0]:9.1f},{s_int[1]:10.1f}] {ka:4} {at:9.1f} [{a_int[0]:9.1f},{a_int[1]:10.1f}] {r:8.1f}")
    # seconds per detection: SimSpect (execution + generation) and AMuLeT
    ss_t = sim_cpu[D] + GEN; aa_t = amu_cpu[D]
    ssec = st * ss_t; asec = at * aa_t
    s_sint = (s_int[0] * ss_t, s_int[1] * ss_t); a_sint = (a_int[0] * aa_t, a_int[1] * aa_t)
    print_s.append((b, D, ss_t, ssec, s_sint, aa_t, asec, a_sint, asec / ssec, sim_cpu[D] * st))
    for rows, sv, av, si, ai, rr in ((rows_t, st, at, s_int, a_int, r), (rows_s, ssec, asec, s_sint, a_sint, asec / ssec)):
        shi_l = log10(si[1]); clip = 1 if shi_l > AXIS_TOP else 0
        rows.append((bugs.index(b), log10(sv), log10(av), lab(sv), lab(av), rlab(rr), xlab[b], log10(si[0]),
                     min(shi_l, AXIS_TOP), log10(ai[0]), log10(ai[1]), clip, shi_l))

print("\n=== seconds per detection, one core (SimSpect: tests x (fast-path CPU-s per test + 0.93 generation); AMuLeT: test cases x TIME-1 CPU-s per test case) ===")
print(f"{'bug':4} {'defense':11} {'S s/test':>9} {'S sec':>10} {'S 95% s':>25} {'S exec only':>11} {'A s/tc':>9} {'A sec':>8} {'A 95% s':>19} {'ratio':>7} {'exec-only ratio':>15}")
for b, D, ss_t, ssec, s_sint, aa_t, asec, a_sint, rr, sexec in print_s:
    print(f"{b:4} {D:11} {ss_t:9.4f} {ssec:10.1f} [{s_sint[0]:10.1f},{s_sint[1]:12.1f}] {sexec:11.1f} {aa_t:9.5f} {asec:8.1f} [{a_sint[0]:8.1f},{a_sint[1]:8.1f}] {rr:7.3f} {asec / sexec:15.3f}")

# ---- A-UV5 ratio intervals, both sides' uncertainty ----
k, n = sim['UV5']
tlo, thi = ratio_ci(k, n, amuK['UV5'], NA)
f = amu_cpu['CleanupSpec'] / (sim_cpu['CleanupSpec'] + GEN)
pt = ((NA + 1) / (amuK['UV5'] + 1)) / ((n + 1) / (k + 1))
print(f"\nA-UV5 (K_s={k} of {n:,}, K_a={amuK['UV5']} of {NA:,}): tests ratio {pt:.2f}x, 95% {tlo:.4f}-{thi:.2f}x;"
      f" time factor {f:.6f}; time ratio {pt * f:.4f}x, 95% {tlo * f:.6f}-{thi * f:.4f}x  (AMuLeT {1 / (pt * f):.0f}x faster at the point estimate)")

hdr = "% index / log10 SimSpect / log10 AMuLeT / SimSpect label / AMuLeT label / ratio / x label / log10 95% low and high (high clipped at the axis top), SimSpect then AMuLeT / clip flag"
for name, rows in (("tests per detection (tikz/firstdet_bars_v5_body.tex)", rows_t), ("seconds per detection (tikz/timedet_bars_v4_body.tex)", rows_s)):
    print(f"\n=== paste-ready \\foreach rows: {name} ===")
    print(hdr)
    for i, (idx, s, a, sl, al, r, la, slo, shi, alo, ahi, clip, shi_raw) in enumerate(rows):
        end = "} {" if i == len(rows) - 1 else ","
        print(f"  {idx}/{s:.4f}/{a:.4f}/{{{sl}}}/{{{al}}}/{{{r}}}/{la}/{slo:.4f}/{shi:.4f}/{alo:.4f}/{ahi:.4f}/{clip}{end}"
              + (f"  % SimSpect high {shi_raw:.4f} ({10 ** shi_raw:,.0f}) clipped at {AXIS_TOP}" if clip else ""))


# ---- (c) timing-figure variants (main session, 2026-11-16): execution-only values for the split and three-bar panels ----
print("\n=== timing variants: per bug, log10 seconds (execution only / with generation / AMuLeT), 95% CI, ratios ===")
rows_split, rows_three = [], []
for b in bugs:
    D = defense[b]; k, n = sim[b]; ka = amuK[b]
    st = (n + 1) / (k + 1); at = (NA + 1) / (ka + 1)
    slo, shi = cp(k, n); alo, ahi = cp(ka, NA)
    s_int = (1 / shi, 1 / slo); a_int = (1 / ahi, 1 / alo)
    ex = sim_cpu[D]; tot = sim_cpu[D] + GEN; am = amu_cpu[D]
    e_s, g_s, a_s = st * ex, st * tot, at * am
    e_ci = (s_int[0] * ex, s_int[1] * ex); g_ci = (s_int[0] * tot, s_int[1] * tot); a_ci = (a_int[0] * am, a_int[1] * am)
    r_e, r_g = a_s / e_s, a_s / g_s
    print(f"{b:4} exec {e_s:10.1f} [{e_ci[0]:9.1f},{e_ci[1]:10.1f}]  gen {g_s:10.1f} [{g_ci[0]:9.1f},{g_ci[1]:10.1f}]  amu {a_s:8.1f}  ratio exec {r_e:.3f} gen {r_g:.3f}")
    i = bugs.index(b)
    rows_split.append(f"  {i}/{log10(g_s):.4f}/{log10(a_s):.4f}/{log10(e_s):.4f}/{{{lab(g_s)}}}/{{{lab(a_s)}}}/{{{rlab(r_g)}}}/{xlab[b]}/{log10(g_ci[0]):.4f}/{log10(g_ci[1]):.4f}/{log10(a_ci[0]):.4f}/{log10(a_ci[1]):.4f}")
    rows_three.append(f"  {i}/{log10(e_s):.4f}/{log10(g_s):.4f}/{log10(a_s):.4f}/{{{lab(e_s)}}}/{{{lab(g_s)}}}/{{{lab(a_s)}}}/{{{rlab(r_e)}}}/{{{rlab(r_g)}}}/{xlab[b]}/{log10(e_ci[0]):.4f}/{log10(e_ci[1]):.4f}/{log10(g_ci[0]):.4f}/{log10(g_ci[1]):.4f}/{log10(a_ci[0]):.4f}/{log10(a_ci[1]):.4f}")
print("\n=== rows: split panel (tikz/timedet_split_v1_body.tex): i / log10 total / log10 AMuLeT / log10 exec / total label / AMuLeT label / ratio (with gen) / x label / total 95% lo hi / AMuLeT 95% lo hi ===")
print(",\n".join(rows_split) + "} {")
print("\n=== rows: three-bar panel (tikz/timedet_three_v1_body.tex): i / log10 exec / log10 total / log10 AMuLeT / labels exec total AMuLeT / ratio exec / ratio with gen / x label / exec 95% / total 95% / AMuLeT 95% ===")
print(",\n".join(rows_three) + "} {")
