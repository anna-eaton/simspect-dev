## SimSpect CPU per test (16 workers, cafe2 CPUs 0-31)

| corpus | row | N | status | total CPU-s/test mean (median) | gem5 CPU-s/test | non-gem5 | wall s/test | by setup (n, mean) |
|---|---|---|---|---|---|---|---|---|
| big corpus s2A sample | T1g (InvisiSpec) | 1000 | {'ok': 1000} | 3.69 (2.53) | 0.71 | 2.98 | 3.69 | {'full': (488, 5.339), 'warm': (512, 2.126)} |
| big corpus s2A sample | T2g (CleanupSpec) | 1000 | {'ok': 1000} | 3.74 (3.98) | 1.25 | 2.48 | 3.73 | {'cold': (314, 4.057), 'full': (354, 4.281), 'warm': (332, 2.853)} |
| big corpus s2A sample | T3g (SpecLFB) | 1000 | {'ok': 1000} | 2.78 (3.01) | 0.72 | 2.06 | 2.78 | {'cold': (314, 3.034), 'full': (354, 3.568), 'warm': (332, 1.711)} |

## AMuLeT CPU per program (instances pinned to CPUs 0-31)

| defense | instances | programs | violations | CPU-s per program | CPU-s per test case (/140) | T5 CPU-s per program (32 inst.) | ratio TIME-1 / T5 | RUSAGE_CHILDREN CPU-s vs summed instances |
|---|---|---|---|---|---|---|---|---|
| InvisiSpec | 14 | 2800 | 137 | 10.655 | 0.0761 | 11.4 | 0.93 | 29835.366523 vs 29835 |
| CleanupSpec | 14 | 2800 | 96 | 3.019 | 0.0216 | 3.86 | 0.78 | 8452.0206 vs 8452 |
| SpecLFB | 14 | 2800 | 116 | 2.061 | 0.0147 | 2.69 | 0.77 | 5771.966060000001 vs 5772 |

## CPU-per-detection multiples (AMuLeT CPU per detection / SimSpect CPU per detection; >1 = SimSpect cheaper)

Estimator (N+1)/(K+1) on both sides; AMuLeT N = 896,000 test cases per defense; generation = 0.93 CPU-s per test.

| K/N set | SimSpect CPU basis | bug | SimSpect K/N | exp. tests | AMuLeT K | AMuLeT exp. test cases | multiple (tests) | SimSpect CPU-s/det (exec) | AMuLeT CPU-s/det | multiple exec only | multiple incl. generation |
|---|---|---|---|---|---|---|---|---|---|---|
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | UV1 | 2002/4000 | 2.00 | 270 | 3306 | 1655.2x | 7.4 | 251.6 | 34.1x | 27.2x |
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | UV3 | 1274/50232 | 39.40 | 236 | 3781 | 96.0x | 147.2 | 81.5 | 0.554x | 0.443x |
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | UV4 | 162/50232 | 308.18 | 4 | 179200 | 581.5x | 1151.5 | 3863.8 | 3.36x | 2.69x |
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | UV5 | 0/50232 | 50233.00 | 4 | 179200 | 3.6x | 187695.9 | 3863.8 | 0.0206x | 0.0165x |
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | UV6 | 851/4000 | 4.70 | 150 | 5934 | 1263.6x | 13.1 | 87.4 | 6.68x | 5.01x |
| big corpus Footprint A (2026-11-15 rerun) | simspect_bc | jmp_shadow | 527/4000 | 7.58 | 47 | 18667 | 2463.4x | 21.1 | 274.9 | 13x | 9.77x |
