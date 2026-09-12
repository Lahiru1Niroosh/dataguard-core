from app.reconciliation.hashing import find_candidate_mismatches
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


def test_identical_data_has_no_hash_candidates(clean_db):
    date = _get_a_date_with_rows()
    candidates = find_candidate_mismatches("core_banking", "reporting_replica", date)
    assert candidates == set()


def test_value_mismatch_produces_a_candidate(clean_db):
    date = _get_a_date_with_rows()

    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE reporting_replica.transactions SET amount = amount + 1
        WHERE created_at::date = '{date}' LIMIT 1
    """) if False else None
    # LIMIT not supported directly on UPDATE — use subquery instead:
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
    assert len(candidates) == 1