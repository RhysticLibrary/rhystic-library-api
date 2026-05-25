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
