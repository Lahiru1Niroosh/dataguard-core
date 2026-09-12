# DataGuard Core — Benchmarks

All numbers below are real measurements from an actual run on this machine.

## 100,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 1.17 | 23.021 |
| Rows/sec | 85484.8 | 4343.8 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 0.05x**

## 1,000,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 8.153 | 52.789 |
| Rows/sec | 122649.1 | 18943.3 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 0.15x**

