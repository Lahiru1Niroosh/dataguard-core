"""
Phase A10 — Business domain enrichment.
The unified discrepancy record used by Phase A11 onward. Every
discrepancy carries dollar_impact and affected_account_id so a
row mismatch reads as business impact, not just a row ID.
"""
from typing import Optional
from pydantic import BaseModel


class Discrepancy(BaseModel):
    table_name: str
    row_pk: int
    field: Optional[str] = None
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    fault_type: str  # MISSING_ROW, DUPLICATE_ROW, VALUE_MISMATCH, NULL_INJECTION,
                      # TYPE_DRIFT, SCHEMA_DRIFT, TIMESTAMP_SHIFT, PARTITION_ANOMALY
    dollar_impact: float = 0.0
    affected_account_id: Optional[int] = None