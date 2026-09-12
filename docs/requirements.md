# DataGuard Core — Requirements

## Functional requirements

1. Detect drift between a source database (`core_banking`) and a downstream replica
   (`reporting_replica`) across schema, row-count, aggregate, partition, and row levels.
2. Classify every detected discrepancy into one of 8 fault types (see
   `docs/algorithm.md`).
3. Attach business context (dollar impact, affected account) to every discrepancy.
4. Provide a labeled fault-injection framework to validate detection accuracy against
   ground truth.
5. Persist every reconciliation run's results for historical trend analysis by a
   downstream BI layer (DataGuard Insights).
6. Provide a single CLI command that reproduces the full demo end-to-end.

## Non-functional requirements

- The engine must be measurably faster than a naive full-table comparison at scale
  (validated in `docs/benchmarks.md`).
- Financial amount comparisons use exact equality — no silent tolerance.
- The engine is agnostic to whether source and target live in the same Postgres
  instance or different ones (connection strings are configuration, not hardcoded).
- Test coverage exists for every reconciliation module, plus one full integration test.

## Explicit non-goals

No Kafka, Spark, Cassandra, Kubernetes, Airflow, FastAPI, or React in this repo. These
add infrastructure surface area without adding to what this project needs to prove:
reconciliation depth and (in the companion Insights project) business-facing analytics.