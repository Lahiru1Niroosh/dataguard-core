import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extractors.metadata import get_schema_snapshot

core = get_schema_snapshot("core_banking")
replica = get_schema_snapshot("reporting_replica")

print("=== core_banking ===")
print(json.dumps(core.model_dump(), indent=2, default=str))

print("\n=== reporting_replica ===")
print(json.dumps(replica.model_dump(), indent=2, default=str))