"""Presentation helpers shared by skill CLI scripts.

Kept separate from ``adr_lib`` so the parsing library stays focused on input
handling and doesn't grow output-formatting responsibilities.
"""
from __future__ import annotations

from typing import Any


def summary_line(fm: dict[str, Any]) -> str:
    """Format one ADR's frontmatter as a single TSV row.

    Columns: ``<id>\\t<status>\\t[<tags>]\\t<description>``. Used by
    ``list_adrs.py`` and ``find_adrs.py`` so both produce identical output.
    """
    tags = ",".join(fm.get("tags", []) or [])
    return (
        f"{fm.get('id', '------')}\t"
        f"{fm.get('status', '?')}\t"
        f"[{tags}]\t"
        f"{fm.get('description', '')}"
    )
