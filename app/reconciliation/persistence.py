"""
Phase A13 — Results persistence.
Writes reconciliation run results into dataguard_meta:
reconciliation_runs, discrepancies, schema_snapshots.
"""
import json
from datetime import datetime
from typing import List

from app.extractors.metadata import get_conn
from app.models.discrepancy import Discrepancy


def create_meta_tables():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dataguard_meta.reconciliation_runs (
            run_id SERIAL PRIMARY KEY,
            started_at TIMESTAMP NOT NULL,
            finished_at TIMESTAMP,
            duration_seconds NUMERIC,
            status TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dataguard_meta.discrepancies (
            id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES dataguard_meta.reconciliation_runs(run_id),
            table_name TEXT,
            row_pk BIGINT,
            field TEXT,
            fault_type TEXT,
            dollar_impact NUMERIC,
            account_id BIGINT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dataguard_meta.schema_snapshots (
            id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES dataguard_meta.reconciliation_runs(run_id),
            schema_name TEXT,
            snapshot_json JSONB,
            captured_at TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def start_run() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dataguard_meta.reconciliation_runs (started_at, status)
        VALUES (%s, 'running') RETURNING run_id
    """, (datetime.now(),))
    run_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return run_id


def finish_run(run_id: int, duration_seconds: float, total_rows_checked: int = None, status: str = "completed"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE dataguard_meta.reconciliation_runs
        SET finished_at = %s, duration_seconds = %s, total_rows_checked = %s, status = %s
        WHERE run_id = %s
    """, (datetime.now(), duration_seconds, total_rows_checked, status, run_id))
    conn.commit()
    cur.close()
    conn.close()


def save_discrepancies(run_id: int, discrepancies: List[Discrepancy]):
    if not discrepancies:
        return
    conn = get_conn()
    cur = conn.cursor()
    for d in discrepancies:
        cur.execute("""
            INSERT INTO dataguard_meta.discrepancies
            (run_id, table_name, row_pk, field, fault_type, dollar_impact, account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (run_id, d.table_name, d.row_pk, d.field, d.fault_type, d.dollar_impact, d.affected_account_id))
    conn.commit()
    cur.close()
    conn.close()


def save_schema_snapshot(run_id: int, schema_name: str, snapshot_dict: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dataguard_meta.schema_snapshots (run_id, schema_name, snapshot_json, captured_at)
        VALUES (%s, %s, %s, %s)
    """, (run_id, schema_name, json.dumps(snapshot_dict, default=str), datetime.now()))
    conn.commit()
    cur.close()
    conn.close()