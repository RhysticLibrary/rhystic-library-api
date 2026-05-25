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
