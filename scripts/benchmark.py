"""
Phase A15 — Benchmark suite.
Compares a naive full-outer-join baseline against the hierarchical
reconciliation engine, at multiple dataset sizes. All numbers here
are real measurements from this machine — never hand-write a number.
"""
import time
import subprocess
import psutil
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extractors.metadata import get_conn
from app.reconciliation.pipeline import run_full_pipeline


def measure_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def run_naive_baseline(source_schema="core_banking", target_schema="reporting_replica"):
    """
    A fair, competent baseline: SQL EXCEPT run once per table,
    not a row-by-row Python loop with per-row DB round trips.
    """
    conn = get_conn()
    cur = conn.cursor()

    start = time.time()
    query_count = 0

    cur.execute(f"""
        SELECT transaction_id, account_id, amount, currency, transaction_type, status, created_at
        FROM {source_schema}.transactions
        EXCEPT
        SELECT transaction_id, account_id, amount, currency, transaction_type, status, created_at
        FROM {target_schema}.transactions
    """)
    source_minus_target = cur.fetchall()
    query_count += 1

    cur.execute(f"""
        SELECT transaction_id, account_id, amount, currency, transaction_type, status, created_at
        FROM {target_schema}.transactions
        EXCEPT
        SELECT transaction_id, account_id, amount, currency, transaction_type, status, created_at
        FROM {source_schema}.transactions
    """)
    target_minus_source = cur.fetchall()
    query_count += 1

    duration = time.time() - start
    row_diffs = len(source_minus_target) + len(target_minus_source)

    cur.close()
    conn.close()
    return duration, row_diffs, query_count


def run_hierarchical(source_schema="core_banking", target_schema="reporting_replica"):
    start = time.time()
    discrepancies = run_full_pipeline(source_schema, target_schema, persist=False)
    duration = time.time() - start
    return duration, len(discrepancies)


def benchmark_at_size(n_transactions: int):
    print(f"\n=== Benchmarking at {n_transactions} transactions ===")
    subprocess.run([
        sys.executable, "scripts/generate_data.py",
        "--accounts", "1000", "--transactions", str(n_transactions)
    ], check=True)

    mem_before = measure_memory_mb()
    naive_duration, naive_diffs, naive_queries = run_naive_baseline()
    mem_after_naive = measure_memory_mb()

    hier_duration, hier_diffs = run_hierarchical()
    mem_after_hier = measure_memory_mb()

    rows_per_sec_naive = n_transactions / naive_duration if naive_duration > 0 else 0
    rows_per_sec_hier = n_transactions / hier_duration if hier_duration > 0 else 0
    speedup = naive_duration / hier_duration if hier_duration > 0 else 0

    result = {
        "n_transactions": n_transactions,
        "naive": {
            "duration_seconds": round(naive_duration, 3),
            "rows_per_sec": round(rows_per_sec_naive, 1),
            "db_query_count": naive_queries,
            "memory_mb": round(mem_after_naive - mem_before, 2),
            "row_diffs_found": naive_diffs,
        },
        "hierarchical": {
            "duration_seconds": round(hier_duration, 3),
            "rows_per_sec": round(rows_per_sec_hier, 1),
            "memory_mb": round(mem_after_hier - mem_after_naive, 2),
            "discrepancies_found": hier_diffs,
        },
        "speedup_factor": round(speedup, 2),
    }
    return result


def main():
    results = []
    for size in (100_000, 1_000_000):
        results.append(benchmark_at_size(size))

    with open("docs/benchmarks.md", "w") as f:
        f.write("# DataGuard Core — Benchmarks\n\n")
        f.write("All numbers below are real measurements from an actual run on this machine.\n\n")
        for r in results:
            f.write(f"## {r['n_transactions']:,} transactions\n\n")
            f.write("| Metric | Naive (SQL EXCEPT) | Hierarchical |\n")
            f.write("|---|---|---|\n")
            f.write(f"| Duration (s) | {r['naive']['duration_seconds']} | {r['hierarchical']['duration_seconds']} |\n")
            f.write(f"| Rows/sec | {r['naive']['rows_per_sec']} | {r['hierarchical']['rows_per_sec']} |\n")
            f.write(f"| DB queries | {r['naive']['db_query_count']} | (multi-stage, see pipeline) |\n")
            f.write(f"| Discrepancies found | {r['naive']['row_diffs_found']} | {r['hierarchical']['discrepancies_found']} |\n")
            f.write(f"\n**Speedup: {r['speedup_factor']}x**\n\n")

    print("\nBenchmark results written to docs/benchmarks.md")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()