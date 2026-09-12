"""
Phase A11 — Row-level difference engine.
For a set of candidate primary keys (typically narrowed by Phase A9's
hashing), does exact field-by-field comparison and classifies each
discrepancy into a fault type from the blueprint's catalogue.

Duplicate detection: a target-only PK is only classified as MISSING_ROW
if its account_id/amount/created_at don't match a genuine source row
under a different PK — that pattern indicates a duplicated row (fault
type DUPLICATE_ROW), not a true gap.
"""
from typing import List, Set
from app.extractors.metadata import get_conn
from app.models.discrepancy import Discrepancy

COMPARE_COLUMNS = ["account_id", "amount", "currency", "transaction_type", "status", "created_at"]


def _fetch_row(cur, schema: str, table: str, pk_column: str, pk_value: int):
    cols = ", ".join(COMPARE_COLUMNS)
    cur.execute(f"""
        SELECT {cols} FROM {schema}.{table} WHERE {pk_column} = %s
    """, (pk_value,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip(COMPARE_COLUMNS, row))


def _is_duplicate_of_existing_source_row(cur, source_schema: str, table: str, target_row: dict) -> bool:
    cur.execute(f"""
        SELECT 1 FROM {source_schema}.{table}
        WHERE account_id = %s AND amount = %s AND created_at = %s
        LIMIT 1
    """, (target_row["account_id"], target_row["amount"], target_row["created_at"]))
    return cur.fetchone() is not None


def diff_rows(
    source_schema: str,
    target_schema: str,
    candidate_pks: Set[int],
    table: str = "transactions",
    pk_column: str = "transaction_id",
) -> List[Discrepancy]:
    discrepancies: List[Discrepancy] = []

    conn = get_conn()
    cur = conn.cursor()

    for pk in candidate_pks:
        source_row = _fetch_row(cur, source_schema, table, pk_column, pk)
        target_row = _fetch_row(cur, target_schema, table, pk_column, pk)

        if source_row is not None and target_row is None:
            discrepancies.append(Discrepancy(
                table_name=table,
                row_pk=pk,
                fault_type="MISSING_ROW",
                dollar_impact=float(source_row["amount"]),
                affected_account_id=source_row["account_id"],
            ))
            continue

        if source_row is None and target_row is not None:
            if _is_duplicate_of_existing_source_row(cur, source_schema, table, target_row):
                fault_type = "DUPLICATE_ROW"
            else:
                fault_type = "MISSING_ROW"
            discrepancies.append(Discrepancy(
                table_name=table,
                row_pk=pk,
                fault_type=fault_type,
                dollar_impact=float(target_row["amount"]),
                affected_account_id=target_row["account_id"],
            ))
            continue

        if source_row is None and target_row is None:
            continue

        for field in COMPARE_COLUMNS:
            s_val = source_row[field]
            t_val = target_row[field]

            if s_val == t_val:
                continue

            if s_val is None or t_val is None:
                fault_type = "NULL_INJECTION"
            elif field == "created_at":
                fault_type = "TIMESTAMP_SHIFT"
            else:
                fault_type = "VALUE_MISMATCH"

            discrepancies.append(Discrepancy(
                table_name=table,
                row_pk=pk,
                field=field,
                source_value=str(s_val),
                target_value=str(t_val),
                fault_type=fault_type,
                dollar_impact=float(source_row["amount"]),
                affected_account_id=source_row["account_id"],
            ))

    cur.close()
    conn.close()
    return discrepancies