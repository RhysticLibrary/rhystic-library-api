# ADR Process and Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the ADR process for `rhystic-library-api`: create the directory layout, template, tags file, the first (meta) ADR codifying the process, three Claude skills with helper scripts, CI validation, and updated `README.md` / `CLAUDE.md`.

**Architecture:** All ADRs live under `docs/adr/` with sequential 6-digit IDs and YAML frontmatter mirrored by a human header table. A single Python validator (`tools/adr/validate.py`) enforces numbering, schema, tag membership, body structure, frontmatter↔table consistency, and a merge gate that blocks `Proposed` ADRs from landing on `main`. Three project-level skills under `.claude/skills/` give Claude operational entry points (search, tag discovery, creation), each backed by small Python scripts in `tools/adr/` so common operations don't require reading entire files.

**Tech Stack:** Python 3 (pyyaml, pytest), `markdownlint-cli2` (Node, run via npx in CI), GitHub Actions.

**Spec:** [`docs/superpowers/specs/2026-05-24-adr-process-design.md`](../specs/2026-05-24-adr-process-design.md)

---

## File Structure

**Created:**

- `pyproject.toml` — pytest configuration + dev dep markers.
- `requirements-dev.txt` — Python dev deps (pytest, pyyaml).
- `tools/adr/adr_lib.py` — shared frontmatter parser, ADR enumeration, tags-file parser, header-table parser.
- `tools/adr/validate.py` — CI validator (numbering, schema, tags, body, consistency, merge gate).
- `tools/adr/list_adrs.py` — overview lister (used by `searching-adrs` skill).
- `tools/adr/find_adrs.py` — filtered finder (used by `searching-adrs` skill).
- `tools/adr/show_adr.py` — single-ADR frontmatter printer (used by `searching-adrs` skill).
- `tools/adr/list_tags.py` — tag lister (used by `listing-adr-tags` skill).
- `tools/adr/tag_usage.py` — tag→ADRs cross-reference (used by `listing-adr-tags` skill).
- `tools/adr/new_adr.py` — scaffold a new ADR (used by `creating-an-adr` skill).
- `tools/adr/add_tag.py` — insert a new tag alphabetically into `_tags.md` (used by `creating-an-adr` skill).
- `tools/adr/tests/conftest.py` — shared pytest fixtures.
- `tools/adr/tests/test_adr_lib.py` — adr_lib tests.
- `tools/adr/tests/test_validate.py` — validator tests.
- `tools/adr/tests/test_skill_scripts.py` — skill script tests.
- `docs/adr/_tags.md` — alphabetical allowed-tags list.
- `docs/adr/_template.md` — copy-paste skeleton for new ADRs.
- `docs/adr/000001-adr-process-and-structure.md` — the first ADR (meta).
- `.claude/skills/searching-adrs/SKILL.md` — when/how to search ADRs.
- `.claude/skills/listing-adr-tags/SKILL.md` — when/how to discover tags.
- `.claude/skills/creating-an-adr/SKILL.md` — when/how to author a new ADR.
- `CLAUDE.md` — slim pointer to ADR 000001 and the three skills.
- `.markdownlint.jsonc` — markdownlint config.
- `.github/workflows/ci.yml` — markdown-lint and adr-validate jobs.

**Modified:**

- `README.md` — replace the single-line placeholder with project description + ADR pointer section.
- `.gitignore` — add Python artifacts (`__pycache__/`, `.pytest_cache/`).

---

## Task 1: Bootstrap Python tooling

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tools/adr/tests"]
pythonpath = ["tools/adr"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 2: Write `requirements-dev.txt`**

```
pytest>=8.0
pyyaml>=6.0
```

- [ ] **Step 3: Append Python artifacts to `.gitignore`**

Append these lines to the existing `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
```

- [ ] **Step 4: Create venv and install deps**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Expected: `Successfully installed pytest-... pyyaml-...`

- [ ] **Step 5: Verify pytest discovers no tests yet**

```bash
.venv/bin/pytest
```

Expected: `no tests ran in 0.0Xs` (exit code 5 is fine here; pytest distinguishes "no tests" from "tests failed").

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml requirements-dev.txt .gitignore
git commit -m "chore: bootstrap python dev tooling for adr scripts"
```

---

## Task 2: Shared `adr_lib.py` module

**Files:**
- Create: `tools/adr/adr_lib.py`
- Create: `tools/adr/tests/__init__.py` (empty)
- Create: `tools/adr/tests/conftest.py`
- Create: `tools/adr/tests/test_adr_lib.py`

`adr_lib.py` exposes four functions that every script needs:

- `parse_frontmatter(text: str) -> dict` — parses YAML frontmatter from the head of a markdown string. Raises `ValueError` if no frontmatter block is present.
- `enumerate_adrs(adr_dir: Path) -> list[Path]` — returns ADR file paths matching `NNNNNN-*.md`, sorted by ID. Skips files beginning with `_`.
- `parse_tags_file(tags_path: Path) -> dict[str, str]` — returns tag-slug → description mapping from `_tags.md`.
- `parse_header_table(text: str) -> dict[str, str]` — returns header table field → value mapping (e.g. `{"Status": "Accepted", "Date Proposed": "2026-05-24", ...}`).

- [ ] **Step 1: Write `tools/adr/tests/conftest.py` with shared fixtures**

```python
"""Shared pytest fixtures for ADR script tests."""
from __future__ import annotations
from pathlib import Path
from textwrap import dedent
import pytest


def make_frontmatter(**overrides: object) -> str:
    defaults: dict[str, object] = {
        "id": '"000001"',
        "name": "test-adr",
        "description": "A test ADR.",
        "status": "Accepted",
        "date-proposed": '"2026-05-24"',
        "date-accepted": '"2026-05-24"',
        "date-invalidated": '""',
        "supersedes": "[]",
        "superseded-by": "[]",
        "tags": "[meta]",
    }
    defaults.update({k: v for k, v in overrides.items()})
    lines = ["---"]
    for key, value in defaults.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def make_header_table(**overrides: str) -> str:
    defaults: dict[str, str] = {
        "Status": "Accepted",
        "Date Proposed": "2026-05-24",
        "Date Accepted": "2026-05-24",
        "Date Invalidated": "—",
        "Authors": "Steven Timothy",
        "Supersedes": "—",
        "Superseded By": "—",
        "Tags": "meta",
    }
    defaults.update(overrides)
    rows = ["| Field            | Value                                |",
            "|------------------|--------------------------------------|"]
    for key in ["Status", "Date Proposed", "Date Accepted", "Date Invalidated",
                "Authors", "Supersedes", "Superseded By", "Tags"]:
        rows.append(f"| {key:<16} | {defaults[key]:<36} |")
    return "\n".join(rows) + "\n"


def make_adr(
    fm_overrides: dict[str, object] | None = None,
    table_overrides: dict[str, str] | None = None,
    title: str = "# ADR 000001: Test ADR",
    sections: list[str] | None = None,
) -> str:
    fm = make_frontmatter(**(fm_overrides or {}))
    table = make_header_table(**(table_overrides or {}))
    if sections is None:
        sections = [
            "## Context and Problem Statement\nBody.",
            "## Considered Options\nOptions.",
            "## Decision Outcome\nOutcome.",
            "## Consequences\nConsequences.",
        ]
    return f"{fm}\n{title}\n\n{table}\n" + "\n\n".join(sections) + "\n"


@pytest.fixture
def adr_factory():
    return make_adr


@pytest.fixture
def fm_factory():
    return make_frontmatter


@pytest.fixture
def table_factory():
    return make_header_table


@pytest.fixture
def adr_repo(tmp_path: Path) -> Path:
    """Returns a temp dir with docs/adr/ and a seed _tags.md."""
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "_tags.md").write_text(dedent("""
        # Allowed ADR Tags

        - **documentation** — Decisions about docs.
        - **meta** — Decisions about the ADR process itself.
        - **process** — Decisions about how work is done.
        """).lstrip())
    return tmp_path
```

- [ ] **Step 2: Write the failing tests in `tools/adr/tests/test_adr_lib.py`**

```python
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
```

- [ ] **Step 3: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_adr_lib.py -v
```

Expected: `ModuleNotFoundError: No module named 'adr_lib'`

- [ ] **Step 4: Implement `tools/adr/adr_lib.py`**

```python
"""Shared helpers for ADR scripts."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_ADR_FILENAME_RE = re.compile(r"^(\d{6})-[a-z0-9-]+\.md$")
_TAG_LINE_RE = re.compile(r"^-\s*\*\*(?P<tag>[a-z0-9-]+)\*\*\s*[—-]\s*(?P<desc>.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\|\s*(?P<key>[^|]+?)\s*\|\s*(?P<value>[^|]+?)\s*\|\s*$")


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the YAML frontmatter block at the start of `text`."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("no frontmatter block at start of document")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"malformed YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def enumerate_adrs(adr_dir: Path) -> list[Path]:
    """Return ADR file paths sorted by 6-digit ID."""
    if not adr_dir.is_dir():
        return []
    matches = []
    for path in adr_dir.iterdir():
        if path.name.startswith("_"):
            continue
        if _ADR_FILENAME_RE.match(path.name):
            matches.append(path)
    return sorted(matches, key=lambda p: p.name)


def parse_tags_file(tags_path: Path) -> dict[str, str]:
    """Return {tag-slug: description} parsed from a _tags.md file."""
    tags: dict[str, str] = {}
    for line in tags_path.read_text().splitlines():
        match = _TAG_LINE_RE.match(line)
        if match:
            tags[match.group("tag")] = match.group("desc")
    return tags


def parse_header_table(text: str) -> dict[str, str]:
    """Return {field: value} parsed from the key-value header table."""
    rows: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.startswith("|") and "Field" in line and "Value" in line:
            in_table = True
            continue
        if in_table and re.match(r"^\|[-:\s|]+\|$", line):
            continue
        if in_table:
            match = _TABLE_ROW_RE.match(line)
            if match:
                rows[match.group("key")] = match.group("value")
            else:
                break
    if not rows:
        raise ValueError("could not locate header table")
    return rows
```

- [ ] **Step 5: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_adr_lib.py -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add tools/adr/adr_lib.py tools/adr/tests/
git commit -m "feat(adr): shared library for parsing ADR files"
```

---

## Task 3: Validator — numbering check

**Files:**
- Create: `tools/adr/validate.py`
- Create: `tools/adr/tests/test_validate.py`

The validator exposes one function `validate_repo(adr_dir, *, merge_gate=False) -> list[str]` returning a list of human-readable error strings. The CLI prints them and exits non-zero if non-empty. This task implements just the numbering check; later tasks add more checks.

- [ ] **Step 1: Write failing tests in `tools/adr/tests/test_validate.py`**

```python
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
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: `ModuleNotFoundError: No module named 'validate'`

- [ ] **Step 3: Implement `tools/adr/validate.py` (numbering only for now)**

```python
"""ADR validator. Returns a list of error messages; empty list means valid."""
from __future__ import annotations
import re
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


_FILENAME_RE = re.compile(r"^(?P<id>\d{6})-(?P<slug>[a-z0-9-]+)\.md$")


def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    return errors


def _check_numbering(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    parsed: list[tuple[Path, str, str]] = []  # (path, filename_id, filename_slug)

    for path in paths:
        match = _FILENAME_RE.match(path.name)
        if not match:
            errors.append(f"{path.name}: filename does not match NNNNNN-kebab-slug.md")
            continue
        fid = match.group("id")
        fslug = match.group("slug")
        if fid in seen_ids:
            errors.append(
                f"{path.name}: duplicate ID {fid} (also used by {seen_ids[fid].name})"
            )
            continue
        seen_ids[fid] = path
        parsed.append((path, fid, fslug))

    # Frontmatter id/name vs filename
    for path, fid, fslug in parsed:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if str(fm.get("id", "")) != fid:
            errors.append(
                f"{path.name}: filename id {fid} does not match frontmatter id {fm.get('id')!r}"
            )
        if fm.get("name") != fslug:
            errors.append(
                f"{path.name}: filename slug {fslug!r} does not match frontmatter name {fm.get('name')!r}"
            )

    # Gap detection
    ids_in_order = sorted(seen_ids.keys())
    for index, fid in enumerate(ids_in_order, start=1):
        expected = f"{index:06d}"
        if fid != expected:
            errors.append(
                f"numbering: expected ID {expected} but found {fid} "
                f"(gap or out-of-order)"
            )
            break
    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate ADR repository.")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    parser.add_argument("--merge-gate", action="store_true",
                        help="Enforce the merge gate (status must be Accepted/Deprecated/Superseded).")
    args = parser.parse_args(argv)
    errors = validate_repo(args.adr_dir, merge_gate=args.merge_gate)
    for err in errors:
        print(f"ADR-VALIDATE: {err}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator numbering check (IDs sequential, no gaps, no dupes)"
```

---

## Task 4: Validator — frontmatter schema check

**Files:**
- Modify: `tools/adr/validate.py`
- Modify: `tools/adr/tests/test_validate.py`

Adds a check that each ADR's frontmatter has all required fields with correct types and values.

- [ ] **Step 1: Add failing tests to `tools/adr/tests/test_validate.py`**

Append after the existing `TestNumberingCheck` class:

```python
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
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py::TestFrontmatterSchemaCheck -v
```

Expected: failures (the schema check doesn't exist yet).

- [ ] **Step 3: Extend `validate.py` with the schema check**

Add at top:

```python
from datetime import date
```

Add these constants and function near the existing helpers:

```python
_ALLOWED_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}
_REQUIRED_FIELDS = [
    "id", "name", "description", "status",
    "date-proposed", "date-accepted", "date-invalidated",
    "supersedes", "superseded-by", "tags",
]


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _check_frontmatter_schema(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    existing_ids = {_FILENAME_RE.match(p.name).group("id") for p in paths
                    if _FILENAME_RE.match(p.name)}
    for path in paths:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue  # numbering check already reported this
        for field in _REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"{path.name}: missing required frontmatter field '{field}'")
        if fm.get("status") not in _ALLOWED_STATUSES:
            errors.append(
                f"{path.name}: status {fm.get('status')!r} is unknown; "
                f"must be one of {sorted(_ALLOWED_STATUSES)}"
            )
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"{path.name}: description must be a non-empty string")
        if not _is_iso_date(fm.get("date-proposed")):
            errors.append(f"{path.name}: date-proposed must be ISO-8601 (YYYY-MM-DD), got {fm.get('date-proposed')!r}")
        for date_field in ("date-accepted", "date-invalidated"):
            value = fm.get(date_field)
            if value not in ("", None) and not _is_iso_date(value):
                errors.append(f"{path.name}: {date_field} must be ISO-8601 or empty, got {value!r}")
        tags = fm.get("tags")
        if not isinstance(tags, list) or len(tags) == 0:
            errors.append(f"{path.name}: tags must be a non-empty list")
        for ref_field in ("supersedes", "superseded-by"):
            refs = fm.get(ref_field, [])
            if not isinstance(refs, list):
                errors.append(f"{path.name}: {ref_field} must be a list")
                continue
            for ref in refs:
                if not (isinstance(ref, str) and re.fullmatch(r"\d{6}", ref)):
                    errors.append(f"{path.name}: {ref_field} entry {ref!r} must be a 6-digit ID string")
                    continue
                if ref not in existing_ids:
                    errors.append(f"{path.name}: {ref_field} references unknown ADR {ref}")
    return errors
```

Then wire it into `validate_repo`:

```python
def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    return errors
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator frontmatter schema check"
```

---

## Task 5: Validator — tag membership check

**Files:**
- Modify: `tools/adr/validate.py`
- Modify: `tools/adr/tests/test_validate.py`

Every tag in an ADR's `tags` list must exist in `_tags.md`.

- [ ] **Step 1: Add failing tests**

Append to `tools/adr/tests/test_validate.py`:

```python
class TestTagMembershipCheck:
    def test_passes_when_all_tags_known(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "tags": "[meta, process]",
        }))
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "unknown tag" in e.lower()] == []

    def test_fails_on_unknown_tag(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "tags": "[meta, ghost]",
        }))
        errors = validate_repo(adr_dir)
        assert any("unknown tag" in e.lower() and "ghost" in e for e in errors)

    def test_fails_when_tags_file_missing(self, tmp_path, adr_factory):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "000001-foo.md").write_text(adr_factory({"name": "foo"}))
        errors = validate_repo(adr_dir)
        assert any("_tags.md" in e for e in errors)
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py::TestTagMembershipCheck -v
```

Expected: failures.

- [ ] **Step 3: Extend validator**

Add to `validate.py`:

```python
from adr_lib import enumerate_adrs, parse_frontmatter, parse_tags_file


def _check_tag_membership(adr_dir: Path, paths: list[Path]) -> list[str]:
    errors: list[str] = []
    tags_path = adr_dir / "_tags.md"
    if not tags_path.is_file():
        errors.append(f"_tags.md missing at {tags_path}")
        return errors
    allowed = set(parse_tags_file(tags_path).keys())
    for path in paths:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue
        for tag in fm.get("tags", []) or []:
            if tag not in allowed:
                errors.append(
                    f"{path.name}: unknown tag {tag!r} (add it to _tags.md before use)"
                )
    return errors
```

Wire into `validate_repo`:

```python
def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    return errors
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator tag membership check"
```

---

## Task 6: Validator — body structure check

**Files:**
- Modify: `tools/adr/validate.py`
- Modify: `tools/adr/tests/test_validate.py`

Checks: H1 follows frontmatter, header table follows H1 with all eight fields, Authors non-empty, required level-2 sections present.

- [ ] **Step 1: Add failing tests**

```python
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
        (adr_dir / "000001-foo.md").write_text(adr_factory(
            {"name": "foo"}, table_overrides={"Authors": "—"},
        ))
        errors = validate_repo(adr_dir)
        assert any("Authors" in e for e in errors)

    def test_fails_when_table_missing_a_field(self, adr_repo, adr_factory, fm_factory):
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
        body = fm + "\n# ADR 000001: Foo\n\n" + partial_table + "\n## Context and Problem Statement\nx\n## Considered Options\nx\n## Decision Outcome\nx\n## Consequences\nx\n"
        (adr_dir / "000001-foo.md").write_text(body)
        errors = validate_repo(adr_dir)
        assert any("Authors" in e for e in errors)
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py::TestBodyStructureCheck -v
```

Expected: failures.

- [ ] **Step 3: Extend validator**

Add to `validate.py`:

```python
from adr_lib import enumerate_adrs, parse_frontmatter, parse_tags_file, parse_header_table


_REQUIRED_SECTIONS = [
    "Context and Problem Statement",
    "Considered Options",
    "Decision Outcome",
    "Consequences",
]
_REQUIRED_TABLE_FIELDS = [
    "Status", "Date Proposed", "Date Accepted", "Date Invalidated",
    "Authors", "Supersedes", "Superseded By", "Tags",
]


def _body_after_frontmatter(text: str) -> str:
    match = _FRONTMATTER_BLOCK_RE.match(text)
    return text[match.end():] if match else text


# Add to top imports / constants section:
_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def _check_body_structure(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        body = _body_after_frontmatter(text).lstrip("\n")

        # H1 check
        first_meaningful = next((l for l in body.splitlines() if l.strip()), "")
        if not first_meaningful.startswith("# "):
            errors.append(f"{path.name}: expected H1 immediately after frontmatter")
            continue

        # Header table presence + fields
        try:
            table = parse_header_table(body)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        for field in _REQUIRED_TABLE_FIELDS:
            if field not in table:
                errors.append(f"{path.name}: header table missing row '{field}'")
        if table.get("Authors", "").strip() in ("", "—"):
            errors.append(f"{path.name}: Authors must be non-empty")

        # Required level-2 sections
        for section in _REQUIRED_SECTIONS:
            pattern = re.compile(rf"^## {re.escape(section)}\s*$", re.MULTILINE)
            if not pattern.search(body):
                errors.append(f"{path.name}: missing required section '## {section}'")
    return errors
```

Wire into `validate_repo`:

```python
def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    errors.extend(_check_body_structure(paths))
    return errors
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator body structure check (H1, table, required sections)"
```

---

## Task 7: Validator — frontmatter ↔ header table consistency

**Files:**
- Modify: `tools/adr/validate.py`
- Modify: `tools/adr/tests/test_validate.py`

Check each pairing per the spec's mapping table.

- [ ] **Step 1: Add failing tests**

```python
class TestFrontmatterTableConsistency:
    def test_fails_when_status_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory(
            {"name": "foo", "status": "Accepted"},
            table_overrides={"Status": "Proposed"},
        ))
        errors = validate_repo(adr_dir)
        assert any("Status" in e and "frontmatter" in e.lower() for e in errors)

    def test_fails_when_date_proposed_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory(
            {"name": "foo", "date-proposed": '"2026-05-24"'},
            table_overrides={"Date Proposed": "2026-05-25"},
        ))
        errors = validate_repo(adr_dir)
        assert any("Date Proposed" in e for e in errors)

    def test_empty_date_pairs_with_emdash(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        # Both empty ↔ em-dash: valid pairing.
        (adr_dir / "000001-foo.md").write_text(adr_factory(
            {"name": "foo", "date-invalidated": '""'},
            table_overrides={"Date Invalidated": "—"},
        ))
        errors = validate_repo(adr_dir)
        assert [e for e in errors if "Date Invalidated" in e] == []

    def test_fails_when_tags_differ(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory(
            {"name": "foo", "tags": "[meta, process]"},
            table_overrides={"Tags": "meta"},
        ))
        errors = validate_repo(adr_dir)
        assert any("Tags" in e for e in errors)

    def test_fails_when_supersedes_differs(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({"id": '"000001"', "name": "foo"}))
        (adr_dir / "000002-bar.md").write_text(adr_factory(
            {"id": '"000002"', "name": "bar", "supersedes": '["000001"]'},
            table_overrides={"Supersedes": "—"},
        ))
        errors = validate_repo(adr_dir)
        assert any("Supersedes" in e for e in errors)
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py::TestFrontmatterTableConsistency -v
```

Expected: failures.

- [ ] **Step 3: Extend validator**

Add to `validate.py`:

```python
def _normalize_list(value: object) -> str:
    """Normalize a list-valued frontmatter field to its table representation."""
    if not value:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _normalize_table_list(value: str) -> str:
    return value.strip()


def _check_consistency(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        try:
            fm = parse_frontmatter(text)
            table = parse_header_table(_body_after_frontmatter(text))
        except ValueError:
            continue

        pairs: list[tuple[str, object, str]] = [
            ("Status", fm.get("status"), "Status"),
            ("Date Proposed", fm.get("date-proposed"), "Date Proposed"),
            ("Date Accepted", fm.get("date-accepted"), "Date Accepted"),
            ("Date Invalidated", fm.get("date-invalidated"), "Date Invalidated"),
            ("Tags", fm.get("tags"), "Tags"),
            ("Supersedes", fm.get("supersedes"), "Supersedes"),
            ("Superseded By", fm.get("superseded-by"), "Superseded By"),
        ]
        for label, fm_value, table_key in pairs:
            table_value = table.get(table_key, "").strip()
            if label in ("Date Accepted", "Date Invalidated"):
                expected_table = fm_value if fm_value else "—"
                if expected_table != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
            elif label in ("Tags", "Supersedes", "Superseded By"):
                expected_table = _normalize_list(fm_value)
                if expected_table != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
            else:
                if str(fm_value) != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
    return errors
```

Wire into `validate_repo`:

```python
def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    errors.extend(_check_body_structure(paths))
    errors.extend(_check_consistency(paths))
    return errors
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator frontmatter↔table consistency check"
```

---

## Task 8: Validator — merge gate

**Files:**
- Modify: `tools/adr/validate.py`
- Modify: `tools/adr/tests/test_validate.py`

Only enforced when `--merge-gate` is passed (or `merge_gate=True`). Rules from the spec:

- Status must be Accepted / Deprecated / Superseded (Proposed blocks merge).
- Accepted/Deprecated/Superseded requires `date-accepted` to be a valid date.
- Deprecated/Superseded requires `date-invalidated` to be a valid date on/after `date-accepted`.
- Proposed/Accepted requires `date-invalidated` to be empty.
- Superseded requires `superseded-by` to be non-empty.

- [ ] **Step 1: Add failing tests**

```python
class TestMergeGate:
    def test_off_by_default(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Proposed",
            "date-accepted": '""', "date-invalidated": '""',
        }, table_overrides={
            "Status": "Proposed", "Date Accepted": "—", "Date Invalidated": "—",
        }))
        errors = validate_repo(adr_dir, merge_gate=False)
        assert [e for e in errors if "merge gate" in e.lower()] == []

    def test_blocks_proposed_under_strict(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Proposed",
            "date-accepted": '""', "date-invalidated": '""',
        }, table_overrides={
            "Status": "Proposed", "Date Accepted": "—", "Date Invalidated": "—",
        }))
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("merge gate" in e.lower() and "Proposed" in e for e in errors)

    def test_accepted_requires_date_accepted(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Accepted", "date-accepted": '""',
        }, table_overrides={"Date Accepted": "—"}))
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("date-accepted" in e for e in errors)

    def test_superseded_requires_date_invalidated_and_supersededby(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Superseded",
            "date-accepted": '"2026-05-24"', "date-invalidated": '""',
            "superseded-by": "[]",
        }, table_overrides={
            "Status": "Superseded", "Date Invalidated": "—", "Superseded By": "—",
        }))
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("date-invalidated" in e for e in errors)
        assert any("superseded-by" in e for e in errors)

    def test_invalidated_must_be_on_or_after_accepted(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Deprecated",
            "date-accepted": '"2026-05-24"', "date-invalidated": '"2026-05-20"',
        }, table_overrides={
            "Status": "Deprecated", "Date Invalidated": "2026-05-20",
        }))
        errors = validate_repo(adr_dir, merge_gate=True)
        assert any("on or after" in e.lower() for e in errors)

    def test_proposed_must_have_empty_date_invalidated(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        (adr_dir / "000001-foo.md").write_text(adr_factory({
            "name": "foo", "status": "Proposed",
            "date-accepted": '""', "date-invalidated": '"2026-05-25"',
        }, table_overrides={
            "Status": "Proposed", "Date Accepted": "—", "Date Invalidated": "2026-05-25",
        }))
        # merge_gate=False still runs the empty-invalidated rule? Per spec, this is a
        # merge-gate rule, so it's only enforced under strict mode.
        errors_loose = validate_repo(adr_dir, merge_gate=False)
        assert [e for e in errors_loose if "date-invalidated" in e and "empty" in e.lower()] == []
        errors_strict = validate_repo(adr_dir, merge_gate=True)
        assert any("date-invalidated" in e and "empty" in e.lower() for e in errors_strict)
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py::TestMergeGate -v
```

Expected: failures.

- [ ] **Step 3: Extend validator**

```python
def _check_merge_gate(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue
        status = fm.get("status")
        date_accepted = fm.get("date-accepted") or ""
        date_invalidated = fm.get("date-invalidated") or ""
        superseded_by = fm.get("superseded-by") or []

        if status == "Proposed":
            errors.append(f"{path.name}: merge gate — status 'Proposed' blocks merge")
        if status in {"Accepted", "Deprecated", "Superseded"} and not _is_iso_date(date_accepted):
            errors.append(f"{path.name}: status {status!r} requires date-accepted to be a valid date")
        if status in {"Deprecated", "Superseded"}:
            if not _is_iso_date(date_invalidated):
                errors.append(f"{path.name}: status {status!r} requires date-invalidated to be a valid date")
            elif _is_iso_date(date_accepted) and date_invalidated < date_accepted:
                errors.append(
                    f"{path.name}: date-invalidated ({date_invalidated}) must be on or after date-accepted ({date_accepted})"
                )
        if status in {"Proposed", "Accepted"} and date_invalidated:
            errors.append(f"{path.name}: status {status!r} requires date-invalidated to be empty")
        if status == "Superseded" and not superseded_by:
            errors.append(f"{path.name}: status 'Superseded' requires non-empty superseded-by")
    return errors
```

Wire into `validate_repo`:

```python
def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    errors.extend(_check_body_structure(paths))
    errors.extend(_check_consistency(paths))
    if merge_gate:
        errors.extend(_check_merge_gate(paths))
    return errors
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_validate.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/validate.py tools/adr/tests/test_validate.py
git commit -m "feat(adr): validator merge gate (--merge-gate flag)"
```

---

## Task 9: Skill script — `list_adrs.py`

**Files:**
- Create: `tools/adr/list_adrs.py`
- Create: `tools/adr/tests/test_skill_scripts.py`

Prints one line per ADR: `<id> <status> [<tags>] <description>`. Sort by ID ascending.

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestListAdrs -v
```

Expected: failure (script does not exist).

- [ ] **Step 3: Implement `tools/adr/list_adrs.py`**

```python
"""List every ADR with id, status, tags, description."""
from __future__ import annotations
import argparse
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)
    for path in enumerate_adrs(args.adr_dir):
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            print(f"{path.name}\tINVALID\t[]\t<unparseable>")
            continue
        tags = ",".join(fm.get("tags", []) or [])
        print(f"{fm.get('id', '------')}\t{fm.get('status', '?')}\t[{tags}]\t{fm.get('description', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestListAdrs -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/list_adrs.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): list_adrs.py skill helper"
```

---

## Task 10: Skill script — `find_adrs.py`

**Files:**
- Create: `tools/adr/find_adrs.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

Filter ADRs by `--tag`, `--status`, and `--search` (AND-combined).

- [ ] **Step 1: Add failing tests**

```python
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
```

- [ ] **Step 2: Run tests, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestFindAdrs -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/find_adrs.py`**

```python
"""Filter ADRs by tag, status, and/or keyword (filters AND together)."""
from __future__ import annotations
import argparse
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    parser.add_argument("--tag", help="Restrict to ADRs containing this tag.")
    parser.add_argument("--status", help="Restrict to ADRs with this status.")
    parser.add_argument("--search", help="Substring match against name and description.")
    args = parser.parse_args(argv)

    for path in enumerate_adrs(args.adr_dir):
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue
        if args.tag and args.tag not in (fm.get("tags") or []):
            continue
        if args.status and fm.get("status") != args.status:
            continue
        if args.search:
            needle = args.search.lower()
            hay = f"{fm.get('name', '')} {fm.get('description', '')}".lower()
            if needle not in hay:
                continue
        tags = ",".join(fm.get("tags", []) or [])
        print(f"{fm.get('id', '------')}\t{fm.get('status', '?')}\t[{tags}]\t{fm.get('description', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestFindAdrs -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/find_adrs.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): find_adrs.py skill helper (tag/status/keyword filter)"
```

---

## Task 11: Skill script — `show_adr.py`

**Files:**
- Create: `tools/adr/show_adr.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

Prints the frontmatter of a single ADR as JSON.

- [ ] **Step 1: Add failing test**

```python
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
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestShowAdr -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/show_adr.py`**

```python
"""Print the frontmatter of a single ADR as JSON."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adr_id", help="6-digit ADR ID, e.g. 000001")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    for path in enumerate_adrs(args.adr_dir):
        if path.name.startswith(f"{args.adr_id}-"):
            fm = parse_frontmatter(path.read_text())
            print(json.dumps(fm, indent=2, sort_keys=True))
            return 0
    print(f"ADR {args.adr_id} not found in {args.adr_dir}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestShowAdr -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/show_adr.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): show_adr.py skill helper (frontmatter as JSON)"
```

---

## Task 12: Skill script — `list_tags.py`

**Files:**
- Create: `tools/adr/list_tags.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

Prints every tag with its description, one per line: `<tag>\t<description>`.

- [ ] **Step 1: Add failing test**

```python
class TestListTags:
    def test_prints_tags_in_order(self, adr_repo):
        result = run_script("list_tags.py", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert lines[0].startswith("documentation\t")
        assert lines[1].startswith("meta\t")
        assert lines[2].startswith("process\t")
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestListTags -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/list_tags.py`**

```python
"""List every allowed ADR tag and its description."""
from __future__ import annotations
import argparse
from pathlib import Path

from adr_lib import parse_tags_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)
    tags = parse_tags_file(args.adr_dir / "_tags.md")
    for tag in sorted(tags):
        print(f"{tag}\t{tags[tag]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestListTags -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/list_tags.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): list_tags.py skill helper"
```

---

## Task 13: Skill script — `tag_usage.py`

**Files:**
- Create: `tools/adr/tag_usage.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

For each tag, lists the ADR IDs that use it: `<tag>\t<id1>,<id2>,...`. Tags with zero ADRs appear with an empty list.

- [ ] **Step 1: Add failing test**

```python
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
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestTagUsage -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/tag_usage.py`**

```python
"""For each tag, list ADRs (by id) that use it."""
from __future__ import annotations
import argparse
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter, parse_tags_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    tags = parse_tags_file(args.adr_dir / "_tags.md")
    usage: dict[str, list[str]] = {tag: [] for tag in tags}
    for path in enumerate_adrs(args.adr_dir):
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue
        adr_id = str(fm.get("id", ""))
        for tag in fm.get("tags", []) or []:
            if tag in usage:
                usage[tag].append(adr_id)
    for tag in sorted(usage):
        print(f"{tag}\t{','.join(usage[tag])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestTagUsage -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/tag_usage.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): tag_usage.py skill helper"
```

---

## Task 14: Skill script — `new_adr.py`

**Files:**
- Create: `tools/adr/new_adr.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

Computes next sequential ID, copies `_template.md` to `docs/adr/<id>-<slug>.md`, fills `{{id}}`, `{{name}}`, `{{date-proposed}}`, prints new path. The template uses `{{...}}` placeholders for substitution.

For the test we hand-author a minimal `_template.md`; the real template comes later in Task 17.

- [ ] **Step 1: Add failing test**

```python
class TestNewAdr:
    def _write_template(self, adr_dir: Path) -> None:
        (adr_dir / "_template.md").write_text(
            "---\n"
            'id: "{{id}}"\n'
            "name: {{name}}\n"
            'date-proposed: "{{date-proposed}}"\n'
            "---\n\n# ADR {{id}}: TITLE\n"
        )

    def test_creates_first_adr_with_id_000001(self, adr_repo):
        self._write_template(adr_repo / "docs" / "adr")
        result = run_script("new_adr.py", "my-slug", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0, result.stderr
        out_path = adr_repo / "docs" / "adr" / "000001-my-slug.md"
        assert out_path.is_file()
        content = out_path.read_text()
        assert 'id: "000001"' in content
        assert "name: my-slug" in content
        assert "date-proposed: " in content
        assert result.stdout.strip().endswith("000001-my-slug.md")

    def test_increments_to_next_id(self, adr_repo, adr_factory):
        adr_dir = adr_repo / "docs" / "adr"
        self._write_template(adr_dir)
        (adr_dir / "000001-existing.md").write_text(adr_factory({"id": '"000001"', "name": "existing"}))
        result = run_script("new_adr.py", "next-thing", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode == 0
        assert (adr_dir / "000002-next-thing.md").is_file()

    def test_rejects_invalid_slug(self, adr_repo):
        self._write_template(adr_repo / "docs" / "adr")
        result = run_script("new_adr.py", "Bad Slug", "--adr-dir", "docs/adr", cwd=adr_repo)
        assert result.returncode != 0
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestNewAdr -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/new_adr.py`**

```python
"""Scaffold a new ADR by copying _template.md and filling id/name/date."""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="kebab-case slug for the new ADR")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    if not _SLUG_RE.match(args.slug):
        print(f"error: slug {args.slug!r} must be lowercase kebab-case", file=sys.stderr)
        return 2

    template_path = args.adr_dir / "_template.md"
    if not template_path.is_file():
        print(f"error: template missing at {template_path}", file=sys.stderr)
        return 2

    existing = enumerate_adrs(args.adr_dir)
    next_id = 1
    if existing:
        last_fm = parse_frontmatter(existing[-1].read_text())
        next_id = int(str(last_fm["id"])) + 1
    new_id = f"{next_id:06d}"

    today = date.today().isoformat()
    template = template_path.read_text()
    filled = (
        template
        .replace("{{id}}", new_id)
        .replace("{{name}}", args.slug)
        .replace("{{date-proposed}}", today)
    )

    out_path = args.adr_dir / f"{new_id}-{args.slug}.md"
    if out_path.exists():
        print(f"error: {out_path} already exists", file=sys.stderr)
        return 2
    out_path.write_text(filled)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestNewAdr -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/new_adr.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): new_adr.py scaffolds a new ADR from template"
```

---

## Task 15: Skill script — `add_tag.py`

**Files:**
- Create: `tools/adr/add_tag.py`
- Modify: `tools/adr/tests/test_skill_scripts.py`

Inserts `- **<slug>** — <description>` into `_tags.md` at the correct alphabetical position. Idempotent: re-running with an existing slug is a no-op (and exits 0). Description must be supplied.

- [ ] **Step 1: Add failing test**

```python
class TestAddTag:
    def test_inserts_in_alphabetical_order(self, adr_repo):
        adr_dir = adr_repo / "docs" / "adr"
        result = run_script(
            "add_tag.py", "ci", "Decisions about CI pipelines.",
            "--adr-dir", "docs/adr", cwd=adr_repo,
        )
        assert result.returncode == 0, result.stderr
        text = (adr_dir / "_tags.md").read_text()
        lines = [l for l in text.splitlines() if l.startswith("- **")]
        # ci sorts between documentation and meta? alpha order: ci, documentation, meta, process
        assert lines == [
            "- **ci** — Decisions about CI pipelines.",
            "- **documentation** — Decisions about docs.",
            "- **meta** — Decisions about the ADR process itself.",
            "- **process** — Decisions about how work is done.",
        ]

    def test_no_op_when_tag_exists(self, adr_repo):
        adr_dir = adr_repo / "docs" / "adr"
        before = (adr_dir / "_tags.md").read_text()
        result = run_script(
            "add_tag.py", "meta", "Already exists.",
            "--adr-dir", "docs/adr", cwd=adr_repo,
        )
        assert result.returncode == 0
        assert (adr_dir / "_tags.md").read_text() == before
```

- [ ] **Step 2: Run test, expect failure**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestAddTag -v
```

Expected: failure.

- [ ] **Step 3: Implement `tools/adr/add_tag.py`**

```python
"""Insert a new tag into _tags.md at the correct alphabetical position."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

from adr_lib import parse_tags_file


_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TAG_LINE_RE = re.compile(r"^-\s*\*\*([a-z0-9-]+)\*\*")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="tag slug (lowercase kebab)")
    parser.add_argument("description", help="one-line description")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    if not _SLUG_RE.match(args.slug):
        print(f"error: slug {args.slug!r} must be lowercase kebab-case", file=sys.stderr)
        return 2

    tags_path = args.adr_dir / "_tags.md"
    existing = parse_tags_file(tags_path)
    if args.slug in existing:
        return 0  # idempotent no-op

    new_entry = f"- **{args.slug}** — {args.description}"
    lines = tags_path.read_text().splitlines()
    insert_at = len(lines)
    inserted = False
    for i, line in enumerate(lines):
        match = _TAG_LINE_RE.match(line)
        if match and args.slug < match.group(1):
            insert_at = i
            inserted = True
            break
    if not inserted:
        # Insert after the last tag line.
        last_tag_idx = -1
        for i, line in enumerate(lines):
            if _TAG_LINE_RE.match(line):
                last_tag_idx = i
        insert_at = last_tag_idx + 1 if last_tag_idx >= 0 else len(lines)

    lines.insert(insert_at, new_entry)
    tags_path.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
.venv/bin/pytest tools/adr/tests/test_skill_scripts.py::TestAddTag -v
```

Expected: green.

- [ ] **Step 5: Commit**

```bash
git add tools/adr/add_tag.py tools/adr/tests/test_skill_scripts.py
git commit -m "feat(adr): add_tag.py alphabetical insertion into _tags.md"
```

---

## Task 16: Write `docs/adr/_tags.md` (seed tags)

**Files:**
- Create: `docs/adr/_tags.md`

- [ ] **Step 1: Write `docs/adr/_tags.md`**

```markdown
# Allowed ADR Tags

Every tag used in an ADR's frontmatter MUST appear in this list. Before introducing a new tag, add it here (alphabetically) with a short description. The CI `adr-validate` job fails on any unknown tag.

- **documentation** — Decisions about docs, READMEs, comments, or written artifacts.
- **meta** — Decisions about the ADR process itself.
- **process** — Decisions about how work is done (workflow, conventions, ceremony).
```

- [ ] **Step 2: Verify `list_tags.py` reads it correctly**

```bash
.venv/bin/python tools/adr/list_tags.py
```

Expected output:
```
documentation	Decisions about docs, READMEs, comments, or written artifacts.
meta	Decisions about the ADR process itself.
process	Decisions about how work is done (workflow, conventions, ceremony).
```

- [ ] **Step 3: Commit**

```bash
git add docs/adr/_tags.md
git commit -m "docs(adr): seed _tags.md with documentation/meta/process"
```

---

## Task 17: Write `docs/adr/_template.md`

**Files:**
- Create: `docs/adr/_template.md`

Uses `{{...}}` placeholders that `new_adr.py` fills in. Optional sections are present with HTML-comment markers so authors can delete them.

- [ ] **Step 1: Write `docs/adr/_template.md`**

````markdown
---
id: "{{id}}"
name: {{name}}
description: TODO one-sentence summary.
status: Proposed
date-proposed: "{{date-proposed}}"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: []
---

# ADR {{id}}: TODO Title in Title Case

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | {{date-proposed}}                    |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | TODO Author Name                     |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | TODO                                 |

## Context and Problem Statement

TODO Describe the situation and the problem this ADR addresses.

<!-- optional: delete this section if it doesn't add value -->
## Decision Drivers

- TODO driver 1
- TODO driver 2

## Considered Options

- TODO Option A
- TODO Option B
- TODO "Do nothing"

## Decision Outcome

TODO State the chosen option and a short justification.

## Consequences

- Positive: TODO
- Negative: TODO

<!-- optional: delete this section if it doesn't add value -->
## Pros and Cons of the Options

### Option A

- Pros: TODO
- Cons: TODO

### Option B

- Pros: TODO
- Cons: TODO

<!-- optional: delete this section if it doesn't add value -->
## Links

- TODO related RFC, blog post, ticket, PR
````

- [ ] **Step 2: Verify `_template.md` is skipped by `enumerate_adrs`**

```bash
.venv/bin/python tools/adr/list_adrs.py
```

Expected: empty output (the template starts with `_` and must not be picked up as an ADR).

- [ ] **Step 3: Commit**

```bash
git add docs/adr/_template.md
git commit -m "docs(adr): add _template.md skeleton for new ADRs"
```

---

## Task 18: Write the first ADR

**Files:**
- Create: `docs/adr/000001-adr-process-and-structure.md`

This ADR codifies the spec. It bootstraps with `status: Accepted` (special case for the very first ADR; explained in its own body). All dates are 2026-05-24.

- [ ] **Step 1: Write `docs/adr/000001-adr-process-and-structure.md`**

````markdown
---
id: "000001"
name: adr-process-and-structure
description: Establishes the ADR process, file structure, required sections, and CI gates.
status: Accepted
date-proposed: "2026-05-24"
date-accepted: "2026-05-24"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [documentation, meta, process]
---

# ADR 000001: ADR Process and Structure

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Accepted                             |
| Date Proposed    | 2026-05-24                           |
| Date Accepted    | 2026-05-24                           |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | documentation, meta, process         |

## Context and Problem Statement

`rhystic-library-api` is a brand-new project. Significant technical decisions accumulate quickly in a project's first months — choices about libraries, schemas, deployment models, conventions, and trade-offs that future contributors (human and AI) need to understand to make consistent follow-on decisions. Without a deliberate record, the *why* behind those choices is lost to chat history and faulty memory within weeks.

We need a lightweight, durable Architecture Decision Record (ADR) process from day one — before the first non-trivial design choice — so the project's reasoning is captured as it happens rather than reconstructed later.

## Considered Options

- **No formal process; rely on commit messages and PR descriptions.** Cheap and zero-friction, but commit messages are rarely written for posterity and PR descriptions decay along with the PR UI.
- **Nygard-style minimal ADRs (Context / Decision / Consequences).** Three sections, very lean. Easy to write, but loses *alternatives considered*, which is the field most useful to future readers.
- **MADR-style rich ADRs** with explicit Considered Options, Decision Outcome, optional Decision Drivers / Pros-Cons / Links, plus a frontmatter mirror and a human header table. More structure; more friction per ADR; far better for audit and AI-assisted exploration.
- **Long-form architecture docs in a wiki.** Discoverable for humans but not version-controlled with the code, and substantially heavier per decision.

## Decision Outcome

We adopt the **MADR-style rich ADR** approach, with project-specific choices documented in this section.

### File layout

- All ADRs live in `docs/adr/`.
- Filename: `NNNNNN-kebab-slug.md` (6-digit zero-padded ID, no gaps, no reuse, starting at `000001`).
- Two companion files (underscore-prefixed to sort first and visually separate):
  - [`docs/adr/_template.md`](_template.md) — copy-paste skeleton for new ADRs.
  - [`docs/adr/_tags.md`](_tags.md) — alphabetical list of allowed tags.
- One decision per ADR — never bundle two independent concerns. Future supersession would otherwise be impossible to scope.

### Frontmatter (machine-readable)

Every ADR begins with a YAML frontmatter block:

```yaml
---
id: "NNNNNN"
name: kebab-slug
description: One-sentence summary.
status: Proposed | Accepted | Deprecated | Superseded
date-proposed: "YYYY-MM-DD"
date-accepted: "YYYY-MM-DD"  # or "" until accepted
date-invalidated: ""          # set when status flips to Deprecated/Superseded
supersedes: ["NNNNNN", ...]   # list of ADR IDs; [] when none
superseded-by: ["NNNNNN", ...]
tags: [tag1, tag2]            # every tag must appear in _tags.md
---
```

Dates are quoted ISO-8601 strings; the empty case is `""` so all tools parse them identically. ADR cross-references use **IDs, not filenames**, since IDs are immutable but slugs can in principle be renamed.

### Body structure

An H1 follows the frontmatter, then a human-readable key-value table mirroring the frontmatter, then MADR-style sections in fixed order:

| Section                          | Required? |
|----------------------------------|-----------|
| Context and Problem Statement    | Required  |
| Decision Drivers                 | Optional  |
| Considered Options               | Required  |
| Decision Outcome                 | Required  |
| Consequences                     | Required  |
| Pros and Cons of the Options     | Optional  |
| Links                            | Optional  |

The header table has eight rows (`Status`, `Date Proposed`, `Date Accepted`, `Date Invalidated`, `Authors`, `Supersedes`, `Superseded By`, `Tags`). Empty values render as em-dash (`—`). Authors are bare names, comma-separated. Dates are ISO 8601.

### Status lifecycle and mutability

- `Proposed` — written but not yet merged to `main`. Free to edit during PR review.
- `Accepted` — the ADR commit is on `main`. From this point the body is **immutable**.
- `Deprecated` — the decision no longer applies; nothing replaces it. Set `date-invalidated`.
- `Superseded` — replaced by one or more newer ADRs; populate `superseded-by` and `date-invalidated`.

After acceptance, the only legal changes are metadata (status flip, `date-invalidated`, `superseded-by`, and mirroring those in the header table). Any substantive change requires a new ADR that supersedes the old.

The PR that introduces a new ADR must flip `Proposed` → `Accepted` and populate `Date Accepted` before merge. CI enforces this via the merge gate (see below).

### Tags

Every tag in an ADR's `tags` list MUST appear in [`_tags.md`](_tags.md). To introduce a new tag, add it to `_tags.md` (alphabetically, with a one-line description) in the same change that uses it. The skill `creating-an-adr` ships a helper script `add_tag.py` that does this automatically.

### CI validation

Two CI jobs (see `.github/workflows/ci.yml`) gate every PR and every push to `main`:

- **`markdown-lint`** — standard Markdown linter (`markdownlint-cli2`) over `**/*.md`.
- **`adr-validate`** — custom Python validator at `tools/adr/validate.py`. Run locally via `python tools/adr/validate.py`; CI runs it with `--merge-gate` to enforce the status invariants. The validator checks:
  - **Numbering** — filenames match `NNNNNN-kebab.md`, IDs sequential with no gaps or duplicates, frontmatter `id`/`name` match the filename.
  - **Frontmatter schema** — all required fields present, types correct, status in allowed set, dates ISO-8601, referenced ADR IDs exist.
  - **Tag membership** — every tag is in `_tags.md`.
  - **Body structure** — H1 present, header table present with all eight rows, Authors non-empty, all four required sections present.
  - **Frontmatter ↔ header table consistency** — every paired field matches (with empty string ↔ em-dash equivalence for dates, list ↔ comma-joined equivalence for tags/supersedes).
  - **Merge gate** (only with `--merge-gate`) — status must be Accepted/Deprecated/Superseded; date-accepted required for any of those; date-invalidated required and on-or-after date-accepted for Deprecated/Superseded; date-invalidated must be empty for Proposed/Accepted; Superseded requires non-empty `superseded-by`.

### Claude skills

Three project-level skills under `.claude/skills/` provide Claude operational entry points for the ADR system. Each `SKILL.md` documents when to invoke and what scripts to call; the scripts live in `tools/adr/` and are written in Python:

- [`.claude/skills/searching-adrs/`](../../.claude/skills/searching-adrs/SKILL.md) — `list_adrs.py`, `find_adrs.py`, `show_adr.py`.
- [`.claude/skills/listing-adr-tags/`](../../.claude/skills/listing-adr-tags/SKILL.md) — `list_tags.py`, `tag_usage.py`.
- [`.claude/skills/creating-an-adr/`](../../.claude/skills/creating-an-adr/SKILL.md) — `new_adr.py`, `add_tag.py`.

Scripts read only frontmatter (never bodies), keeping output token-efficient even as the corpus grows.

### Bootstrap quirk for this ADR

This is the very first ADR. Per the lifecycle rule, "Accepted" means *committed to main*. The strict reading of that rule would block this ADR from ever being merged, since CI requires `Accepted` status to merge. We resolve the chicken-and-egg by giving this single bootstrap ADR `status: Accepted` from its introducing commit. Every subsequent ADR follows the normal flow: `Proposed` during development, flipped to `Accepted` immediately before merge.

## Consequences

- **Positive**
  - Every significant decision has a frozen, versioned record with rationale and considered alternatives.
  - Frontmatter makes ADRs scriptable; the skills + helper scripts give Claude precise, low-token discovery and authoring tools.
  - CI catches structural drift (missing sections, unknown tags, gap in numbering) before merge, removing review burden.
  - The one-decision-per-ADR rule keeps supersession clean and scoped.
- **Negative**
  - Each significant decision now requires writing an ADR — non-trivial friction for small calls. Authors must judge the bar (the skill `creating-an-adr` is the place to document that bar over time).
  - Two CI jobs add a small but non-zero PR latency.
  - The validator and skill scripts are project-owned code that must be maintained alongside the codebase proper.

## Links

- Design spec: [`docs/superpowers/specs/2026-05-24-adr-process-design.md`](../superpowers/specs/2026-05-24-adr-process-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-05-24-adr-process.md`](../superpowers/plans/2026-05-24-adr-process.md)
- MADR (Markdown Architecture Decision Records): <https://adr.github.io/madr/>
- Michael Nygard's original ADR post: <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
````

- [ ] **Step 2: Run the validator and skill scripts against the real artifacts**

```bash
.venv/bin/python tools/adr/validate.py --merge-gate
```

Expected: exit code 0, no output.

```bash
.venv/bin/python tools/adr/list_adrs.py
```

Expected: one line starting with `000001  Accepted  [documentation,meta,process]  Establishes the ADR process...`.

```bash
.venv/bin/python tools/adr/show_adr.py 000001
```

Expected: pretty-printed JSON with all frontmatter fields.

```bash
.venv/bin/python tools/adr/find_adrs.py --tag meta
```

Expected: the one ADR line printed.

```bash
.venv/bin/python tools/adr/tag_usage.py
```

Expected:
```
documentation	000001
meta	000001
process	000001
```

- [ ] **Step 3: Commit**

```bash
git add docs/adr/000001-adr-process-and-structure.md
git commit -m "docs(adr): write ADR 000001 codifying the ADR process"
```

---

## Task 19: Skill — `searching-adrs`

**Files:**
- Create: `.claude/skills/searching-adrs/SKILL.md`

- [ ] **Step 1: Write `.claude/skills/searching-adrs/SKILL.md`**

```markdown
---
name: searching-adrs
description: Use when looking up existing Architecture Decision Records by id, tag, status, or keyword. Use this BEFORE making a design choice that may already have a recorded decision.
---

# Searching ADRs

All ADRs live under `docs/adr/` as `NNNNNN-kebab-slug.md`. Prefer the scripts below over reading files directly — they parse only frontmatter, so they stay cheap as the corpus grows. The first ADR ([`000001-adr-process-and-structure.md`](../../../docs/adr/000001-adr-process-and-structure.md)) is the source of truth for the process.

Run scripts from the repo root.

## When to use

- Before proposing a design or implementation that touches an area likely to have prior decisions.
- When asked "why does this codebase do X?" — there may be an ADR explaining it.
- When triaging deprecated/superseded ADRs.

## Scripts

### Overview of all ADRs

```bash
python tools/adr/list_adrs.py
```

Prints one line per ADR sorted by ID: `<id>\t<status>\t[<tags>]\t<description>`. Use this as the entry point when scanning.

### Filtered lookup

```bash
python tools/adr/find_adrs.py [--tag TAG] [--status STATUS] [--search KEYWORD]
```

Filters AND together. `--search` does case-insensitive substring match against `name` and `description`. Useful examples:

- Find all process decisions: `--tag process`
- Find every still-in-force ADR: `--status Accepted`
- Find ADRs about logging: `--search logging`

### Read a single ADR's frontmatter

```bash
python tools/adr/show_adr.py <id>
```

Where `<id>` is the 6-digit ID (e.g. `000001`). Outputs JSON. Use this to inspect supersedes/superseded-by relationships, status, or full tag list. Read the file directly with the `Read` tool when you need the body.

## Falling back to direct reads

When you've identified the candidate ADR(s), read the full file with the `Read` tool to get context, decision, consequences, and links.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/searching-adrs/SKILL.md
git commit -m "feat(skill): searching-adrs skill"
```

---

## Task 20: Skill — `listing-adr-tags`

**Files:**
- Create: `.claude/skills/listing-adr-tags/SKILL.md`

- [ ] **Step 1: Write `.claude/skills/listing-adr-tags/SKILL.md`**

```markdown
---
name: listing-adr-tags
description: Use when picking tags for a new ADR or surveying which topics already have decisions recorded. Always check before assigning a tag — unknown tags fail CI.
---

# Listing ADR Tags

Allowed tags live in [`docs/adr/_tags.md`](../../../docs/adr/_tags.md). Every tag used in an ADR's frontmatter MUST appear there. Adding a tag that isn't in `_tags.md` fails the `adr-validate` CI job.

Run scripts from the repo root.

## When to use

- Before writing the `tags:` field on a new ADR.
- When deciding whether to introduce a new tag vs reuse an existing one.
- When surveying which areas of the system already have recorded decisions.

## Scripts

### List every allowed tag with its description

```bash
python tools/adr/list_tags.py
```

Output: `<tag>\t<description>`, one per line, alphabetical.

### See which ADRs use each tag

```bash
python tools/adr/tag_usage.py
```

Output: `<tag>\t<id1>,<id2>,...`, one per line, alphabetical. Tags with zero ADRs appear with an empty list — that's useful for spotting stale tags.

## Adding a new tag

If no existing tag fits, add a new one with the `creating-an-adr` skill's `add_tag.py` script (inserts alphabetically and idempotently). Then use it in your ADR's `tags:` field.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/listing-adr-tags/SKILL.md
git commit -m "feat(skill): listing-adr-tags skill"
```

---

## Task 21: Skill — `creating-an-adr`

**Files:**
- Create: `.claude/skills/creating-an-adr/SKILL.md`

- [ ] **Step 1: Write `.claude/skills/creating-an-adr/SKILL.md`**

```markdown
---
name: creating-an-adr
description: Use when authoring a new Architecture Decision Record. Walks through the full creation flow — scaffold, fill, validate, flip status, merge — and ensures the new ADR conforms to ADR 000001.
---

# Creating an ADR

All ADRs live under `docs/adr/`. The first ADR ([`000001-adr-process-and-structure.md`](../../../docs/adr/000001-adr-process-and-structure.md)) is the canonical source of truth — every rule below comes from there.

Run scripts from the repo root.

## When to use

- A non-trivial design choice that future contributors will need to understand.
- A change in conventions, workflow, tools, or constraints that affects how code is written.
- A reversal or refinement of an earlier decision (write a new ADR; supersede the old).

Not every change needs an ADR. If a future contributor would shrug at the choice, skip the ADR.

## End-to-end flow

1. **Pick (or add) tags.** Use the `listing-adr-tags` skill to see what's available. If you need a new tag, run:
   ```bash
   python tools/adr/add_tag.py <slug> "Short description."
   ```
2. **Scaffold the ADR.** Choose a kebab-slug that captures the decision:
   ```bash
   python tools/adr/new_adr.py <slug>
   ```
   This computes the next sequential ID, copies [`docs/adr/_template.md`](../../../docs/adr/_template.md) to `docs/adr/<id>-<slug>.md`, pre-fills `id`, `name`, and `date-proposed` (today), and prints the new path.
3. **Fill in the ADR.** Open the file. Required sections (NEVER delete):
   - `## Context and Problem Statement`
   - `## Considered Options`
   - `## Decision Outcome`
   - `## Consequences`

   Optional sections (delete if they don't add value):
   - `## Decision Drivers`
   - `## Pros and Cons of the Options`
   - `## Links`

   Also fill the header table: Authors, Tags, and update Status (still `Proposed` at this point).

4. **Keep frontmatter and table in sync.** The validator checks every paired field. Whenever you change a status, date, tag, or supersedes value in one, mirror it in the other.

5. **Validate locally** during iteration:
   ```bash
   python tools/adr/validate.py
   ```
   Drops the merge-gate check so `Proposed` doesn't fail. Fix every error before opening the PR.

6. **Flip to Accepted before merge.** Just before the PR merges, change:
   - Frontmatter: `status: Accepted`, `date-accepted: "YYYY-MM-DD"`.
   - Header table: `Status | Accepted`, `Date Accepted | YYYY-MM-DD`.

   Then run the merge-gate validator:
   ```bash
   python tools/adr/validate.py --merge-gate
   ```
   Must exit 0.

7. **Merge.** CI runs the merge-gate validator + markdown lint and gates the merge.

## Mutability after merge

Once an ADR is on `main`, the body is **immutable**. The only legal edits are metadata: flipping `status` to `Deprecated` or `Superseded`, populating `date-invalidated`, populating `superseded-by`. Mirror those in the header table.

To change a decision, write a new ADR that supersedes the old.

## Superseding an existing ADR

1. Scaffold a new ADR as above.
2. In its frontmatter, set `supersedes: ["<old-id>"]` and mirror in the table.
3. In a separate commit (or the same PR), edit the superseded ADR:
   - Frontmatter: `status: Superseded`, `date-invalidated: "<today>"`, `superseded-by: ["<new-id>"]`.
   - Header table: same three fields.
   - Body unchanged.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/creating-an-adr/SKILL.md
git commit -m "feat(skill): creating-an-adr skill"
```

---

## Task 22: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Overwrite `README.md`**

```markdown
# rhystic-library-api

API for the Rhystic Library.

## Architecture Decisions

Significant technical decisions are captured as Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/). Each ADR represents a single decision, is numbered sequentially (`NNNNNN-kebab-slug.md`), and is immutable once accepted — superseded decisions are replaced by newer ADRs rather than edited.

Start with [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md) to understand the process. Two companion files live alongside the ADRs:

- [`_template.md`](docs/adr/_template.md) — copy-paste skeleton for new ADRs.
- [`_tags.md`](docs/adr/_tags.md) — allowed tag list.

## Development

Set up the Python tooling used by ADR scripts and CI:

\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
\`\`\`

Run the ADR test suite:

\`\`\`bash
pytest
\`\`\`

Validate ADRs locally:

\`\`\`bash
python tools/adr/validate.py            # development mode
python tools/adr/validate.py --merge-gate  # CI mode
\`\`\`
```

(Note: the backslash-escaped fences above are an artifact of embedding in this plan; write actual triple-backtick fences in `README.md`.)

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: expand README with project description and ADR pointer"
```

---

## Task 23: Create `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write `CLAUDE.md`**

```markdown
# CLAUDE.md

Project-level guidance for Claude working in this repository.

## Architecture Decision Records

- **Where:** `docs/adr/`. Companion files: `_template.md` and `_tags.md`.
- **Source of truth:** [`docs/adr/000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md). Read this once when you need full detail on the ADR process, structure, status lifecycle, or immutability rules.
- **Skills (use these instead of grepping by hand):**
  - `.claude/skills/searching-adrs/` — when looking up existing decisions by id, tag, status, or keyword.
  - `.claude/skills/listing-adr-tags/` — when picking tags for a new ADR or surveying topic areas.
  - `.claude/skills/creating-an-adr/` — when authoring a new ADR (scaffolds, validates, walks the merge flow).

Each skill ships helper scripts under `tools/adr/` that parse only frontmatter — prefer them over reading whole files when the question can be answered from metadata.

## Python tooling

- Dev deps: `requirements-dev.txt` (pytest, pyyaml).
- Tests: `pytest` from repo root runs the ADR script tests.
- Validator: `python tools/adr/validate.py` (add `--merge-gate` to mirror CI).
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md pointing at ADR 000001 and the three skills"
```

---

## Task 24: Markdownlint config + GitHub Actions CI

**Files:**
- Create: `.markdownlint.jsonc`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write `.markdownlint.jsonc`**

```jsonc
{
  // Reasonable defaults; relax a few rules that fight ADR table layout.
  "default": true,
  "MD013": false,        // line-length: ADRs use prose paragraphs
  "MD024": { "siblings_only": true }, // duplicate headings OK across sections
  "MD033": false,        // allow inline HTML (template uses <!-- ... -->)
  "MD041": false         // first line can be frontmatter, not H1
}
```

- [ ] **Step 2: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  markdown-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Run markdownlint
        run: npx --yes markdownlint-cli2 "**/*.md" "#node_modules"

  adr-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Python deps
        run: pip install -r requirements-dev.txt
      - name: Run validator (merge gate)
        run: python tools/adr/validate.py --merge-gate
      - name: Run pytest
        run: pytest
```

- [ ] **Step 3: Run markdownlint locally to confirm clean output**

```bash
npx --yes markdownlint-cli2 "**/*.md" "#node_modules" "#.venv"
```

Expected: exit code 0, no warnings.

If warnings appear, fix the offending files and re-run. Common likely fix: trailing whitespace or missing newline at EOF.

- [ ] **Step 4: Run the validator end-to-end**

```bash
.venv/bin/python tools/adr/validate.py --merge-gate
```

Expected: exit code 0, no output.

- [ ] **Step 5: Commit**

```bash
git add .markdownlint.jsonc .github/workflows/ci.yml
git commit -m "ci: add markdownlint and adr-validate jobs"
```

---

## Task 25: Final verification

**Files:** (none modified)

- [ ] **Step 1: Run full test suite**

```bash
.venv/bin/pytest -v
```

Expected: all tests green.

- [ ] **Step 2: Run validator in both modes**

```bash
.venv/bin/python tools/adr/validate.py
.venv/bin/python tools/adr/validate.py --merge-gate
```

Expected: both exit 0 with no output.

- [ ] **Step 3: Run every skill script against the real first ADR**

```bash
.venv/bin/python tools/adr/list_adrs.py
.venv/bin/python tools/adr/find_adrs.py --tag meta
.venv/bin/python tools/adr/find_adrs.py --status Accepted
.venv/bin/python tools/adr/show_adr.py 000001
.venv/bin/python tools/adr/list_tags.py
.venv/bin/python tools/adr/tag_usage.py
```

Each should print sensible output and exit 0.

- [ ] **Step 4: Dry-run the scaffold script in a sandbox**

```bash
mkdir -p /tmp/adr-scaffold-test/docs/adr
cp docs/adr/_template.md /tmp/adr-scaffold-test/docs/adr/_template.md
cp docs/adr/_tags.md /tmp/adr-scaffold-test/docs/adr/_tags.md
(cd /tmp/adr-scaffold-test && PYTHONPATH=$PWD/../../$(pwd | xargs basename)/tools/adr python3 ${PWD}/../../$(pwd | xargs basename)/tools/adr/new_adr.py example-decision --adr-dir docs/adr 2>&1 || true)
```

(If the path gymnastics above bother you, just run `.venv/bin/python tools/adr/new_adr.py example-decision` from a scratch git worktree.)

Expected: prints the new file path; the file exists and is valid YAML.

Clean up afterwards:

```bash
rm -rf /tmp/adr-scaffold-test
```

- [ ] **Step 5: Run markdownlint over everything**

```bash
npx --yes markdownlint-cli2 "**/*.md" "#node_modules" "#.venv"
```

Expected: exit 0.

- [ ] **Step 6: Final sanity check — git status clean**

```bash
git status
```

Expected: `nothing to commit, working tree clean`. All work landed in commits during the tasks above.

- [ ] **Step 7: Push and let CI confirm green**

```bash
git push -u origin main  # or open a PR if working on a branch
```

Watch CI; both `markdown-lint` and `adr-validate` jobs must pass.

---

## Self-review notes (planner's own pass)

- Spec coverage: every section of the spec — location, frontmatter, body, dates, lifecycle, mutability, template, tags file, skills, CLAUDE.md, README, CI — has at least one task. ✓
- Type consistency: `validate_repo(adr_dir, *, merge_gate=False)` signature used identically across all validator extension tasks; helper names (`_check_numbering`, `_check_frontmatter_schema`, etc.) are unique and not redefined. ✓
- Placeholders: spot-checked — no "TBD" / "fill in details" / "similar to Task N" patterns. Every code step shows the actual code. The `_template.md` content uses `TODO` strings *intentionally* (they're literal template placeholders meant to be visible to ADR authors), not plan placeholders.
- One gotcha: `tools/adr/list_adrs.py` and similar use `python tools/adr/script.py` from repo root. Python's default behavior inserts the script's directory at `sys.path[0]`, so `from adr_lib import ...` works without further setup. Pytest finds them via `pythonpath = ["tools/adr"]` in `pyproject.toml`. Confirmed consistent across all script tasks.
