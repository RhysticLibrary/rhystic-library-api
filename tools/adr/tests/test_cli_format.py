"""Tests for cli_format helpers."""

from __future__ import annotations

from cli_format import summary_line


class TestSummaryLine:
    def test_renders_all_fields(self):
        fm = {
            "id": "000001",
            "status": "Accepted",
            "tags": ["meta", "process"],
            "description": "A decision.",
        }
        assert summary_line(fm) == "000001\tAccepted\t[meta,process]\tA decision."

    def test_empty_tags_render_as_empty_brackets(self):
        fm = {"id": "000002", "status": "Proposed", "tags": [], "description": "x"}
        assert summary_line(fm) == "000002\tProposed\t[]\tx"

    def test_none_tags_safe(self):
        fm = {"id": "000003", "status": "Accepted", "tags": None, "description": "x"}
        assert summary_line(fm) == "000003\tAccepted\t[]\tx"

    def test_missing_fields_get_placeholders(self):
        assert summary_line({}) == "------\t?\t[]\t"
