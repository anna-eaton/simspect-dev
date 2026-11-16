| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 0/4249 | >4250.0 | — / — | {} | 3,318.0 | ≤0.8x | >43826.8 | 270 | ≤0.01x |
| UV3 | cleanupspec | 199/4774 | 23.88 | 42 / 4 | {'cold': 186, 'full': 13} | 3,794.0 | 158.9x | 237.3 | 105 | 0.44x |
| UV4 | cleanupspec | 50/4774 | 93.63 | 40 / 337 | {'cold': 23, 'warm': 13, 'full': 14} | 224,000 | 2392.5x | 930.7 | 6171 | 6.63x |
| UV5 | cleanupspec | 0/4774 | >4775.0 | — / — | {} | 224,000 | ≤46.9x | >47464.3 | 6171 | ≤0.13x |
| UV6 | speclfb | 1293/6109 | 4.72 | 9 / 4 | {'cold': 648, 'full': 626, 'warm': 19} | 5,978.0 | 1266.0x | 38.9 | 115 | 2.96x |
| jmp_shadow | speclfb | 674/6109 | 9.05 | 9 / 1 | {'cold': 510, 'full': 164} | 19,040 | 2103.4x | 74.5 | 366 | 4.91x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 0.8x (UV1, upper bound); CPU 0.01x (UV1, upper bound).
