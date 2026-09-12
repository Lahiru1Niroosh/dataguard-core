"""
Phase A12 — Fault injection framework.
Deliberately introduces labeled faults into reporting_replica and
writes a manifest recording exactly what was changed, so detection
accuracy can be measured against ground truth later (Phase A14).
"""
import json
import random
from datetime import datetime

from app.extractors.metadata import get_conn


def _get_random_transaction_ids(cur, schema, n):
    cur.execute(f"SELECT transaction_id FROM {schema}.transactions ORDER BY random() LIMIT {n}")
    return [row[0] for row in cur.fetchall()]


def inject_missing_rows(cur, schema, n, manifest):
    ids = _get_random_transaction_ids(cur, schema, n)
    for tid in ids:
        cur.execute(f"DELETE FROM {schema}.transactions WHERE transaction_id = %s", (tid,))
        manifest.append({"fault_type": "MISSING_ROW", "transaction_id": tid})


def inject_duplicate_rows(cur, schema, n, manifest):
    ids = _get_random_transaction_ids(cur, schema, n)
    for tid in ids:
        cur.execute(f"""
            INSERT INTO {schema}.transactions
            (transaction_id, account_id, amount, currency, transaction_type, status, created_at)
            SELECT transaction_id + 1000000, account_id, amount, currency, transaction_type, status, created_at
            FROM {schema}.transactions WHERE transaction_id = %s
        """, (tid,))
        manifest.append({"fault_type": "DUPLICATE_ROW", "transaction_id": tid})


def inject_value_mismatch(cur, schema, n, manifest):
    ids = _get_random_transaction_ids(cur, schema, n)
    for tid in ids:
        cur.execute(f"UPDATE {schema}.transactions SET amount = amount + 100 WHERE transaction_id = %s", (tid,))
        manifest.append({"fault_type": "VALUE_MISMATCH", "transaction_id": tid})


def inject_null_injection(cur, schema, n, manifest):
    ids = _get_random_transaction_ids(cur, schema, n)
    for tid in ids:
        cur.execute(f"UPDATE {schema}.transactions SET status = NULL WHERE transaction_id = %s", (tid,))
        manifest.append({"fault_type": "NULL_INJECTION", "transaction_id": tid})


def inject_timestamp_shift(cur, schema, n, manifest):
    ids = _get_random_transaction_ids(cur, schema, n)
    for tid in ids:
        cur.execute(f"""
            UPDATE {schema}.transactions
            SET created_at = created_at + INTERVAL '3 days'
            WHERE transaction_id = %s
        """, (tid,))
        manifest.append({"fault_type": "TIMESTAMP_SHIFT", "transaction_id": tid})


FAULT_INJECTORS = {
    "missing": inject_missing_rows,
    "duplicate": inject_duplicate_rows,
    "value-mismatch": inject_value_mismatch,
    "null-injection": inject_null_injection,
    "timestamp-shift": inject_timestamp_shift,
}


def run_injection(schema: str, fault_counts: dict, manifest_path: str = "docker/fault_manifest.json"):
    conn = get_conn()
    cur = conn.cursor()

    manifest = []
    for fault_key, count in fault_counts.items():
        if count <= 0:
            continue
        injector_fn = FAULT_INJECTORS[fault_key]
        injector_fn(cur, schema, count, manifest)

    conn.commit()
    cur.close()
    conn.close()

    with open(manifest_path, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "schema": schema,
            "faults": manifest,
        }, f, indent=2)

    print(f"Injected {len(manifest)} faults. Manifest written to {manifest_path}")
    return manifest