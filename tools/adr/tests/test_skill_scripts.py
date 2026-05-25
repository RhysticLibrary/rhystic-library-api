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


class TestFindAdrs:
    def _seed(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-auth.md").write_text(adr_factory({
            "id": '"000001"', "name": "auth",
            "description": "Auth decision.", "tags": "[process]",
        }))
        (adr_dir / "000002-logging.md").write_text(adr_factory({
            "id": '"000002"', "name": "logging",
            "description": "Logging decision.", "tags": "[meta]",
            "status": "Deprecated", "date-invalidated": '"2026-05-24"',
        }, table_overrides={"Status": "Deprecated", "Date Invalidated": "2026-05-24", "Tags": "meta"}))
        return adr_dir

    def test_filter_by_tag(self, adr_repo, adr_factory):
        self._seed(adr_repo, adr_factory)
        result = run_script("find_adrs.py", "--adr-dir", "docs/adr", "--tag", "process", cwd=adr_repo)
        assert result.returncode == 0
        assert "000001" in result.stdout and "000002" not in result.stdout

    def test_filter_by_status(self, adr_repo, adr_factory):
        self._seed(adr_repo, adr_factory)
        result = run_script("find_adrs.py", "--adr-dir", "docs/adr", "--status", "Deprecated", cwd=adr_repo)
        assert result.returncode == 0
        assert "000002" in result.stdout and "000001" not in result.stdout

    def test_filter_by_keyword(self, adr_repo, adr_factory):
        self._seed(adr_repo, adr_factory)
        result = run_script("find_adrs.py", "--adr-dir", "docs/adr", "--search", "logging", cwd=adr_repo)
        assert result.returncode == 0
        assert "000002" in result.stdout and "000001" not in result.stdout

    def test_filters_and_together(self, adr_repo, adr_factory):
        self._seed(adr_repo, adr_factory)
        result = run_script(
            "find_adrs.py", "--adr-dir", "docs/adr",
            "--status", "Accepted", "--tag", "meta",
            cwd=adr_repo,
        )
        # 000002 has tag meta but status Deprecated; AND eliminates it.
        assert "000002" not in result.stdout


class TestShowAdr:
    def test_prints_frontmatter_as_json(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}))
        result = run_script("show_adr.py", "000001", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["id"] == "000001"
        assert data["name"] == "foo"
        assert data["status"] == "Accepted"

    def test_unknown_id_exits_nonzero(self, adr_repo):
        result = run_script("show_adr.py", "999999", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode != 0


class TestListTags:
    def test_prints_tags_in_order(self, adr_repo):
        result = run_script("list_tags.py", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert lines[0].startswith("documentation\t")
        assert lines[1].startswith("meta\t")
        assert lines[2].startswith("process\t")


class TestTagUsage:
    def test_reports_usage_per_tag(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "id": '"000001"', "name": "foo", "tags": "[meta, process]",
        }))
        (adr_dir / "000002-bar.md").write_text(adr_factory({
            "id": '"000002"', "name": "bar", "tags": "[meta]",
        }))
        result = run_script("tag_usage.py", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert "documentation\t" in lines or "documentation\t\n" in result.stdout
        meta_line = next(l for l in lines if l.startswith("meta\t"))
        assert "000001" in meta_line and "000002" in meta_line
        process_line = next(l for l in lines if l.startswith("process\t"))
        assert process_line == "process\t000001"
