"""Tests for skill helper scripts."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_TOOLS = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_TOOLS / script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


class TestListAdrs:
    def test_prints_one_line_per_adr_sorted(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000002-second.md").write_text(adr_factory({
            "id": '"000002"', "name": "second", "description": "Second decision.",
        }))
        (adr_dir / "000001-first.md").write_text(adr_factory({
            "id": '"000001"', "name": "first", "description": "First decision.",
        }))
        result = run_script("list_adrs.py", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0, result.stderr
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 2
        assert lines[0].startswith("000001")
        assert "First decision." in lines[0]
        assert lines[1].startswith("000002")

    def test_empty_dir_prints_nothing(self, adr_repo):
        result = run_script("list_adrs.py", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
