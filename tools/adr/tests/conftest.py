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
    defaults.update(overrides)
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
    rows = [
        "| Field            | Value                                |",
        "|------------------|--------------------------------------|",
    ]
    for key in [
        "Status",
        "Date Proposed",
        "Date Accepted",
        "Date Invalidated",
        "Authors",
        "Supersedes",
        "Superseded By",
        "Tags",
    ]:
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
    (adr_dir / "_tags.md").write_text(
        dedent("""
        # Allowed ADR Tags

        - **documentation** — Decisions about docs.
        - **meta** — Decisions about the ADR process itself.
        - **process** — Decisions about how work is done.
        """).lstrip()
    )
    return tmp_path
