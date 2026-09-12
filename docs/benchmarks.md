# DataGuard Core — Benchmarks

All numbers below are real measurements from an actual run on this machine.

## 100,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 0.351 | 0.14 |
| Rows/sec | 285155.7 | 715421.9 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 2.51x**

## 1,000,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 8.653 | 1.428 |
| Rows/sec | 115573.4 | 700045.9 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 6.06x**

