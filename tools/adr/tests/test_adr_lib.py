"""Tests for adr_lib helpers."""
from __future__ import annotations
from pathlib import Path
import pytest

from adr_lib import (
    parse_frontmatter,
    enumerate_adrs,
    parse_tags_file,
    parse_header_table,
)


class TestParseFrontmatter:
    def test_extracts_simple_fields(self, fm_factory):
        fm = parse_frontmatter(fm_factory())
        assert fm["id"] == "000001"
        assert fm["name"] == "test-adr"
        assert fm["status"] == "Accepted"
        assert fm["tags"] == ["meta"]
        assert fm["supersedes"] == []

    def test_quoted_id_preserves_leading_zeros(self, fm_factory):
        fm = parse_frontmatter(fm_factory(id='"000042"'))
        assert fm["id"] == "000042"

    def test_empty_date_is_empty_string(self, fm_factory):
        fm = parse_frontmatter(fm_factory(**{"date-accepted": '""'}))
        assert fm["date-accepted"] == ""

    def test_missing_frontmatter_raises(self):
        with pytest.raises(ValueError, match="no frontmatter"):
            parse_frontmatter("# Just a title\nbody")

    def test_malformed_yaml_raises(self):
        text = "---\nid: [unclosed\n---\n"
        with pytest.raises(ValueError, match="malformed"):
            parse_frontmatter(text)

    def test_accepts_crlf_line_endings(self, fm_factory):
        crlf_text = fm_factory().replace("\n", "\r\n")
        fm = parse_frontmatter(crlf_text)
        assert fm["id"] == "000001"
        assert fm["name"] == "test-adr"


class TestEnumerateAdrs:
    def test_returns_empty_when_no_adrs(self, adr_repo):
        assert enumerate_adrs(adr_repo / "docs" / "adr") == []

    def test_returns_adrs_sorted_by_id(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000002-second.md").write_text(adr_factory({"id": '"000002"', "name": "second"}))
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "first"}))
        result = enumerate_adrs(adr_dir)
        assert [p.name for p in result] == ["000001-first.md", "000002-second.md"]

    def test_skips_underscore_files(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-real.md").write_text(adr_factory())
        # _template.md and _tags.md must be ignored
        (adr_dir / "_template.md").write_text("template")
        result = enumerate_adrs(adr_dir)
        assert [p.name for p in result] == ["000001-real.md"]

    def test_skips_non_matching_files(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-real.md").write_text(adr_factory())
        (adr_dir / "draft.md").write_text("not an adr")
        (adr_dir / "12345-too-short.md").write_text("not an adr")
        result = enumerate_adrs(adr_dir)
        assert [p.name for p in result] == ["000001-real.md"]


class TestParseTagsFile:
    def test_parses_seed_tags(self, adr_repo):
        tags = parse_tags_file(adr_repo / "docs" / "adr" / "_tags.md")
        assert tags == {
            "documentation": "Decisions about docs.",
            "meta": "Decisions about the ADR process itself.",
            "process": "Decisions about how work is done.",
        }

    def test_ignores_lines_that_arent_tag_entries(self, tmp_path):
        path = tmp_path / "_tags.md"
        path.write_text(
            "# Allowed ADR Tags\n\n"
            "Some prose.\n\n"
            "- **alpha** — first tag.\n"
            "- not a tag entry\n"
            "- **beta** — second tag.\n"
        )
        tags = parse_tags_file(path)
        assert tags == {"alpha": "first tag.", "beta": "second tag."}

    def test_accepts_en_dash_separator(self, tmp_path):
        path = tmp_path / "_tags.md"
        path.write_text(
            "# Allowed ADR Tags\n\n"
            "- **alpha** – en-dash separator.\n"
            "- **beta** — em-dash separator.\n"
            "- **gamma** - hyphen separator.\n"
        )
        tags = parse_tags_file(path)
        assert tags == {
            "alpha": "en-dash separator.",
            "beta": "em-dash separator.",
            "gamma": "hyphen separator.",
        }


class TestParseHeaderTable:
    def test_extracts_all_fields(self, table_factory):
        body = "# Title\n\n" + table_factory()
        table = parse_header_table(body)
        assert table["Status"] == "Accepted"
        assert table["Date Proposed"] == "2026-05-24"
        assert table["Date Invalidated"] == "—"
        assert table["Authors"] == "Steven Timothy"
        assert table["Tags"] == "meta"

    def test_missing_table_raises(self):
        with pytest.raises(ValueError, match="header table"):
            parse_header_table("# Title\n\nNo table here.")
