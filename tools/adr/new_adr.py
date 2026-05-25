"""Scaffold a new ADR by copying _template.md and filling id/name/date."""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="kebab-case slug for the new ADR")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    if not _SLUG_RE.match(args.slug):
        print(f"error: slug {args.slug!r} must be lowercase kebab-case", file=sys.stderr)
        return 2

    template_path = args.adr_dir / "_template.md"
    if not template_path.is_file():
        print(f"error: template missing at {template_path}", file=sys.stderr)
        return 2

    existing = enumerate_adrs(args.adr_dir)
    next_id = 1
    if existing:
        last_fm = parse_frontmatter(existing[-1].read_text())
        next_id = int(str(last_fm["id"])) + 1
    new_id = f"{next_id:06d}"

    today = date.today().isoformat()
    template = template_path.read_text()
    filled = (
        template
        .replace("{{id}}", new_id)
        .replace("{{name}}", args.slug)
        .replace("{{date-proposed}}", today)
    )

    out_path = args.adr_dir / f"{new_id}-{args.slug}.md"
    if out_path.exists():
        print(f"error: {out_path} already exists", file=sys.stderr)
        return 2
    out_path.write_text(filled)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
