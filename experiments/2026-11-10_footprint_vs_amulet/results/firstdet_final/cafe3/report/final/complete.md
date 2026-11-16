**Rows: seed-20261109 order prefix of the full corpus (final semantics), longest fully run and classified prefix per defense.** Report 2026-11-10T14:50:48Z; N per defense: invisispec 4000, cleanupspec 50232, speclfb 4000

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 2002/4000 | 2.0 | 1 / 1 | {'full': 2002} | 3,318.0 | 1661.1x | 18.8 | 270 | 14.33x |
| UV3 | cleanupspec | 1861/50232 | 26.98 | 11 / 347 | {'cold': 1770, 'full': 91} | 3,794.0 | 140.6x | 248.6 | 105 | 0.42x |
| UV4 | cleanupspec | 599/50232 | 83.72 | 1 / 575 | {'cold': 247, 'full': 200, 'warm': 152} | 224,000 | 2675.5x | 771.4 | 6171 | 8.0x |
| UV5 | cleanupspec | 4/50232 | 10046.6 | 7430 / 188 | {'cold': 4} | 224,000 | 22.3x | 92572.9 | 6171 | 0.07x |
| UV6 | speclfb | 861/4000 | 4.64 | 1 / 1 | {'full': 429, 'cold': 420, 'warm': 12} | 5,978.0 | 1287.9x | 35.9 | 115 | 3.2x |
| jmp_shadow | speclfb | 555/4000 | 7.2 | 19 / 19 | {'cold': 439, 'full': 116} | 19,040 | 2645.9x | 55.7 | 366 | 6.57x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 22.3x (UV5); CPU 0.07x (UV5).
