| row | TIME-1 CPU-s/test | production rerun | fast path | speedup | rows fast = rerun | raw hit records fast = rerun | fast exec_path |
|---|---|---|---|---|---|---|---|
| T1g | 3.6939 | 3.6729 | 1.344 | 2.733x | 1000/1000 (rerun vs TIME-1 differ on 0) | 1000/1000 | {'fast': 1000} |
| T2g | 3.7365 | 3.6734 | 1.738 | 2.114x | 1000/1000 (rerun vs TIME-1 differ on 0) | 56/56 | {'fast': 1000} |
| T3g | 2.7839 | 2.7251 | 1.2956 | 2.103x | 1000/1000 (rerun vs TIME-1 differ on 0) | 470/470 | {'fast': 1000} |

CPU-s per test = mean total_cpu_s (whole per-test tree); fast path includes its workers' one-time startup spread over the tests. Per cache setup and gem5-only numbers in summary.json.
