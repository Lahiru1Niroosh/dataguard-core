"""
Shared pytest fixtures: creates a small, known dataset in
core_banking/reporting_replica before each test, using existing
scripts so we don't duplicate table-creation logic.
"""
import sys
import pytest
from app.extractors.metadata import get_conn


@pytest.fixture
def clean_db():
    """
    Wipes and regenerates a small, identical dataset in both schemas.
    Uses the same generator as the rest of the project so table
    structure stays consistent with production code.
    """
    import subprocess
    subprocess.run(
        [sys.executable, "scripts/generate_data.py", "--accounts", "50", "--transactions", "500"],
        check=True,
    )
    yield
    # No teardown needed — next test's clean_db call regenerates anyway.


def get_test_conn():
    return get_conn()