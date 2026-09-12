# DataGuard Core — Benchmarks

All numbers below are real measurements from an actual run on this machine.

## 100,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 0.32 | 0.137 |
| Rows/sec | 312889.8 | 727504.6 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 2.33x**

## 1,000,000 transactions

| Metric | Naive (SQL EXCEPT) | Hierarchical |
|---|---|---|
| Duration (s) | 8.409 | 1.307 |
| Rows/sec | 118916.2 | 765218.3 |
| DB queries | 2 | (multi-stage, see pipeline) |
| Discrepancies found | 0 | 0 |

**Speedup: 6.43x**

