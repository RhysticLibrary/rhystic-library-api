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
