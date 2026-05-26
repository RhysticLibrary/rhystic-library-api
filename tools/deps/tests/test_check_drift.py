"""Subprocess tests for check_drift.py CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEPS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DEPS_DIR / "check_drift.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestExitCodes:
    def test_clean_fixture_exits_zero(self):
        result = run_cli("--root", str(FIXTURES / "clean"))
        assert result.returncode == 0, result.stderr
        assert "no drift" in result.stdout.lower() or result.stdout.strip() == ""

    def test_drift_fixture_exits_one(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"))
        assert result.returncode == 1, result.stderr
        assert "pyyaml" in result.stdout
        assert ">=6.0.3" in result.stdout

    def test_human_report_lists_sightings_under_package_header(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"))
        assert result.returncode == 1
        # Package name appears, then sighting files appear in subsequent lines.
        lines = result.stdout.splitlines()
        pkg_idx = next(i for i, line in enumerate(lines) if "pyyaml" in line)
        body = "\n".join(lines[pkg_idx:])
        assert ".pre-commit-config.yaml" in body
        assert "requirements-dev.txt" in body


class TestJsonOutput:
    def test_json_flag_emits_parseable_array(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"), "--json")
        assert result.returncode == 1, result.stderr
        payload = json.loads(result.stdout)
        assert isinstance(payload, list)
        assert len(payload) == 1
        entry = payload[0]
        assert entry["package"] == "pyyaml"
        assert entry["status"] == "drift"
        assert entry["recommendation"].startswith("bump")
        files_seen = {s["file"] for s in entry["sightings"]}
        assert ".pre-commit-config.yaml" in files_seen
        assert "requirements-dev.txt" in files_seen

    def test_json_clean_fixture_returns_empty_array(self):
        result = run_cli("--root", str(FIXTURES / "clean"), "--json")
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload == []


class TestMalformedYaml:
    def test_malformed_yaml_exits_two_with_stderr_message(self):
        result = run_cli("--root", str(FIXTURES / "malformed"))
        assert result.returncode == 2
        assert "check_drift" in result.stderr
