**Rows: seed-20261109 order prefix of the full corpus (final semantics), longest fully run and classified prefix per defense.** Report 2026-11-10T11:23:46Z; N per defense: invisispec 1352, cleanupspec 13456, speclfb 2017

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 664/1352 | 2.03 | 1 / 38 | {'full': 664} | 3,318.0 | 1630.8x | 20.4 | 270 | 13.25x |
| UV3 | cleanupspec | 514/13456 | 26.13 | 11 / 41 | {'cold': 485, 'full': 29} | 3,794.0 | 145.2x | 248.9 | 105 | 0.42x |
| UV4 | cleanupspec | 153/13456 | 87.38 | 1 / 647 | {'warm': 34, 'full': 60, 'cold': 59} | 224,000 | 2563.4x | 832.5 | 6171 | 7.41x |
| UV5 | cleanupspec | 1/13456 | 6728.5 | 7430 / 10002723 | {'cold': 1} | 224,000 | 33.3x | 64098.9 | 6171 | 0.1x |
| UV6 | speclfb | 413/2017 | 4.87 | 1 / 48 | {'full': 206, 'cold': 200, 'warm': 7} | 5,978.0 | 1226.4x | 39.1 | 115 | 2.94x |
| jmp_shadow | speclfb | 272/2017 | 7.39 | 19 / 1053 | {'cold': 221, 'full': 51} | 19,040 | 2575.8x | 59.4 | 366 | 6.17x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 33.3x (UV5); CPU 0.1x (UV5).
