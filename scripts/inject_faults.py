"""
Phase A12 CLI entrypoint.
Usage: python scripts/inject_faults.py --missing 50 --duplicate 10 --value-mismatch 20
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.faults.injector import run_injection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--missing", type=int, default=0)
    parser.add_argument("--duplicate", type=int, default=0)
    parser.add_argument("--value-mismatch", type=int, default=0)
    parser.add_argument("--null-injection", type=int, default=0)
    parser.add_argument("--timestamp-shift", type=int, default=0)
    args = parser.parse_args()

    fault_counts = {
        "missing": args.missing,
        "duplicate": args.duplicate,
        "value-mismatch": args.value_mismatch,
        "null-injection": args.null_injection,
        "timestamp-shift": args.timestamp_shift,
    }

    run_injection("reporting_replica", fault_counts)


if __name__ == "__main__":
    main()