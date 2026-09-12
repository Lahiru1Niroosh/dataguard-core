import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.persistence import (
    create_meta_tables, start_run, finish_run, save_discrepancies
)
from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows

create_meta_tables()

run_id = start_run()
print(f"Started run {run_id}")

start_time = time.time()
candidates = find_candidate_mismatches("core_banking", "reporting_replica", partition_date="2024-01-04")
discrepancies = diff_rows("core_banking", "reporting_replica", candidates)
save_discrepancies(run_id, discrepancies)
duration = time.time() - start_time

finish_run(run_id, duration)
print(f"Run {run_id} finished in {duration:.2f}s, saved {len(discrepancies)} discrepancies")