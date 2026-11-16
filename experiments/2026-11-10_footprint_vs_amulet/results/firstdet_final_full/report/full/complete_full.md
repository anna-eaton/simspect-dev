| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV1 | invisispec | 25074/50232 | 2.0 | 1 / 1 | {'full': 25074} | 3,318.0 | 1656.3x | 14.2 | 270 | 19.01x |
| UV6 | speclfb | 10840/50232 | 4.63 | 1 / 1 | {'full': 5295, 'cold': 5403, 'warm': 142} | 5,978.0 | 1290.1x | 27.6 | 115 | 4.16x |
| jmp_shadow | speclfb | 7602/50232 | 6.61 | 19 / 19 | {'cold': 6107, 'full': 1493, 'warm': 2} | 19,040 | 2881.8x | 39.4 | 366 | 9.29x |

Minimum over known bugs present (UV1, UV6): tests 1290.1x (UV6); CPU 4.16x (UV6).
