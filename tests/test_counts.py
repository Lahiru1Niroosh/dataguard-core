from app.reconciliation.counts import compare_counts
from tests.conftest import get_test_conn


def test_identical_data_has_no_count_discrepancies(clean_db):
    discrepancies = compare_counts("core_banking", "reporting_replica")
    assert discrepancies == []


def test_deleted_rows_are_detected(clean_db):
    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM reporting_replica.transactions WHERE transaction_id IN (1,2,3);")
    conn.commit()
    cur.close()
    conn.close()

    discrepancies = compare_counts("core_banking", "reporting_replica")
    row_count_diffs = [d for d in discrepancies if d.issue_type == "ROW_COUNT_MISMATCH"]

    assert len(row_count_diffs) == 1
    assert row_count_diffs[0].table_name == "transactions"