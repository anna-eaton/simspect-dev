**INTERIM: all classified tests so far (completion order, snapshot-consistent), not the final seed-order prefix.** Report 2026-11-10T11:24:09Z; N per defense: invisispec 7028, cleanupspec 21769, speclfb 9950

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 3598/7028 | 1.95 | 1 / 3 | {'full': 3598} | 3,318.0 | 1698.9x | 19.7 | 270 | 13.71x |
| UV3 | cleanupspec | 900/21769 | 24.16 | 11 / 4 | {'cold': 849, 'full': 51} | 3,794.0 | 157.0x | 231.4 | 105 | 0.45x |
| UV4 | cleanupspec | 266/21769 | 81.54 | 1 / 337 | {'cold': 103, 'warm': 66, 'full': 97} | 224,000 | 2747.3x | 780.9 | 6171 | 7.9x |
| UV5 | cleanupspec | 1/21769 | 10885.0 | 7430 / 10002723 | {'cold': 1} | 224,000 | 20.6x | 104245.3 | 6171 | 0.06x |
| UV6 | speclfb | 2436/9950 | 4.08 | 1 / 4 | {'cold': 1248, 'full': 1152, 'warm': 36} | 5,978.0 | 1464.0x | 33.0 | 115 | 3.48x |
| jmp_shadow | speclfb | 1476/9950 | 6.74 | 19 / 1 | {'cold': 1170, 'full': 306} | 19,040 | 2826.1x | 54.5 | 366 | 6.72x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 20.6x (UV5); CPU 0.06x (UV5).
