"""ADR validator. Returns a list of error messages; empty list means valid."""
from __future__ import annotations
import re
from datetime import date
from pathlib import Path

from adr_lib import enumerate_adrs, parse_frontmatter, parse_tags_file, parse_header_table


_FILENAME_RE = re.compile(r"^(?P<id>\d{6})-(?P<slug>[a-z0-9-]+)\.md$")
_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
_ALLOWED_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}
_REQUIRED_FIELDS = [
    "id", "name", "description", "status",
    "date-proposed", "date-accepted", "date-invalidated",
    "supersedes", "superseded-by", "tags",
]
_REQUIRED_SECTIONS = [
    "Context and Problem Statement",
    "Considered Options",
    "Decision Outcome",
    "Consequences",
]
_REQUIRED_TABLE_FIELDS = [
    "Status", "Date Proposed", "Date Accepted", "Date Invalidated",
    "Authors", "Supersedes", "Superseded By", "Tags",
]


def _body_after_frontmatter(text: str) -> str:
    match = _FRONTMATTER_BLOCK_RE.match(text)
    return text[match.end():] if match else text


def _normalize_list(value: object) -> str:
    """Normalize a list-valued frontmatter field to its table representation."""
    if not value:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _normalize_table_list(value: str) -> str:
    return value.strip()


def _check_consistency(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        try:
            fm = parse_frontmatter(text)
            table = parse_header_table(_body_after_frontmatter(text))
        except ValueError:
            continue

        pairs: list[tuple[str, object, str]] = [
            ("Status", fm.get("status"), "Status"),
            ("Date Proposed", fm.get("date-proposed"), "Date Proposed"),
            ("Date Accepted", fm.get("date-accepted"), "Date Accepted"),
            ("Date Invalidated", fm.get("date-invalidated"), "Date Invalidated"),
            ("Tags", fm.get("tags"), "Tags"),
            ("Supersedes", fm.get("supersedes"), "Supersedes"),
            ("Superseded By", fm.get("superseded-by"), "Superseded By"),
        ]
        for label, fm_value, table_key in pairs:
            table_value = table.get(table_key, "").strip()
            if label in ("Date Accepted", "Date Invalidated"):
                expected_table = fm_value if fm_value else "—"
                if expected_table != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
            elif label in ("Tags", "Supersedes", "Superseded By"):
                expected_table = _normalize_list(fm_value)
                if expected_table != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
            else:
                if str(fm_value) != table_value:
                    errors.append(
                        f"{path.name}: {label} mismatch — frontmatter {fm_value!r} ↔ table {table_value!r}"
                    )
    return errors


def _check_body_structure(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        body = _body_after_frontmatter(text).lstrip("\n")

        # H1 check
        first_meaningful = next((l for l in body.splitlines() if l.strip()), "")
        if not first_meaningful.startswith("# "):
            errors.append(f"{path.name}: expected H1 immediately after frontmatter")
            continue

        # Header table presence + fields
        try:
            table = parse_header_table(body)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        for field in _REQUIRED_TABLE_FIELDS:
            if field not in table:
                errors.append(f"{path.name}: header table missing row '{field}'")
        if table.get("Authors", "").strip() in ("", "—"):
            errors.append(f"{path.name}: Authors must be non-empty")

        # Required level-2 sections
        for section in _REQUIRED_SECTIONS:
            pattern = re.compile(rf"^## {re.escape(section)}\s*$", re.MULTILINE)
            if not pattern.search(body):
                errors.append(f"{path.name}: missing required section '## {section}'")
    return errors


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _check_frontmatter_schema(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    existing_ids = {_FILENAME_RE.match(p.name).group("id") for p in paths
                    if _FILENAME_RE.match(p.name)}
    for path in paths:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue  # numbering check already reported this
        for field in _REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"{path.name}: missing required frontmatter field '{field}'")
        if fm.get("status") not in _ALLOWED_STATUSES:
            errors.append(
                f"{path.name}: status {fm.get('status')!r} is unknown; "
                f"must be one of {sorted(_ALLOWED_STATUSES)}"
            )
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"{path.name}: description must be a non-empty string")
        if not _is_iso_date(fm.get("date-proposed")):
            errors.append(f"{path.name}: date-proposed must be ISO-8601 (YYYY-MM-DD), got {fm.get('date-proposed')!r}")
        for date_field in ("date-accepted", "date-invalidated"):
            value = fm.get(date_field)
            if value not in ("", None) and not _is_iso_date(value):
                errors.append(f"{path.name}: {date_field} must be ISO-8601 or empty, got {value!r}")
        tags = fm.get("tags")
        if not isinstance(tags, list) or len(tags) == 0:
            errors.append(f"{path.name}: tags must be a non-empty list")
        for ref_field in ("supersedes", "superseded-by"):
            refs = fm.get(ref_field, [])
            if not isinstance(refs, list):
                errors.append(f"{path.name}: {ref_field} must be a list")
                continue
            for ref in refs:
                if not (isinstance(ref, str) and re.fullmatch(r"\d{6}", ref)):
                    errors.append(f"{path.name}: {ref_field} entry {ref!r} must be a 6-digit ID string")
                    continue
                if ref not in existing_ids:
                    errors.append(f"{path.name}: {ref_field} references unknown ADR {ref}")
    return errors


def _check_tag_membership(adr_dir: Path, paths: list[Path]) -> list[str]:
    errors: list[str] = []
    tags_path = adr_dir / "_tags.md"
    if not tags_path.is_file():
        errors.append(f"_tags.md missing at {tags_path}")
        return errors
    allowed = set(parse_tags_file(tags_path).keys())
    for path in paths:
        try:
            fm = parse_frontmatter(path.read_text())
        except ValueError:
            continue
        for tag in fm.get("tags", []) or []:
            if tag not in allowed:
                errors.append(
                    f"{path.name}: unknown tag {tag!r} (add it to _tags.md before use)"
                )
    return errors


def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    errors.extend(_check_body_structure(paths))
    errors.extend(_check_consistency(paths))
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
