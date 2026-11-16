**INTERIM: all classified tests so far (completion order, snapshot-consistent), not the final seed-order prefix.** Report 2026-11-10T11:13:14Z; N per defense: invisispec 5763, cleanupspec 10001, speclfb 8178

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 2978/5763 | 1.93 | 2 / 3 | {'full': 2978} | 3,318.0 | 1714.8x | 19.5 | 270 | 13.82x |
| UV3 | cleanupspec | 491/10001 | 20.33 | 51 / 4 | {'cold': 463, 'full': 28} | 3,794.0 | 186.6x | 196.4 | 105 | 0.53x |
| UV4 | cleanupspec | 135/10001 | 73.54 | 181 / 337 | {'cold': 52, 'warm': 35, 'full': 48} | 224,000 | 3045.8x | 710.7 | 6171 | 8.68x |
| UV5 | cleanupspec | 0/10001 | >10002.0 | — / — | {} | 224,000 | ≤22.4x | >96650.2 | 6171 | ≤0.06x |
| UV6 | speclfb | 2102/8178 | 3.89 | 2 / 4 | {'cold': 1080, 'full': 993, 'warm': 29} | 5,978.0 | 1537.1x | 31.5 | 115 | 3.65x |
| jmp_shadow | speclfb | 1234/8178 | 6.62 | 16 / 1 | {'cold': 976, 'full': 258} | 19,040 | 2875.0x | 53.6 | 366 | 6.82x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 22.4x (UV5, upper bound); CPU 0.06x (UV5, upper bound).
