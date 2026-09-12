"""
Phase A8 — Partition-level reconciliation.
Buckets transactions by created_at::date and compares per-day
counts and sums between source and target.
"""
from typing import List
from pydantic import BaseModel

from app.extractors.metadata import get_conn


class PartitionDiscrepancy(BaseModel):
    table_name: str
    partition_date: str
    issue_type: str          # PARTITION_COUNT_MISMATCH, PARTITION_SUM_MISMATCH
    source_value: str | None = None
    target_value: str | None = None


def get_daily_buckets(cur, schema, table, date_column, amount_column):
    cur.execute(f"""
        SELECT {date_column}::date AS day, COUNT(*), SUM({amount_column})
        FROM {schema}.{table}
        GROUP BY {date_column}::date
        ORDER BY day
    """)
    return {row[0]: (row[1], row[2]) for row in cur.fetchall()}


def compare_partitions(
    source_schema: str,
    target_schema: str,
    table: str = "transactions",
    date_column: str = "created_at",
    amount_column: str = "amount",
) -> List[PartitionDiscrepancy]:
    discrepancies: List[PartitionDiscrepancy] = []

    conn = get_conn()
    cur = conn.cursor()

    source_buckets = get_daily_buckets(cur, source_schema, table, date_column, amount_column)
    target_buckets = get_daily_buckets(cur, target_schema, table, date_column, amount_column)

    all_days = set(source_buckets.keys()) | set(target_buckets.keys())

    for day in sorted(all_days):
        s_count, s_sum = source_buckets.get(day, (0, 0))
        t_count, t_sum = target_buckets.get(day, (0, 0))

        if s_count != t_count:
            discrepancies.append(PartitionDiscrepancy(
                table_name=table,
                partition_date=str(day),
                issue_type="PARTITION_COUNT_MISMATCH",
                source_value=str(s_count),
                target_value=str(t_count),
            ))

        if s_sum != t_sum:
            discrepancies.append(PartitionDiscrepancy(
                table_name=table,
                partition_date=str(day),
                issue_type="PARTITION_SUM_MISMATCH",
                source_value=str(s_sum),
                target_value=str(t_sum),
            ))

    cur.close()
    conn.close()
    return discrepancies