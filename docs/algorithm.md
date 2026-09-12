# DataGuard Core — Algorithm

## The hierarchical reconciliation approach

Comparing two large tables row-by-row is expensive. DataGuard Core avoids this by
running checks in increasing order of cost, and only paying for an expensive check
when a cheaper one has already flagged a problem.

### Level 1 — Schema comparison
Compares `information_schema` metadata (tables, columns, types, nullability) between
source and target. Cost: near-zero, a handful of metadata queries regardless of table
size. Catches: `SCHEMA_DRIFT`, `TYPE_DRIFT`.

### Level 2 — Row count & null count
Per-table row counts, per-column null counts, duplicate primary key counts. Cost:
O(1) per table (a handful of `COUNT` queries). Catches: gross data loss, unexpected
duplication, `NULL_INJECTION` at a table-wide level.

### Level 3 — Aggregates
COUNT/SUM/AVG/MIN/MAX per numeric column, compared with **exact equality** on
financial fields (no tolerance — see rationale below). Cost: O(1) per table. Catches
`VALUE_MISMATCH` even when row counts match exactly (a single altered amount changes
the SUM without changing the count).

### Level 4 — Partition-level comparison
Buckets `transactions` by `created_at::date` and compares per-day count, sum, and
null-count. Cost: O(1) query, O(days) result rows — cheap regardless of table size.
This is the critical filtering step: it narrows "something is wrong somewhere" down
to a small set of specific dates.

**Only partitions flagged here proceed to Levels 5–6.** This is what makes the engine
faster than a naive full-table comparison at scale — most days have zero drift and are
never touched again after this step.

### Level 5 — Hash-based row fingerprinting
For each suspicious partition, canonicalizes each row
(`account_id|amount|currency|status|created_at`) and hashes it with **xxhash**
(non-cryptographic, optimized for speed — not SHA-256, which is designed for
adversarial collision-resistance that's irrelevant here). Comparing hash sets between
source and target cheaply narrows a partition of thousands of rows down to a small
candidate set of rows that actually differ.

A small superset of true mismatches is an accepted edge case (hash collisions across
different rows) — resolved precisely by Level 6.

### Level 6 — Row-level diff & fault classification
For the narrowed candidate set only, does an exact field-by-field comparison and
classifies each discrepancy into one of the catalogue's fault types:

| Fault type | Detected when |
|---|---|
| `MISSING_ROW` | Row exists in source, absent in target (or vice versa) |
| `DUPLICATE_ROW` | Extra target row matches an existing source row's account/amount/timestamp |
| `VALUE_MISMATCH` | A non-null field differs between source and target |
| `NULL_INJECTION` | A field is null on one side, non-null on the other |
| `TIMESTAMP_SHIFT` | `created_at` differs between source and target |
| `TYPE_DRIFT` / `SCHEMA_DRIFT` | Caught earlier, at Level 1 |
| `PARTITION_ANOMALY` | A day's volume deviates abnormally from history (not yet implemented — see Known Limitations) |

## Why exact equality on financial fields (no tolerance)

Floating-point or rounding-based tolerance on monetary values is a bug class, not a
feature, in a financial reconciliation context. A $0.01 drift is exactly the kind of
thing this tool exists to catch. Tolerance is never applied to `amount` or `balance`
comparisons anywhere in this pipeline.

## Known limitations

- **Duplicate detection is heuristic.** A target-only row is classified as
  `DUPLICATE_ROW` if a source row exists with the same `account_id`, `amount`, and
  `created_at`. A coincidental *genuine* duplicate transaction (same account, same
  amount, same exact timestamp, but a legitimately different transaction) would be
  misclassified as a duplicate. This is an acceptable trade-off for this dataset's
  fault-injection design, but would need a stronger signal (e.g. an idempotency key)
  in a real production system.
- **`PARTITION_ANOMALY`** (abnormal daily volume vs. history) is defined in the fault
  catalogue but not yet implemented as a distinct check — current partition-level
  logic only compares source vs. target for the same day, not a day against its own
  historical baseline.