## SimSpect CPU per test (16 workers, cafe2 CPUs 0-31)

| corpus | row | N | status | total CPU-s/test mean (median) | gem5 CPU-s/test | non-gem5 | wall s/test | by setup (n, mean) |
|---|---|---|---|---|---|---|---|---|
| big corpus s2A sample | T1g (InvisiSpec) | 1000 | {'ok': 1000} | 1.34 (0.81) | 0.71 | 0.64 | 1.34 | {'full': (488, 1.989), 'warm': (512, 0.728)} |
| big corpus s2A sample | T2g (CleanupSpec) | 1000 | {'ok': 1000} | 1.74 (1.86) | 1.21 | 0.53 | 1.73 | {'cold': (314, 1.863), 'full': (354, 2.004), 'warm': (332, 1.334)} |
| big corpus s2A sample | T3g (SpecLFB) | 1000 | {'ok': 1000} | 1.29 (1.26) | 0.71 | 0.59 | 1.29 | {'cold': (314, 1.263), 'full': (354, 1.838), 'warm': (332, 0.745)} |

## AMuLeT CPU per program (instances pinned to CPUs 0-31)

| defense | instances | programs | violations | CPU-s per program | CPU-s per test case (/140) | T5 CPU-s per program (32 inst.) | ratio TIME-1 / T5 | RUSAGE_CHILDREN CPU-s vs summed instances |
|---|---|---|---|---|---|---|---|---|
| InvisiSpec | 14 | 2800 | 100 | 10.226 | 0.0730 | 11.4 | 0.90 | 28632.124350000002 vs 28632 |
| CleanupSpec | 15 | 3000 | 89 | 3.272 | 0.0234 | 3.86 | 0.85 | 9817.079074 vs 9817 |
| SpecLFB | 13 | 2600 | 70 | 2.710 | 0.0194 | 2.69 | 1.01 | 7044.887984 vs 7045 |

## CPU-per-detection multiples (AMuLeT CPU per detection / SimSpect CPU per detection; >1 = SimSpect cheaper)

Estimator (N+1)/(K+1) on both sides; AMuLeT N = 896,000 test cases per defense; generation = 0.93 CPU-s per test.

| K/N set | SimSpect CPU basis | bug | SimSpect K/N | exp. tests | AMuLeT K | AMuLeT exp. test cases | multiple (tests) | SimSpect CPU-s/det (exec) | AMuLeT CPU-s/det | multiple exec only | multiple incl. generation |
|---|---|---|---|---|---|---|---|---|---|---|
| final unified-pipeline K/N (2026-11-16) | simspect_bc | UV1 | 2002/4000 | 2.00 | 270 | 3306 | 1655.2x | 2.7 | 241.5 | 90x | 53.2x |
| final unified-pipeline K/N (2026-11-16) | simspect_bc | UV3 | 7288/291860 | 40.04 | 236 | 3781 | 94.4x | 69.6 | 88.4 | 1.27x | 0.827x |
| final unified-pipeline K/N (2026-11-16) | simspect_bc | UV4 | 919/291860 | 317.24 | 4 | 179200 | 564.9x | 551.1 | 4188.6 | 7.6x | 4.95x |
| final unified-pipeline K/N (2026-11-16) | simspect_bc | UV5 | 5/291860 | 48643.50 | 4 | 179200 | 3.7x | 84501.4 | 4188.6 | 0.0496x | 0.0323x |
| final unified-pipeline K/N (2026-11-16) | simspect_bc | UV6 | 851/4000 | 4.70 | 150 | 5934 | 1263.6x | 6.1 | 114.8 | 18.9x | 11x |
| final unified-pipeline K/N (2026-11-16) | simspect_bc | jmp_shadow | 527/4000 | 7.58 | 47 | 18667 | 2463.4x | 9.8 | 361.3 | 36.8x | 21.4x |
