import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.hashing import find_candidate_mismatches
from app.reconciliation.rows import diff_rows

candidates = find_candidate_mismatches(
    "core_banking", "reporting_replica", partition_date="2024-01-04"
)
print(f"Candidates from hashing: {len(candidates)}")

discrepancies = diff_rows("core_banking", "reporting_replica", candidates)
print(f"Discrepancies found: {len(discrepancies)}")
for d in discrepancies:
    print(d.model_dump())