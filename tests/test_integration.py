from app.faults.injector import run_injection
from app.reconciliation.pipeline import run_full_pipeline


def test_full_pipeline_detects_injected_faults(clean_db):
    manifest = run_injection("reporting_replica", {
        "value-mismatch": 5,
        "null-injection": 5,
    })
    injected_ids = {f["transaction_id"] for f in manifest}

    discrepancies = run_full_pipeline(persist=False)
    detected_ids = {d.row_pk for d in discrepancies}

    assert injected_ids.issubset(detected_ids)