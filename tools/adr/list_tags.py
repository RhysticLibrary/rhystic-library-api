"""List every allowed ADR tag and its description."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from adr_lib import parse_tags_file


def main(argv: list[str] | None = None) -> int:
    r"""Print every allowed tag from ``_tags.md`` as ``<tag>\t<description>``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)
    tags_path = args.adr_dir / "_tags.md"
    if not tags_path.is_file():
        print(f"error: _tags.md missing at {tags_path}", file=sys.stderr)
        return 2
    tags = parse_tags_file(tags_path)
    for tag in sorted(tags):
        print(f"{tag}\t{tags[tag]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
