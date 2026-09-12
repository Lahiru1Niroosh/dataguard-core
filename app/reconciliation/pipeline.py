"""
Phase A14/A15/B2-support — full pipeline runner. Genuinely
hierarchical: cheap partition-level checks first, expensive
hashing/row-diff only on partitions actually flagged as suspicious.
Also records total_rows_checked so downstream BI can compute a
real integrity % (discrepancies / total rows), not a guessed one.
"""
import time
from typing import List

from app.extractors.metadata import get_conn
from app.reconciliation.partitions import compare_partitions
from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows
from app.reconciliation.persistence import start_run, finish_run, save_discrepancies
from app.models.discrepancy import Discrepancy


def get_total_row_count(schema: str, table: str = "transactions") -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def run_full_pipeline(source_schema: str = "core_banking", target_schema: str = "reporting_replica", persist: bool = True) -> List[Discrepancy]:
    run_id = start_run() if persist else None
    start_time = time.time()

    total_rows = get_total_row_count(source_schema)

    all_discrepancies: List[Discrepancy] = []
    partition_diffs = compare_partitions(source_schema, target_schema)
    suspicious_dates = {d.partition_date for d in partition_diffs}

    for partition_date in suspicious_dates:
        candidates = find_candidate_mismatches(source_schema, target_schema, partition_date)
        if candidates:
            discrepancies = diff_rows(source_schema, target_schema, candidates)
            all_discrepancies.extend(discrepancies)

    duration = time.time() - start_time

    if persist:
        save_discrepancies(run_id, all_discrepancies)
        finish_run(run_id, duration, total_rows_checked=total_rows)
        print(f"Run {run_id} finished in {duration:.2f}s, found {len(all_discrepancies)} discrepancies out of {total_rows} rows checked")

    return all_discrepancies