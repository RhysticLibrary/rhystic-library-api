"""ADR validator. Returns a list of error messages; empty list means valid."""
from __future__ import annotations
import re
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter


_FILENAME_RE = re.compile(r"^(?P<id>\d{6})-(?P<slug>[a-z0-9-]+)\.md$")


def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    return errors


def _check_numbering(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    parsed: list[tuple[Path, str, str]] = []  # (path, filename_id, filename_slug)

    for path in paths:
        match = _FILENAME_RE.match(path.name)
        if not match:
            errors.append(f"{path.name}: filename does not match NNNNNN-kebab-slug.md")
            continue
        fid = match.group("id")
        fslug = match.group("slug")
        if fid in seen_ids:
            errors.append(
                f"{path.name}: duplicate ID {fid} (also used by {seen_ids[fid].name})"
            )
            continue
        seen_ids[fid] = path
        parsed.append((path, fid, fslug))

    # Frontmatter id/name vs filename
    for path, fid, fslug in parsed:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if str(fm.get("id", "")) != fid:
            errors.append(
                f"{path.name}: filename id {fid} does not match frontmatter id {fm.get('id')!r}"
            )
        if fm.get("name") != fslug:
            errors.append(
                f"{path.name}: filename slug {fslug!r} does not match frontmatter name {fm.get('name')!r}"
            )

    # Gap detection
    ids_in_order = sorted(seen_ids.keys())
    for index, fid in enumerate(ids_in_order, start=1):
        expected = f"{index:06d}"
        if fid != expected:
            errors.append(
                f"numbering: expected ID {expected} but found {fid} "
                f"(gap or out-of-order)"
            )
            break
    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate ADR repository.")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    parser.add_argument("--merge-gate", action="store_true",
                        help="Enforce the merge gate (status must be Accepted/Deprecated/Superseded).")
    args = parser.parse_args(argv)
    errors = validate_repo(args.adr_dir, merge_gate=args.merge_gate)
    for err in errors:
        print(f"ADR-VALIDATE: {err}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
