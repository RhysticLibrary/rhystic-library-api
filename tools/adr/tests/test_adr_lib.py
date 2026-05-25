"""Tests for adr_lib helpers."""
from __future__ import annotations

import pytest
from adr_lib import (
    ADR_FILENAME_RE,
    enumerate_adrs,
    iter_frontmatters,
    parse_frontmatter,
    parse_header_table,
    parse_tags_file,
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

    def test_non_mapping_yaml_raises_typeerror(self):
        # A YAML scalar or sequence at the top is a type error, not a value error.
        text = "---\n- just a list\n---\n"
        with pytest.raises(TypeError, match="mapping"):
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

    def test_returns_non_matching_files_for_validator_to_flag(self, adr_repo, adr_factory):
        # Non-conforming .md files must NOT be silently dropped — the validator
        # is responsible for reporting them. Dropping them here would let a
        # stray draft.md bypass every downstream check.
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-real.md").write_text(adr_factory())
        (adr_dir / "draft.md").write_text("not an adr")
        (adr_dir / "12345-too-short.md").write_text("not an adr")
        result = enumerate_adrs(adr_dir)
        assert [p.name for p in result] == [
            "000001-real.md",
            "12345-too-short.md",
            "draft.md",
        ]


class TestIterFrontmatters:
    def test_yields_path_and_frontmatter_pairs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-first.md").write_text(adr_factory({"id": '"000001"', "name": "first"}))
        (adr_dir / "000002-second.md").write_text(adr_factory({"id": '"000002"', "name": "second"}))
        paths = enumerate_adrs(adr_dir)
        result = list(iter_frontmatters(paths))
        assert [p.name for p, _fm in result] == ["000001-first.md", "000002-second.md"]
        assert [fm["name"] for _p, fm in result] == ["first", "second"]

    def test_skips_unparseable_files_silently(self, adr_repo, adr_factory):
        # iter_frontmatters absorbs ValueError (missing/malformed frontmatter)
        # AND TypeError (non-mapping YAML) so downstream checks don't crash.
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-good.md").write_text(adr_factory({"name": "good"}))
        (adr_dir / "000002-noframe.md").write_text("# Just a heading, no frontmatter")
        (adr_dir / "000003-listframe.md").write_text("---\n- not a mapping\n---\n# x")
        paths = enumerate_adrs(adr_dir)
        result = list(iter_frontmatters(paths))
        assert [p.name for p, _fm in result] == ["000001-good.md"]


class TestAdrFilenameRegex:
    def test_matches_valid_names(self):
        match = ADR_FILENAME_RE.match("000042-some-kebab-slug.md")
        assert match is not None
        assert match.group("id") == "000042"
        assert match.group("slug") == "some-kebab-slug"

    def test_rejects_invalid_names(self):
        assert ADR_FILENAME_RE.match("draft.md") is None
        assert ADR_FILENAME_RE.match("12345-too-short.md") is None
        assert ADR_FILENAME_RE.match("000001-Has-Capitals.md") is None


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
        # The "alpha" line below contains an intentional en-dash to exercise that path.
        path = tmp_path / "_tags.md"
        path.write_text(
            "# Allowed ADR Tags\n\n"
            "- **alpha** – en-dash separator.\n"  # noqa: RUF001
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
