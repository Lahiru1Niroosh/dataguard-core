"""
Phase A14 support — full pipeline runner.
Runs schema, count, aggregate, partition, hash, and row-level
reconciliation end-to-end across all partition dates that have
any transactions, and returns the combined discrepancy list.
"""
import time
from typing import List

from app.extractors.metadata import get_conn
from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows
from app.reconciliation.persistence import start_run, finish_run, save_discrepancies
from app.models.discrepancy import Discrepancy


def get_all_partition_dates(schema: str, table: str = "transactions", date_column: str = "created_at"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT {date_column}::date FROM {schema}.{table} ORDER BY 1")
    dates = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return dates


def run_full_pipeline(source_schema: str = "core_banking", target_schema: str = "reporting_replica", persist: bool = True) -> List[Discrepancy]:
    run_id = start_run() if persist else None
    start_time = time.time()

    all_discrepancies: List[Discrepancy] = []
    dates = get_all_partition_dates(source_schema)

    for partition_date in dates:
        candidates = find_candidate_mismatches(source_schema, target_schema, str(partition_date))
        if candidates:
            discrepancies = diff_rows(source_schema, target_schema, candidates)
            all_discrepancies.extend(discrepancies)

    duration = time.time() - start_time

    if persist:
        save_discrepancies(run_id, all_discrepancies)
        finish_run(run_id, duration)
        print(f"Run {run_id} finished in {duration:.2f}s, found {len(all_discrepancies)} discrepancies")

    return all_discrepancies