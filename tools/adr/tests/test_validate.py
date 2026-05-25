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


class TestFrontmatterSchemaCheck:
    def test_passes_with_complete_frontmatter(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}))
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "frontmatter" in e.lower() or "missing" in e.lower()] == []

    def test_fails_on_missing_required_field(self, adr_repo, fm_factory, table_factory):
        adr_dir = adr_repo / "docs" / "adr"
        fm_text = fm_factory(name="foo")
        # Strip the description line.
        fm_text = "\n".join(l for l in fm_text.splitlines() if not l.startswith("description:")) + "\n"
        body = fm_text + "\n# ADR 000001: Foo\n\n" + table_factory() + "\n## Context and Problem Statement\nx\n## Considered Options\nx\n## Decision Outcome\nx\n## Consequences\nx\n"
        (adr_dir / "000001-foo.md").write_text(body)
        errors = validate_repo(adr_dir)
        assert any("description" in e.lower() and "missing" in e.lower() for e in errors)

    def test_fails_on_invalid_status(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo", "status": "Unknown"}))
        errors = validate_repo(adr_dir)
        assert any("status" in e.lower() and "unknown" in e.lower() for e in errors)

    def test_fails_on_invalid_date_format(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "date-proposed": '"not-a-date"',
        }))
        errors = validate_repo(adr_dir)
        assert any("date-proposed" in e for e in errors)

    def test_fails_on_empty_tags(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo", "tags": "[]"}))
        errors = validate_repo(adr_dir)
        assert any("tags" in e.lower() and ("empty" in e.lower() or "non-empty" in e.lower()) for e in errors)

    def test_fails_when_supersedes_references_missing_adr(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "supersedes": '["000099"]',
        }))
        errors = validate_repo(adr_dir)
        assert any("supersedes" in e.lower() and "000099" in e for e in errors)
