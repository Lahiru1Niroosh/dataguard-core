import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.hashing import find_candidate_mismatches

candidates = find_candidate_mismatches(
    "core_banking", "reporting_replica", partition_date="2024-01-04"
)

print(f"Found {len(candidates)} candidate mismatches on 2024-01-04.")
print(sorted(candidates))