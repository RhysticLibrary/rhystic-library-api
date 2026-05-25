"""List every ADR with id, status, tags, description."""
from __future__ import annotations
import argparse
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    args = parser.parse_args(argv)
    for path in enumerate_adrs(args.adr_dir):
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            print(f"{path.name}\tINVALID\t[]\t<unparseable>")
            continue
        tags = ",".join(fm.get("tags", []) or [])
        print(f"{fm.get('id', '------')}\t{fm.get('status', '?')}\t[{tags}]\t{fm.get('description', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
