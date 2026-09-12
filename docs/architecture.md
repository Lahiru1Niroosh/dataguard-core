# DataGuard Core - Architecture

## Domain

Simulated core banking system (source of truth) reconciled against a downstream reporting replica (simulated analytics/warehouse copy).

## Databases (3 schemas, single Postgres instance)

- `core_banking` - source (accounts, transactions, ledger_balances)
- `reporting_replica` - target (same schema, may drift)
- `dataguard_meta` - DataGuard's own run/result metadata

## Reconciliation hierarchy (cheapest -> most expensive)

1. Schema - tables/columns/types/nullability
2. Row count & nulls
3. Aggregates - COUNT/SUM/AVG/MIN/MAX
4. Partition - per-day count/sum buckets
5. Hash fingerprinting (xxhash) - narrows to candidate mismatched rows
6. Row-level diff - exact field comparison, classified by fault type

## Design property

The engine reads connection strings from config and is agnostic to whether source/target are the same Postgres instance or different ones.

## Non-goals

No Kafka, Spark, Cassandra, Kubernetes, Airflow, FastAPI, or React in this repo.
