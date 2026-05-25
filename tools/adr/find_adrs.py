"""Filter ADRs by tag, status, and/or keyword (filters AND together)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from adr_lib import enumerate_adrs, iter_frontmatters
from cli_format import summary_line


def _matches(
    fm: dict[str, Any],
    *,
    tag: str | None,
    status: str | None,
    search: str | None,
) -> bool:
    if tag and tag not in (fm.get("tags") or []):
        return False
    if status and fm.get("status") != status:
        return False
    if search:
        haystack = f"{fm.get('name', '')} {fm.get('description', '')}".lower()
        if search.lower() not in haystack:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    """Print ADRs matching every supplied filter, one TSV row per ADR."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    parser.add_argument("--tag", help="Restrict to ADRs containing this tag.")
    parser.add_argument("--status", help="Restrict to ADRs with this status.")
    parser.add_argument("--search", help="Substring match against name and description.")
    args = parser.parse_args(argv)

    for _path, fm in iter_frontmatters(enumerate_adrs(args.adr_dir)):
        if _matches(fm, tag=args.tag, status=args.status, search=args.search):
            print(summary_line(fm))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
