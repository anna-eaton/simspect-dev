**INTERIM: all classified tests so far (completion order, snapshot-consistent), not the final seed-order prefix.** Report 2026-11-16T05:05:18Z; N per defense: invisispec 4000, cleanupspec 69855, speclfb 4000

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 2016/4000 | 1.98 | 3 / 3 | {'full': 2016} | 3,318.0 | 1672.7x | 9.2 | 270 | 29.3x |
| UV3 | cleanupspec | 1516/69855 | 46.05 | 35 / 2 | {'cold': 1412, 'full': 104} | 3,794.0 | 82.4x | 267.9 | 105 | 0.39x |
| UV4 | cleanupspec | 184/69855 | 377.6 | 292 / 333 | {'warm': 41, 'cold': 79, 'full': 64} | 224,000 | 593.2x | 2196.5 | 6171 | 2.81x |
| UV5 | cleanupspec | 1/69855 | 34928.0 | 68957 / 1025507 | {'cold': 1} | 224,000 | 6.4x | 203172.6 | 6171 | 0.03x |
| UV6 | speclfb | 791/4000 | 5.05 | 7 / 7 | {'full': 404, 'cold': 382, 'warm': 5} | 5,978.0 | 1183.3x | 17.6 | 115 | 6.55x |
| jmp_shadow | speclfb | 584/4000 | 6.84 | 5 / 5 | {'cold': 436, 'full': 148} | 19,040 | 2783.9x | 23.8 | 366 | 15.39x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 6.4x (UV5); CPU 0.03x (UV5).
