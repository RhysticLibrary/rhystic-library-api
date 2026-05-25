"""For each tag, list ADRs (by id) that use it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from adr_lib import enumerate_adrs, iter_frontmatters, parse_tags_file


def main(argv: list[str] | None = None) -> int:
    r"""Print ``<tag>\t<id1,id2,...>`` for every tag declared in ``_tags.md``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)

    tags_path = args.adr_dir / "_tags.md"
    if not tags_path.is_file():
        print(f"error: _tags.md missing at {tags_path}", file=sys.stderr)
        return 2
    tags = parse_tags_file(tags_path)
    usage: dict[str, list[str]] = {tag: [] for tag in tags}
    for _path, fm in iter_frontmatters(enumerate_adrs(args.adr_dir)):
        adr_id = str(fm.get("id", "")).strip()
        if not adr_id:
            continue
        for tag in fm.get("tags") or []:
            if tag in usage:
                usage[tag].append(adr_id)
    for tag in sorted(usage):
        print(f"{tag}\t{','.join(usage[tag])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
