**INTERIM: all classified tests so far (completion order, snapshot-consistent), not the final seed-order prefix.** Report 2026-11-16T00:30:54Z; N per defense: invisispec 4000, cleanupspec 50232, speclfb 4000

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 2002/4000 | 2.0 | 1 / 1 | {'full': 2002} | 3,318.0 | 1661.1x | 13.5 | 270 | 20.07x |
| UV3 | cleanupspec | 1274/50232 | 39.4 | 6 / 79 | {'cold': 1178, 'full': 96} | 3,794.0 | 96.3x | 227.0 | 105 | 0.46x |
| UV4 | cleanupspec | 162/50232 | 308.18 | 295 / 121 | {'warm': 44, 'full': 50, 'cold': 68} | 224,000 | 726.9x | 1775.4 | 6171 | 3.48x |
| UV5 | cleanupspec | 0/50232 | >50233.0 | — / — | {} | 224,000 | ≤4.5x | >289386.2 | 6171 | ≤0.02x |
| UV6 | speclfb | 851/4000 | 4.7 | 6 / 4 | {'full': 426, 'cold': 420, 'warm': 5} | 5,978.0 | 1273.0x | 23.8 | 115 | 4.84x |
| jmp_shadow | speclfb | 527/4000 | 7.58 | 14 / 4 | {'full': 132, 'cold': 395} | 19,040 | 2512.7x | 38.4 | 366 | 9.54x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 4.5x (UV5, upper bound); CPU 0.02x (UV5, upper bound).
