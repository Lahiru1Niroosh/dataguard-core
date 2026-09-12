"""
Phase A10 — enrichment helper.
Given a transaction_id, looks up its amount and account_id so
discrepancy records can carry real dollar/account context.
"""
from app.extractors.metadata import get_conn


def get_transaction_context(schema: str, transaction_id: int):
    """
    Returns (amount, account_id) for a transaction, checked against
    the given schema. Returns (0.0, None) if the row doesn't exist
    there (e.g. for MISSING_ROW faults).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT amount, account_id FROM {schema}.transactions
        WHERE transaction_id = %s
    """, (transaction_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return 0.0, None
    return float(row[0]), row[1]