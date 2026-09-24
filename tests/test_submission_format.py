"""
Automated pytest suite validating all 20 benchmark case files in cases/.
"""

import os
import json
import pytest
from scripts.verify_submission import verify_all_cases


def test_submission_files_exist():
    assert os.path.exists("cases"), "cases/ directory must exist"
    files = [f for f in os.listdir("cases") if f.endswith(".json")]
    assert len(files) == 20, f"Expected 20 case files, found {len(files)}"


def test_submission_schema_valid():
    # Will raise SystemExit(1) if validation fails
    try:
        verify_all_cases("cases")
    except SystemExit as e:
        pytest.fail(f"Verification failed with exit code {e}")
