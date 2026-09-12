from app.extractors.metadata import get_schema_snapshot
from app.reconciliation.schema import compare_schemas
from tests.conftest import get_test_conn


def test_identical_schemas_have_no_discrepancies(clean_db):
    source = get_schema_snapshot("core_banking")
    target = get_schema_snapshot("reporting_replica")
    discrepancies = compare_schemas(source, target)
    assert discrepancies == []


def test_type_mismatch_is_detected(clean_db):
    conn = get_test_conn()
    cur = conn.cursor()
    cur.execute("ALTER TABLE reporting_replica.transactions ALTER COLUMN currency TYPE VARCHAR(10);")
    conn.commit()
    cur.close()
    conn.close()

    source = get_schema_snapshot("core_banking")
    target = get_schema_snapshot("reporting_replica")
    discrepancies = compare_schemas(source, target)

    assert len(discrepancies) == 1
    assert discrepancies[0].issue_type == "TYPE_MISMATCH"
    assert discrepancies[0].column_name == "currency"