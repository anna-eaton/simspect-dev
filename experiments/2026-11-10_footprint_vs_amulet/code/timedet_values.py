"""Values for the ISCA-27 time-to-detection figure (tikz/timedet_bars_body.tex): seconds per detection on one core, SimSpect vs AMuLeT.
Inputs, all from simspect wiki/state/EVAL_MANIFEST.md (read 2026-11-11):
  SimSpect K/N, complete run (footprint part 7 "Complete run" table, lines 389-398); estimator (N+1)/(K+1).
  SimSpect dedicated CPU-s per test, build + gem5 + checker, no generation (part 8 check 6, line 477): InvisiSpec 3.60, CleanupSpec 3.49, SpecLFB 2.62.
  AMuLeT N = 896,000 test cases per defense, K per bug (part 9 same-estimator paragraph, line 538).
  AMuLeT CPU-s per test case = pooled CPU-s / pooled test cases (part 7 table, lines 393-398); UV5 uses CleanupSpec's (UV4) rate.
Error bars: 95% Clopper-Pearson on each side's detection rate (same as firstdet_cp_intervals.py), scaled by the fixed time per test;
the uncertainty of the time per test itself is not included. Pure Python. Run: python3 -I timedet_values.py"""
import os, sys
from math import log10
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from firstdet_cp_intervals import cp  # noqa: E402  (prints its own table on import; harmless)

bugs = ['UV1', 'UV3', 'UV4', 'UV5', 'UV6', 'jmp']
sim = {'UV1': (2002, 4000), 'UV3': (1861, 50232), 'UV4': (599, 50232), 'UV5': (4, 50232), 'UV6': (861, 4000), 'jmp': (555, 4000)}
sim_s = {'UV1': 3.60, 'UV3': 3.49, 'UV4': 3.49, 'UV5': 3.49, 'UV6': 2.62, 'jmp': 2.62}
NA = 896000
amuK = {'UV1': 270, 'UV3': 236, 'UV4': 4, 'UV5': 4, 'UV6': 150, 'jmp': 47}
amu_pool = {'UV1': (270, 3318), 'UV3': (105, 3794), 'UV4': (6171, 224000), 'UV5': (6171, 224000), 'UV6': (115, 5978), 'jmp': (366, 19040)}

print("\n=== time to detection, one core (seconds) ===")
print(f"{'bug':4} {'S tests':>9} {'S s/test':>8} {'S sec':>10} {'A tests':>10} {'A s/tc':>8} {'A sec':>9} {'ratio A/S':>9}  log10 S, A; log10 95% S lo-hi, A lo-hi")
for b in bugs:
    k, n = sim[b]
    st = (n + 1) / (k + 1); ss = st * sim_s[b]
    ra = amu_pool[b][0] / amu_pool[b][1]
    at = (NA + 1) / (amuK[b] + 1); asec = at * ra
    slo, shi = cp(k, n); alo, ahi = cp(amuK[b], NA)
    sint = (sim_s[b] / shi, sim_s[b] / slo); aint = (ra / ahi, ra / alo)
    print(f"{b:4} {st:9.2f} {sim_s[b]:8.2f} {ss:10.1f} {at:10.1f} {ra:8.5f} {asec:9.1f} {asec/ss:9.3f}  "
          f"{log10(ss):.4f} {log10(asec):.4f}; S [{sint[0]:.1f},{sint[1]:.1f}] log [{log10(sint[0]):.4f},{log10(sint[1]):.4f}]"
          f" A [{aint[0]:.1f},{aint[1]:.1f}] log [{log10(aint[0]):.4f},{log10(aint[1]):.4f}]")
# A-UV5 ratio interval: the tests-ratio interval with both sides' uncertainty (3.3-96x, EVAL_MANIFEST line 474) times the fixed time factor
k, n = sim['UV5']
f = (amu_pool['UV5'][0] / amu_pool['UV5'][1]) / sim_s['UV5']
pt = ((NA + 1) / 5) / ((n + 1) / (k + 1))
print(f"\nUV5 tests ratio {pt:.2f}x; time factor {f:.5f}; time ratio {pt*f:.3f}x; 95% (3.3-96x tests) -> {3.3*f:.3f}-{96*f:.3f}x time")
