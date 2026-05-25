"""Tests for the ADR validator."""

from __future__ import annotations

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

    def test_fails_on_duplicate_id(self, adr_repo, adr_factory):
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

    def test_fails_on_stray_non_adr_markdown_in_dir(self, adr_repo, adr_factory):
        # A user drops draft.md into docs/adr/ — validator must flag it, not
        # silently skip. Regression test for codex P1 finding (enumerate_adrs
        # used to drop non-matching filenames, hiding them from every check).
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-real.md").write_text(adr_factory())
        (adr_dir / "draft.md").write_text("not an ADR\n")
        errors = validate_repo(adr_dir)
        assert any("draft.md" in e and "filename does not match" in e for e in errors)

    def test_does_not_crash_on_non_mapping_yaml_frontmatter(self, adr_repo, adr_factory):
        # Regression: parse_frontmatter raises TypeError (not ValueError) when
        # the YAML body is a scalar or sequence. Checks must absorb both so the
        # validator surfaces a real error instead of crashing.
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-real.md").write_text(adr_factory())
        (adr_dir / "000002-listframe.md").write_text("---\n- just a list\n---\n# x\n")
        errors = validate_repo(adr_dir, merge_gate=True)
        # We don't assert on a specific message here — only that the call
        # completed and produced some errors (the numbering check will report
        # the filename id/name mismatch for the malformed file).
        assert isinstance(errors, list)


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
        fm_text = "\n".join(line for line in fm_text.splitlines() if not line.startswith("description:")) + "\n"
        sections = (
            "\n## Context and Problem Statement\nx\n"
            "## Considered Options\nx\n"
            "## Decision Outcome\nx\n"
            "## Consequences\nx\n"
        )
        body = fm_text + "\n# ADR 000001: Foo\n\n" + table_factory() + sections
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
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "date-proposed": '"not-a-date"',
                }
            )
        )
        errors = validate_repo(adr_dir)
        assert any("date-proposed" in e for e in errors)

    def test_fails_on_empty_tags(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo", "tags": "[]"}))
        errors = validate_repo(adr_dir)
        assert any("tags" in e.lower() and ("empty" in e.lower() or "non-empty" in e.lower()) for e in errors)

    def test_fails_when_supersedes_references_missing_adr(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "supersedes": '["000099"]',
                }
            )
        )
        errors = validate_repo(adr_dir)
        assert any("supersedes" in e.lower() and "000099" in e for e in errors)


class TestTagMembershipCheck:
    def test_passes_when_all_tags_known(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "tags": "[meta, process]",
                }
            )
        )
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "unknown tag" in e.lower()] == []

    def test_fails_on_unknown_tag(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "tags": "[meta, ghost]",
                }
            )
        )
        errors = validate_repo(adr_dir)
        assert any("unknown tag" in e.lower() and "ghost" in e for e in errors)

    def test_fails_when_tags_file_missing(self, tmp_path, adr_factory):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}))
        errors = validate_repo(adr_dir)
        assert any("_tags.md" in e for e in errors)


class TestBodyStructureCheck:
    def test_passes_with_complete_body(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}))
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "h1" in e.lower() or "section" in e.lower() or "table" in e.lower()] == []

    def test_fails_on_missing_h1(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        adr = adr_factory({"name": "foo"}, title="## Not an H1")
        (adr_dir / "000001-foo.md").write_text(adr)
        errors = validate_repo(adr_dir)
        assert any("h1" in e.lower() for e in errors)

    def test_fails_when_required_section_missing(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        sections = [
            "## Context and Problem Statement\nx",
            "## Considered Options\nx",
            # Decision Outcome missing
            "## Consequences\nx",
        ]
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}, sections=sections))
        errors = validate_repo(adr_dir)
        assert any("Decision Outcome" in e for e in errors)

    def test_fails_when_authors_empty(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {"name": "foo"},
                table_overrides={"Authors": "—"},
            )
        )
        errors = validate_repo(adr_dir)
        assert any("Authors" in e for e in errors)

    def test_fails_when_table_missing_a_field(self, adr_repo, fm_factory):
        adr_dir = adr_repo / "docs" / "adr"
        # Build a body whose table is missing the Authors row entirely.
        fm = fm_factory(name="foo")
        partial_table = (
            "| Field         | Value                |\n"
            "|---------------|----------------------|\n"
            "| Status        | Accepted             |\n"
            "| Date Proposed | 2026-05-24           |\n"
            "| Date Accepted | 2026-05-24           |\n"
            "| Date Invalidated | —                 |\n"
            "| Supersedes    | —                    |\n"
            "| Superseded By | —                    |\n"
            "| Tags          | meta                 |\n"
        )
        sections = (
            "\n## Context and Problem Statement\nx\n"
            "## Considered Options\nx\n"
            "## Decision Outcome\nx\n"
            "## Consequences\nx\n"
        )
        body = fm + "\n# ADR 000001: Foo\n\n" + partial_table + sections
        (adr_dir / "000001-foo.md").write_text(body)
        errors = validate_repo(adr_dir)
        assert any("Authors" in e for e in errors)

    def test_passes_with_crlf_line_endings(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        crlf = adr_factory({"name": "foo"}).replace("\n", "\r\n")
        (adr_dir / "000001-foo.md").write_text(crlf)
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "h1" in e.lower() or "header table" in e.lower()] == []


class TestFrontmatterTableConsistency:
    def test_fails_when_status_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {"name": "foo", "status": "Accepted"},
                table_overrides={"Status": "Proposed"},
            )
        )
        errors = validate_repo(adr_dir)
        assert any("Status" in e and "frontmatter" in e.lower() for e in errors)

    def test_fails_when_date_proposed_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {"name": "foo", "date-proposed": '"2026-05-24"'},
                table_overrides={"Date Proposed": "2026-05-25"},
            )
        )
        errors = validate_repo(adr_dir)
        assert any("Date Proposed" in e for e in errors)

    def test_empty_date_pairs_with_emdash(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        # Both empty ↔ em-dash: valid pairing.
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {"name": "foo", "date-invalidated": '""'},
                table_overrides={"Date Invalidated": "—"},
            )
        )
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "Date Invalidated" in e] == []

    def test_fails_when_tags_differ(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {"name": "foo", "tags": "[meta, process]"},
                table_overrides={"Tags": "meta"},
            )
        )
        errors = validate_repo(adr_dir)
        assert any("Tags" in e for e in errors)

    def test_fails_when_supersedes_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"id": '"000001"', "name": "foo"}))
        (adr_dir / "000002-bar.md").write_text(
            adr_factory(
                {"id": '"000002"', "name": "bar", "supersedes": '["000001"]'},
                table_overrides={"Supersedes": "—"},
            )
        )
        errors = validate_repo(adr_dir)
        assert any("Supersedes" in e for e in errors)


class TestMergeGate:
    def test_off_by_default(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Proposed",
                    "date-accepted": '""',
                    "date-invalidated": '""',
                },
                table_overrides={
                    "Status": "Proposed",
                    "Date Accepted": "—",
                    "Date Invalidated": "—",
                },
            )
        )
        errors = validate_repo(adr_dir, merge_gate=False)
        assert [e for e in errors if "merge gate" in e.lower()] == []

    def test_blocks_proposed_under_strict(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Proposed",
                    "date-accepted": '""',
                    "date-invalidated": '""',
                },
                table_overrides={
                    "Status": "Proposed",
                    "Date Accepted": "—",
                    "Date Invalidated": "—",
                },
            )
        )
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("merge gate" in e.lower() and "Proposed" in e for e in errors)

    def test_accepted_requires_date_accepted(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Accepted",
                    "date-accepted": '""',
                },
                table_overrides={"Date Accepted": "—"},
            )
        )
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("date-accepted" in e for e in errors)

    def test_superseded_requires_date_invalidated_and_supersededby(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Superseded",
                    "date-accepted": '"2026-05-24"',
                    "date-invalidated": '""',
                    "superseded-by": "[]",
                },
                table_overrides={
                    "Status": "Superseded",
                    "Date Invalidated": "—",
                    "Superseded By": "—",
                },
            )
        )
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("date-invalidated" in e for e in errors)
        assert any("superseded-by" in e for e in errors)

    def test_invalidated_must_be_on_or_after_accepted(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Deprecated",
                    "date-accepted": '"2026-05-24"',
                    "date-invalidated": '"2026-05-20"',
                },
                table_overrides={
                    "Status": "Deprecated",
                    "Date Invalidated": "2026-05-20",
                },
            )
        )
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("on or after" in e.lower() for e in errors)

    def test_proposed_must_have_empty_date_invalidated(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(
            adr_factory(
                {
                    "name": "foo",
                    "status": "Proposed",
                    "date-accepted": '""',
                    "date-invalidated": '"2026-05-25"',
                },
                table_overrides={
                    "Status": "Proposed",
                    "Date Accepted": "—",
                    "Date Invalidated": "2026-05-25",
                },
            )
        )
        # merge_gate=False still runs the empty-invalidated rule? Per spec, this is a
        # merge-gate rule, so it's only enforced under strict mode.
        errors_loose = validate_repo(adr_dir, merge_gate=False)
        assert [e for e in errors_loose if "date-invalidated" in e and "empty" in e.lower()] == []
        errors_strict = validate_repo(adr_dir, merge_gate=True)
        assert any("date-invalidated" in e and "empty" in e.lower() for e in errors_strict)
