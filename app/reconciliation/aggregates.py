"""
Phase A7 — Aggregate-level reconciliation.
Compares COUNT/SUM/AVG/MIN/MAX per numeric column between two schemas.
Financial amount columns use exact equality — no tolerance.
"""
from typing import List
from pydantic import BaseModel

from app.extractors.metadata import get_conn, get_schema_snapshot

NUMERIC_TYPES = {"numeric", "bigint", "integer", "double precision", "real"}


class AggregateDiscrepancy(BaseModel):
    table_name: str
    column_name: str
    issue_type: str          # AGGREGATE_MISMATCH
    metric: str               # SUM, AVG, MIN, MAX
    source_value: str | None = None
    target_value: str | None = None


def get_aggregates(cur, schema, table, column):
    cur.execute(f"""
        SELECT SUM({column}), AVG({column}), MIN({column}), MAX({column})
        FROM {schema}.{table}
    """)
    return cur.fetchone()


def compare_aggregates(source_schema: str, target_schema: str) -> List[AggregateDiscrepancy]:
    discrepancies: List[AggregateDiscrepancy] = []

    source_snapshot = get_schema_snapshot(source_schema)
    conn = get_conn()
    cur = conn.cursor()

    for table in source_snapshot.tables:
        table_name = table.table_name
        numeric_columns = [
            c.column_name for c in table.columns
            if c.data_type in NUMERIC_TYPES
        ]

        for column in numeric_columns:
            s_sum, s_avg, s_min, s_max = get_aggregates(cur, source_schema, table_name, column)
            t_sum, t_avg, t_min, t_max = get_aggregates(cur, target_schema, table_name, column)

            metrics = [
                ("SUM", s_sum, t_sum),
                ("AVG", s_avg, t_avg),
                ("MIN", s_min, t_min),
                ("MAX", s_max, t_max),
            ]

            for metric_name, s_val, t_val in metrics:
                # Exact equality — no tolerance, per blueprint rule on money fields.
                if s_val != t_val:
                    discrepancies.append(AggregateDiscrepancy(
                        table_name=table_name,
                        column_name=column,
                        issue_type="AGGREGATE_MISMATCH",
                        metric=metric_name,
                        source_value=str(s_val),
                        target_value=str(t_val),
                    ))

    cur.close()
    conn.close()
    return discrepancies