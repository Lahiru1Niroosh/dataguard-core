import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.partitions import compare_partitions

discrepancies = compare_partitions("core_banking", "reporting_replica")

print(f"Found {len(discrepancies)} discrepancies.")
for d in discrepancies:
    print(d.model_dump())