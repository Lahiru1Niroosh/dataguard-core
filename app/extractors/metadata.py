"""
Phase A4 — Metadata Discovery Engine.
Reads information_schema for a given schema and returns a
structured SchemaSnapshot (Pydantic model), not printed text.
"""
import os
import psycopg2
from dotenv import load_dotenv

from app.models.schema_models import ColumnInfo, TableInfo, SchemaSnapshot

load_dotenv()

DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "55432")
DB_NAME = os.getenv("DATABASE_NAME", "dataguard")
DB_USER = os.getenv("DATABASE_USER", "dataguard")
DB_PASS = os.getenv("DATABASE_PASSWORD", "dataguard_dev_pw")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def get_primary_keys(cur, schema_name, table_name):
    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tco
        JOIN information_schema.key_column_usage kcu
          ON tco.constraint_name = kcu.constraint_name
         AND tco.table_schema = kcu.table_schema
        WHERE tco.constraint_type = 'PRIMARY KEY'
          AND tco.table_schema = %s
          AND tco.table_name = %s
    """, (schema_name, table_name))
    return {row[0] for row in cur.fetchall()}


def get_schema_snapshot(schema_name: str) -> SchemaSnapshot:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """, (schema_name,))
    table_names = [row[0] for row in cur.fetchall()]

    tables = []
    for table_name in table_names:
        pk_columns = get_primary_keys(cur, schema_name, table_name)

        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))

        columns = [
            ColumnInfo(
                column_name=row[0],
                data_type=row[1],
                is_nullable=(row[2] == "YES"),
                is_primary_key=(row[0] in pk_columns),
            )
            for row in cur.fetchall()
        ]
        tables.append(TableInfo(table_name=table_name, columns=columns))

    cur.close()
    conn.close()
    return SchemaSnapshot(schema_name=schema_name, tables=tables)