import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extractors.metadata import get_schema_snapshot
from app.reconciliation.schema import compare_schemas

core = get_schema_snapshot("core_banking")
replica = get_schema_snapshot("reporting_replica")

discrepancies = compare_schemas(core, replica)

print(f"Found {len(discrepancies)} discrepancies.")
for d in discrepancies:
    print(d.model_dump())