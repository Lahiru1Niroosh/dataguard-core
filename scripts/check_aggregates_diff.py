import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.aggregates import compare_aggregates

discrepancies = compare_aggregates("core_banking", "reporting_replica")

print(f"Found {len(discrepancies)} discrepancies.")
for d in discrepancies:
    print(d.model_dump())