"""
Phase A17 — CLI entrypoint.
Usage: python -m app.cli run
Runs the full demo: generate data, inject faults, reconcile, print summary.
"""
import argparse
import subprocess
import sys

from app.faults.injector import run_injection
from app.reconciliation.pipeline import run_full_pipeline
from app.reconciliation.persistence import create_meta_tables


def run_demo():
    print("=== DataGuard Core Demo ===\n")

    print("[1/4] Generating synthetic banking dataset...")
    subprocess.run(
        [sys.executable, "scripts/generate_data.py", "--accounts", "1000", "--transactions", "100000"],
        check=True,
    )

    print("\n[2/4] Setting up metadata tables...")
    create_meta_tables()

    print("\n[3/4] Injecting known faults into reporting_replica...")
    manifest = run_injection("reporting_replica", {
        "missing": 20,
        "duplicate": 5,
        "value-mismatch": 20,
        "null-injection": 15,
        "timestamp-shift": 10,
    })
    print(f"Injected {len(manifest)} faults.")

    print("\n[4/4] Running hierarchical reconciliation pipeline...\n")
    discrepancies = run_full_pipeline(persist=True)

    print(f"\n=== Summary ===")
    print(f"Total discrepancies detected: {len(discrepancies)}")

    by_type = {}
    total_dollar_impact = 0.0
    for d in discrepancies:
        by_type[d.fault_type] = by_type.get(d.fault_type, 0) + 1
        total_dollar_impact += d.dollar_impact

    for fault_type, count in sorted(by_type.items()):
        print(f"  {fault_type}: {count}")

    print(f"Total dollar impact: ${total_dollar_impact:,.2f}")


def main():
    parser = argparse.ArgumentParser(description="DataGuard Core CLI")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="Run the full demo pipeline")

    args = parser.parse_args()

    if args.command == "run":
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()