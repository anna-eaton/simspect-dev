| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 1982/4000 | 2.02 | 1 / 1 | {'full': 1982} | 3,318.0 | 1644.5x | 13.2 | 270 | 20.4x |
| UV3 | cleanupspec | 1659/52940 | 31.89 | 7 / 36 | {'cold': 1561, 'full': 98} | 3,794.0 | 119.0x | 195.3 | 105 | 0.54x |
| UV4 | cleanupspec | 383/52940 | 137.87 | 54 / 81 | {'cold': 153, 'warm': 97, 'full': 133} | 224,000 | 1624.8x | 844.4 | 6171 | 7.31x |
| UV5 | cleanupspec | 6/52940 | 7563.0 | 2339 / 10618 | {'cold': 6} | 224,000 | 29.6x | 46322.8 | 6171 | 0.13x |
| UV6 | speclfb | 883/4000 | 4.53 | 4 / 4 | {'cold': 442, 'full': 434, 'warm': 7} | 5,978.0 | 1320.8x | 25.2 | 115 | 4.56x |
| jmp_shadow | speclfb | 606/4000 | 6.59 | 5 / 5 | {'cold': 450, 'full': 156} | 19,040 | 2888.6x | 36.8 | 366 | 9.96x |

Minimum over known bugs present (UV1, UV3, UV4, UV5, UV6): tests 29.6x (UV5); CPU 0.13x (UV5).
