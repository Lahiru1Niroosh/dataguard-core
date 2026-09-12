"""
Phase A5 — Schema-level reconciliation.
Diffs two SchemaSnapshot objects: missing tables, missing columns,
type mismatches, nullability mismatches.
"""
from typing import List
from pydantic import BaseModel

from app.models.schema_models import SchemaSnapshot, TableInfo


class SchemaDiscrepancy(BaseModel):
    table_name: str
    column_name: str | None = None
    issue_type: str          # MISSING_TABLE, MISSING_COLUMN, TYPE_MISMATCH, NULLABILITY_MISMATCH
    source_value: str | None = None
    target_value: str | None = None


def _tables_by_name(snapshot: SchemaSnapshot) -> dict[str, TableInfo]:
    return {t.table_name: t for t in snapshot.tables}


def compare_schemas(source: SchemaSnapshot, target: SchemaSnapshot) -> List[SchemaDiscrepancy]:
    discrepancies: List[SchemaDiscrepancy] = []

    source_tables = _tables_by_name(source)
    target_tables = _tables_by_name(target)

    # Tables missing entirely on either side
    for table_name in source_tables.keys() - target_tables.keys():
        discrepancies.append(SchemaDiscrepancy(
            table_name=table_name,
            issue_type="MISSING_TABLE",
            source_value="present",
            target_value="absent",
        ))
    for table_name in target_tables.keys() - source_tables.keys():
        discrepancies.append(SchemaDiscrepancy(
            table_name=table_name,
            issue_type="MISSING_TABLE",
            source_value="absent",
            target_value="present",
        ))

    # Column-level comparison for tables present on both sides
    common_tables = source_tables.keys() & target_tables.keys()
    for table_name in common_tables:
        source_cols = {c.column_name: c for c in source_tables[table_name].columns}
        target_cols = {c.column_name: c for c in target_tables[table_name].columns}

        for col_name in source_cols.keys() - target_cols.keys():
            discrepancies.append(SchemaDiscrepancy(
                table_name=table_name,
                column_name=col_name,
                issue_type="MISSING_COLUMN",
                source_value="present",
                target_value="absent",
            ))
        for col_name in target_cols.keys() - source_cols.keys():
            discrepancies.append(SchemaDiscrepancy(
                table_name=table_name,
                column_name=col_name,
                issue_type="MISSING_COLUMN",
                source_value="absent",
                target_value="present",
            ))

        for col_name in source_cols.keys() & target_cols.keys():
            s_col = source_cols[col_name]
            t_col = target_cols[col_name]

            if s_col.data_type != t_col.data_type:
                discrepancies.append(SchemaDiscrepancy(
                    table_name=table_name,
                    column_name=col_name,
                    issue_type="TYPE_MISMATCH",
                    source_value=s_col.data_type,
                    target_value=t_col.data_type,
                ))

            if s_col.is_nullable != t_col.is_nullable:
                discrepancies.append(SchemaDiscrepancy(
                    table_name=table_name,
                    column_name=col_name,
                    issue_type="NULLABILITY_MISMATCH",
                    source_value=str(s_col.is_nullable),
                    target_value=str(t_col.is_nullable),
                ))

    return discrepancies