"""Print the frontmatter of a single ADR as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


def main(argv: list[str] | None = None) -> int:
    """Print the frontmatter of the ADR with the given 6-digit ID as JSON.

    Returns 1 if no ADR matches the ID, 2 if the matched ADR's frontmatter
    is unparseable.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adr_id", help="6-digit ADR ID, e.g. 000001")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    for path in enumerate_adrs(args.adr_dir):
        if path.name.startswith(f"{args.adr_id}-"):
            try:
                fm = parse_frontmatter(path.read_text())
            except (ValueError, TypeError) as exc:
                print(f"error: ADR {args.adr_id} ({path.name}) is unparseable: {exc}", file=sys.stderr)
                return 2
            print(json.dumps(fm, indent=2, sort_keys=True))
            return 0
    print(f"ADR {args.adr_id} not found in {args.adr_dir}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
