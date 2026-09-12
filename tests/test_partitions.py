from app.reconciliation.partitions import compare_partitions
from tests.conftest import get_test_conn


def test_identical_data_has_no_partition_discrepancies(clean_db):
    discrepancies = compare_partitions("core_banking", "reporting_replica")
    assert discrepancies == []


def test_null_injection_is_flagged_at_partition_level(clean_db):
    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reporting_replica.transactions SET status = NULL WHERE transaction_id = 1;")
    conn.commit()
    cur.close()
    conn.close()

    discrepancies = compare_partitions("core_banking", "reporting_replica")
    null_diffs = [d for d in discrepancies if d.issue_type == "PARTITION_NULL_MISMATCH"]
    assert len(null_diffs) == 1