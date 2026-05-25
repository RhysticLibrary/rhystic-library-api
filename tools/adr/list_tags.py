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
