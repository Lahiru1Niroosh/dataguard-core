from app.reconciliation.aggregates import compare_aggregates
from tests.conftest import get_test_conn


def test_identical_data_has_no_aggregate_discrepancies(clean_db):
    discrepancies = compare_aggregates("core_banking", "reporting_replica")
    assert discrepancies == []


def test_value_mismatch_caught_even_with_same_row_count(clean_db):
    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reporting_replica.transactions SET amount = amount + 500 WHERE transaction_id = 1;")
    conn.commit()
    cur.close()
    conn.close()

    discrepancies = compare_aggregates("core_banking", "reporting_replica")
    sum_diffs = [d for d in discrepancies if d.metric == "SUM"]
    assert len(sum_diffs) == 1