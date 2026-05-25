"""List every ADR with id, status, tags, description."""

from __future__ import annotations

import argparse
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter
from cli_format import summary_line


def main(argv: list[str] | None = None) -> int:
    """Print every ADR as a TSV row sorted by ID.

    Files whose frontmatter is missing, malformed, or non-mapping are
    surfaced as an ``INVALID`` row rather than silently skipped.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)
    for path in enumerate_adrs(args.adr_dir):
        try:
            fm = parse_frontmatter(path.read_text())
        except (ValueError, TypeError):
            print(f"{path.name}\tINVALID\t[]\t<unparseable>")
            continue
        print(summary_line(fm))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
