"""Tests for the ADR validator."""
from __future__ import annotations
from pathlib import Path

import pytest

from validate import validate_repo


class TestNumberingCheck:
    def test_passes_with_no_adrs(self, adr_repo):
        errors = validate_repo(adr_repo / "docs" / "adr")
        assert errors == []

    def test_passes_with_sequential_ids(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "first"}))
        (adr_dir / "000002-second.md").write_text(adr_factory({"id": '"000002"', "name": "second"}))
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "numbering" in e.lower() or "gap" in e.lower()] == []

    def test_fails_on_gap(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "first"}))
        (adr_dir / "000003-third.md").write_text(adr_factory({"id": '"000003"', "name": "third"}))
        errors = validate_repo(adr_dir)
        assert any("gap" in e.lower() and "000002" in e for e in errors)

    def test_fails_on_duplicate_id(self, adr_repo, adr_factory, tmp_path):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "first"}))
        (adr_dir / "000001-other.md").write_text(adr_factory({"id": '"000001"', "name": "other"}))
        errors = validate_repo(adr_dir)
        # Filename uniqueness collision shows up; check we caught it.
        assert any("duplicate" in e.lower() for e in errors)

    def test_fails_when_filename_id_mismatches_frontmatter_id(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000099"', "name": "first"}))
        errors = validate_repo(adr_dir)
        assert any("filename" in e.lower() and "id" in e.lower() for e in errors)

    def test_fails_when_filename_slug_mismatches_frontmatter_name(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "different"}))
        errors = validate_repo(adr_dir)
        assert any("slug" in e.lower() or "name" in e.lower() for e in errors)
