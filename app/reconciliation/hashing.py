"""
Phase A9 — Hash-based row fingerprinting.
Canonicalizes each row (account_id|amount|currency|status|created_at)
and hashes with xxhash — NOT SHA-256, since this is about speed at
scale, not cryptographic collision resistance (see blueprint Section 6).
"""
from typing import Dict, Set
import xxhash

from app.extractors.metadata import get_conn


def get_row_hashes_for_date(
    cur,
    schema: str,
    table: str,
    date_column: str,
    partition_date: str,
    pk_column: str = "transaction_id",
) -> Dict[int, str]:
    cur.execute(f"""
        SELECT {pk_column}, account_id, amount, currency, status, {date_column}
        FROM {schema}.{table}
        WHERE {date_column}::date = %s
    """, (partition_date,))

    row_hashes = {}
    for row in cur.fetchall():
        pk = row[0]
        canonical = "|".join(str(v) for v in row[1:])
        row_hashes[pk] = xxhash.xxh64(canonical.encode("utf-8")).hexdigest()
    return row_hashes


def find_candidate_mismatches(
    source_schema: str,
    target_schema: str,
    partition_date: str,
    table: str = "transactions",
    date_column: str = "created_at",
    pk_column: str = "transaction_id",
) -> Set[int]:
    """
    Returns the set of primary keys whose row hash differs (or is
    missing/extra) between source and target for the given date.
    This is a cheap narrowing step — a small superset of true
    mismatches is an acceptable edge case (hash collisions), to be
    resolved precisely by Phase A11's row-level diff.
    """
    conn = get_conn()
    cur = conn.cursor()

    source_hashes = get_row_hashes_for_date(cur, source_schema, table, date_column, partition_date, pk_column)
    target_hashes = get_row_hashes_for_date(cur, target_schema, table, date_column, partition_date, pk_column)

    cur.close()
    conn.close()

    all_pks = set(source_hashes.keys()) | set(target_hashes.keys())
    candidates = {
        pk for pk in all_pks
        if source_hashes.get(pk) != target_hashes.get(pk)
    }
    return candidates