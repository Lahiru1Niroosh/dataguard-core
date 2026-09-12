from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows
from app.extractors.metadata import get_conn
from tests.conftest import get_test_conn


def _get_a_date_with_rows():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT created_at::date FROM core_banking.transactions LIMIT 1;")
    date = cur.fetchone()[0]
    cur.close()
    conn.close()
    return str(date)


def test_value_mismatch_is_classified_correctly(clean_db):
    date = _get_a_date_with_rows()

    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE reporting_replica.transactions SET amount = amount + 1
        WHERE transaction_id = (
            SELECT transaction_id FROM reporting_replica.transactions
            WHERE created_at::date = '{date}' LIMIT 1
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

    candidates = find_candidate_mismatches("core_banking", "reporting_replica", date)
    discrepancies = diff_rows("core_banking", "reporting_replica", candidates)

    assert len(discrepancies) == 1
    assert discrepancies[0].fault_type == "VALUE_MISMATCH"
    assert discrepancies[0].field == "amount"


def test_null_injection_is_classified_correctly(clean_db):
    date = _get_a_date_with_rows()

    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE reporting_replica.transactions SET status = NULL
        WHERE transaction_id = (
            SELECT transaction_id FROM reporting_replica.transactions
            WHERE created_at::date = '{date}' LIMIT 1
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

    candidates = find_candidate_mismatches("core_banking", "reporting_replica", date)
    discrepancies = diff_rows("core_banking", "reporting_replica", candidates)

    assert len(discrepancies) == 1
    assert discrepancies[0].fault_type == "NULL_INJECTION"