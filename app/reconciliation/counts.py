"""
Phase A6 — Row count and null reconciliation.
Compares row counts per table, null counts per column, and
duplicate primary key counts between two schemas.
"""
from typing import List
from pydantic import BaseModel

from app.extractors.metadata import get_conn, get_schema_snapshot


class CountDiscrepancy(BaseModel):
    table_name: str
    column_name: str | None = None
    issue_type: str          # ROW_COUNT_MISMATCH, NULL_COUNT_MISMATCH, DUPLICATE_PK
    source_value: str | None = None
    target_value: str | None = None


def get_row_count(cur, schema, table):
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
    return cur.fetchone()[0]


def get_null_count(cur, schema, table, column):
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {column} IS NULL")
    return cur.fetchone()[0]


def get_duplicate_pk_count(cur, schema, table, pk_column):
    cur.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT {pk_column} FROM {schema}.{table}
            GROUP BY {pk_column} HAVING COUNT(*) > 1
        ) dupes
    """)
    return cur.fetchone()[0]


def compare_counts(source_schema: str, target_schema: str) -> List[CountDiscrepancy]:
    discrepancies: List[CountDiscrepancy] = []

    source_snapshot = get_schema_snapshot(source_schema)
    conn = get_conn()
    cur = conn.cursor()

    for table in source_snapshot.tables:
        table_name = table.table_name

        source_count = get_row_count(cur, source_schema, table_name)
        target_count = get_row_count(cur, target_schema, table_name)
        if source_count != target_count:
            discrepancies.append(CountDiscrepancy(
                table_name=table_name,
                issue_type="ROW_COUNT_MISMATCH",
                source_value=str(source_count),
                target_value=str(target_count),
            ))

        pk_columns = [c.column_name for c in table.columns if c.is_primary_key]
        if pk_columns:
            pk_column = pk_columns[0]
            source_dupes = get_duplicate_pk_count(cur, source_schema, table_name, pk_column)
            target_dupes = get_duplicate_pk_count(cur, target_schema, table_name, pk_column)
            if source_dupes != target_dupes:
                discrepancies.append(CountDiscrepancy(
                    table_name=table_name,
                    column_name=pk_column,
                    issue_type="DUPLICATE_PK",
                    source_value=str(source_dupes),
                    target_value=str(target_dupes),
                ))

        for col in table.columns:
            source_nulls = get_null_count(cur, source_schema, table_name, col.column_name)
            target_nulls = get_null_count(cur, target_schema, table_name, col.column_name)
            if source_nulls != target_nulls:
                discrepancies.append(CountDiscrepancy(
                    table_name=table_name,
                    column_name=col.column_name,
                    issue_type="NULL_COUNT_MISMATCH",
                    source_value=str(source_nulls),
                    target_value=str(target_nulls),
                ))

    cur.close()
    conn.close()
    return discrepancies