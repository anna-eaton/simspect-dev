**Rows: seed-20261109 order prefix of the full corpus (final semantics), longest fully run and classified prefix per defense.** Report 2026-11-10T14:36:25Z; N per defense: invisispec 3605, cleanupspec 37415, speclfb 4000

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 1796/3605 | 2.01 | 1 / 1 | {'full': 1796} | 3,318.0 | 1653.5x | 18.8 | 270 | 14.36x |
| UV3 | cleanupspec | 1400/37415 | 26.71 | 11 / 347 | {'cold': 1327, 'full': 73} | 3,794.0 | 142.1x | 245.7 | 105 | 0.43x |
| UV4 | cleanupspec | 447/37415 | 83.52 | 1 / 575 | {'cold': 190, 'full': 154, 'warm': 103} | 224,000 | 2682.1x | 768.5 | 6171 | 8.03x |
| UV5 | cleanupspec | 3/37415 | 9354.0 | 7430 / 188 | {'cold': 3} | 224,000 | 23.9x | 86067.6 | 6171 | 0.07x |
| UV6 | speclfb | 861/4000 | 4.64 | 1 / 1 | {'full': 429, 'cold': 420, 'warm': 12} | 5,978.0 | 1287.9x | 35.9 | 115 | 3.2x |
| jmp_shadow | speclfb | 555/4000 | 7.2 | 19 / 19 | {'cold': 439, 'full': 116} | 19,040 | 2645.9x | 55.7 | 366 | 6.57x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 23.9x (UV5); CPU 0.07x (UV5).
