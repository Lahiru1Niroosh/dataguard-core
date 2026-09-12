"""
Phase A3 — generates synthetic core_banking data and copies it
(initially identical) into reporting_replica.
"""
import os
import random
import argparse
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "dataguard")
DB_USER = os.getenv("DATABASE_USER", "dataguard")
DB_PASS = os.getenv("DATABASE_PASSWORD", "dataguard_dev_pw")

COUNTRIES = ["LK", "US", "UK", "IN", "AU"]
ACCOUNT_TYPES = ["savings", "current", "loan"]
ACCOUNT_STATUSES = ["active", "closed", "frozen"]
TXN_TYPES = ["deposit", "withdrawal", "transfer", "fee"]
TXN_STATUSES = ["completed", "pending", "reversed"]
CURRENCIES = ["USD", "LKR", "GBP"]


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def create_tables(cur, schema):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.accounts (
            account_id BIGINT PRIMARY KEY,
            customer_name TEXT,
            country TEXT,
            account_type TEXT,
            opened_at TIMESTAMP,
            status TEXT
        );
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.transactions (
            transaction_id BIGINT PRIMARY KEY,
            account_id BIGINT,
            amount NUMERIC(14,2),
            currency TEXT,
            transaction_type TEXT,
            status TEXT,
            created_at TIMESTAMP
        );
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.ledger_balances (
            account_id BIGINT PRIMARY KEY,
            balance NUMERIC(14,2),
            as_of TIMESTAMP
        );
    """)


def clear_tables(cur, schema):
    cur.execute(
        f"TRUNCATE TABLE {schema}.accounts, {schema}.transactions, "
        f"{schema}.ledger_balances"
    )


def generate_accounts(n):
    accounts = []
    start_date = datetime(2023, 1, 1)
    for i in range(1, n + 1):
        accounts.append((
            i,
            f"Customer_{i}",
            random.choice(COUNTRIES),
            random.choice(ACCOUNT_TYPES),
            start_date + timedelta(days=random.randint(0, 700)),
            random.choice(ACCOUNT_STATUSES),
        ))
    return accounts


def generate_transactions(n, num_accounts):
    txns = []
    start_date = datetime(2024, 1, 1)
    for i in range(1, n + 1):
        txns.append((
            i,
            random.randint(1, num_accounts),
            round(random.uniform(5, 5000), 2),
            random.choice(CURRENCIES),
            random.choice(TXN_TYPES),
            random.choice(TXN_STATUSES),
            start_date + timedelta(
                days=random.randint(0, 250),
                seconds=random.randint(0, 86400),
            ),
        ))
    return txns


def generate_ledger(num_accounts):
    now = datetime.now()
    return [
        (acc_id, round(random.uniform(0, 100000), 2), now)
        for acc_id in range(1, num_accounts + 1)
    ]


def insert_rows(cur, schema, table, columns, rows):
    placeholders = ",".join(["%s"] * len(columns))
    col_list = ",".join(columns)
    query = f"INSERT INTO {schema}.{table} ({col_list}) VALUES ({placeholders})"
    cur.executemany(query, rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accounts", type=int, default=1000)
    parser.add_argument("--transactions", type=int, default=100_000)
    args = parser.parse_args()

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()

    print("Creating tables in core_banking and reporting_replica...")
    create_tables(cur, "core_banking")
    create_tables(cur, "reporting_replica")
    clear_tables(cur, "core_banking")
    clear_tables(cur, "reporting_replica")

    print(f"Generating {args.accounts} accounts...")
    accounts = generate_accounts(args.accounts)

    print(f"Generating {args.transactions} transactions...")
    transactions = generate_transactions(args.transactions, args.accounts)

    print("Generating ledger balances...")
    ledger = generate_ledger(args.accounts)

    for schema in ("core_banking", "reporting_replica"):
        print(f"Loading data into {schema}...")
        insert_rows(
            cur,
            schema,
            "accounts",
            ("account_id", "customer_name", "country", "account_type", "opened_at", "status"),
            accounts,
        )
        insert_rows(
            cur,
            schema,
            "transactions",
            (
                "transaction_id",
                "account_id",
                "amount",
                "currency",
                "transaction_type",
                "status",
                "created_at",
            ),
            transactions,
        )
        insert_rows(
            cur,
            schema,
            "ledger_balances",
            ("account_id", "balance", "as_of"),
            ledger,
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Data generation complete.")


if __name__ == "__main__":
    main()