#!/usr/bin/env python3
"""Run API smoke tests. Execute with: .venv/bin/python _run_tests.py"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_api_smoke.py", "-v", "--tb=short"],
    capture_output=False,
)
sys.exit(result.returncode)
