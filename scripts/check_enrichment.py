import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reconciliation.enrichment import get_transaction_context
from app.models.discrepancy import Discrepancy

amount, account_id = get_transaction_context("core_banking", 10)

d = Discrepancy(
    table_name="transactions",
    row_pk=10,
    field="amount",
    fault_type="VALUE_MISMATCH",
    dollar_impact=amount,
    affected_account_id=account_id,
)

print(d.model_dump())