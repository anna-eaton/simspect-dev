**INTERIM: all classified tests so far (completion order, snapshot-consistent), not the final seed-order prefix.** Report 2026-11-10T14:36:33Z; N per defense: invisispec 3607, cleanupspec 42274, speclfb 4000

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 1796/3607 | 2.01 | 1 / 1 | {'full': 1796} | 3,318.0 | 1652.6x | 18.8 | 270 | 14.35x |
| UV3 | cleanupspec | 1606/42274 | 26.31 | 11 / 347 | {'cold': 1519, 'full': 87} | 3,794.0 | 144.2x | 242.0 | 105 | 0.43x |
| UV4 | cleanupspec | 488/42274 | 86.45 | 1 / 575 | {'cold': 202, 'full': 172, 'warm': 114} | 224,000 | 2591.0x | 795.3 | 6171 | 7.76x |
| UV5 | cleanupspec | 4/42274 | 8455.0 | 7430 / 188 | {'cold': 4} | 224,000 | 26.5x | 77783.3 | 6171 | 0.08x |
| UV6 | speclfb | 861/4000 | 4.64 | 1 / 1 | {'full': 429, 'cold': 420, 'warm': 12} | 5,978.0 | 1287.9x | 35.9 | 115 | 3.2x |
| jmp_shadow | speclfb | 555/4000 | 7.2 | 19 / 19 | {'cold': 439, 'full': 116} | 19,040 | 2645.9x | 55.7 | 366 | 6.57x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 26.5x (UV5); CPU 0.08x (UV5).
