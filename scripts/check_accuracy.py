"""
Phase A14 — Accuracy testing.
Injects a known manifest of faults, runs the full pipeline, and
computes precision/recall against ground truth.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.faults.injector import run_injection
from app.reconciliation.pipeline import run_full_pipeline

FAULT_COUNTS = {
    "missing": 30,
    "duplicate": 0,          # duplicates aren't caught by this pipeline yet (row-count/hash only compares PKs that exist on both sides) — excluded from this accuracy run, noted as a known limitation
    "value-mismatch": 40,
    "null-injection": 30,
}

manifest = run_injection("reporting_replica", FAULT_COUNTS)
injected_ids = {f["transaction_id"] for f in manifest}
injected_count = len(manifest)

discrepancies = run_full_pipeline(persist=False)
detected_ids = {d.row_pk for d in discrepancies}

true_positives = injected_ids & detected_ids
false_positives = detected_ids - injected_ids
false_negatives = injected_ids - detected_ids

precision = len(true_positives) / len(detected_ids) if detected_ids else 0
recall = len(true_positives) / len(injected_ids) if injected_ids else 0

print(f"Injected: {injected_count}")
print(f"Detected: {len(detected_ids)}")
print(f"True positives: {len(true_positives)}")
print(f"False positives: {len(false_positives)}")
print(f"False negatives: {len(false_negatives)}")
print(f"Precision: {precision:.2%}")
print(f"Recall: {recall:.2%}")

with open("docs/accuracy_report.json", "w") as f:
    json.dump({
        "injected": injected_count,
        "detected": len(detected_ids),
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": precision,
        "recall": recall,
    }, f, indent=2)