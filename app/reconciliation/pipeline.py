"""
Phase A14/A15 support — full pipeline runner, now genuinely
hierarchical: cheap partition-level checks first, expensive
hashing/row-diff only on partitions actually flagged as suspicious.
"""
import time
from typing import List

from app.extractors.metadata import get_conn
from app.reconciliation.partitions import compare_partitions
from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows
from app.reconciliation.persistence import start_run, finish_run, save_discrepancies
from app.models.discrepancy import Discrepancy


def run_full_pipeline(source_schema: str = "core_banking", target_schema: str = "reporting_replica", persist: bool = True) -> List[Discrepancy]:
    run_id = start_run() if persist else None
    start_time = time.time()

    all_discrepancies: List[Discrepancy] = []

    # Cheap step: find only the partition-dates with a count or sum
    # mismatch. Clean dates are never touched again after this.
    partition_diffs = compare_partitions(source_schema, target_schema)
    suspicious_dates = {d.partition_date for d in partition_diffs}

    # Expensive step: hash + row-diff, but ONLY on flagged dates.
    for partition_date in suspicious_dates:
        candidates = find_candidate_mismatches(source_schema, target_schema, partition_date)
        if candidates:
            discrepancies = diff_rows(source_schema, target_schema, candidates)
            all_discrepancies.extend(discrepancies)

    duration = time.time() - start_time

    if persist:
        save_discrepancies(run_id, all_discrepancies)
        finish_run(run_id, duration)
        print(f"Run {run_id} finished in {duration:.2f}s, found {len(all_discrepancies)} discrepancies")

    return all_discrepancies