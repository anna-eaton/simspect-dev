**Rows: seed-20261109 order prefix of the full corpus (final semantics), longest fully run and classified prefix per defense.** Report 2026-11-11T03:23:57Z; N per defense: cleanupspec 50232

| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |
|---|---|---|---|---|---|---|---|---|---|---|
| UV3 | cleanupspec | 1902/50232 | 26.4 | 46 / 34 | {'cold': 1814, 'full': 88} | 3,794.0 | 143.7x | 246.0 | 105 | 0.43x |
| UV4 | cleanupspec | 597/50232 | 84.0 | 203 / 98 | {'cold': 235, 'full': 170, 'warm': 192} | 224,000 | 2666.6x | 782.7 | 6171 | 7.88x |
| UV5 | cleanupspec | 5/50232 | 8372.17 | 19927 / 11082 | {'cold': 5} | 224,000 | 26.8x | 78014.0 | 6171 | 0.08x |

Minimum over known bugs present (UV3, UV4, UV5): tests 26.8x (UV5); CPU 0.08x (UV5).
