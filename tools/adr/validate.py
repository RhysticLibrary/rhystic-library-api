"""ADR validator. Returns a list of error messages; empty list means valid."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from adr_lib import (
    ADR_FILENAME_RE,
    enumerate_adrs,
    iter_frontmatters,
    parse_frontmatter,
    parse_header_table,
    parse_tags_file,
)

_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
_ALLOWED_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}
_REQUIRED_FIELDS = (
    "id", "name", "description", "status",
    "date-proposed", "date-accepted", "date-invalidated",
    "supersedes", "superseded-by", "tags",
)
_REQUIRED_SECTIONS = (
    "Context and Problem Statement",
    "Considered Options",
    "Decision Outcome",
    "Consequences",
)
_REQUIRED_TABLE_FIELDS = (
    "Status", "Date Proposed", "Date Accepted", "Date Invalidated",
    "Authors", "Supersedes", "Superseded By", "Tags",
)
_ID_REF_RE = re.compile(r"^\d{6}$")


# --- Small shared helpers ---------------------------------------------------

def _body_after_frontmatter(text: str) -> str:
    match = _FRONTMATTER_BLOCK_RE.match(text)
    return text[match.end():] if match else text


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _normalize_list(value: object) -> str:
    """Normalize a list-valued frontmatter field to its table representation."""
    if not value:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _existing_ids(paths: list[Path]) -> set[str]:
    """Return the set of valid 6-digit IDs derived from the path filenames."""
    return {
        match.group("id")
        for path in paths
        if (match := ADR_FILENAME_RE.match(path.name)) is not None
    }


# --- Numbering check -------------------------------------------------------

def _check_numbering(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    parsed: list[tuple[Path, str, str]] = []  # (path, filename_id, filename_slug)

    for path in paths:
        match = ADR_FILENAME_RE.match(path.name)
        if not match:
            errors.append(f"{path.name}: filename does not match NNNNNN-kebab-slug.md")
            continue
        fid, fslug = match.group("id"), match.group("slug")
        if fid in seen_ids:
            errors.append(
                f"{path.name}: duplicate ID {fid} (also used by {seen_ids[fid].name})"
            )
            continue
        seen_ids[fid] = path
        parsed.append((path, fid, fslug))

    errors.extend(_check_filename_matches_frontmatter(parsed))
    errors.extend(_check_no_id_gaps(sorted(seen_ids)))
    return errors


def _check_filename_matches_frontmatter(parsed: list[tuple[Path, str, str]]) -> list[str]:
    errors: list[str] = []
    for path, fid, fslug in parsed:
        try:
            fm = parse_frontmatter(path.read_text())
        except (ValueError, TypeError) as exc:
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
    return errors


def _check_no_id_gaps(ids_in_order: list[str]) -> list[str]:
    for index, fid in enumerate(ids_in_order, start=1):
        expected = f"{index:06d}"
        if fid != expected:
            return [f"numbering: expected ID {expected} but found {fid} (gap or out-of-order)"]
    return []


# --- Frontmatter schema check ----------------------------------------------

def _check_frontmatter_schema(paths: list[Path]) -> list[str]:
    """Orchestrator: per ADR, run each schema sub-check and collect errors."""
    errors: list[str] = []
    existing = _existing_ids(paths)
    for path, fm in iter_frontmatters(paths):
        errors.extend(_check_required_fields_present(path, fm))
        errors.extend(_check_status_allowed(path, fm))
        errors.extend(_check_description_non_empty(path, fm))
        errors.extend(_check_date_fields(path, fm))
        errors.extend(_check_tags_non_empty(path, fm))
        errors.extend(_check_id_references_exist(path, fm, existing))
    return errors


def _check_required_fields_present(path: Path, fm: dict[str, Any]) -> list[str]:
    return [
        f"{path.name}: missing required frontmatter field '{field}'"
        for field in _REQUIRED_FIELDS if field not in fm
    ]


def _check_status_allowed(path: Path, fm: dict[str, Any]) -> list[str]:
    if fm.get("status") in _ALLOWED_STATUSES:
        return []
    return [
        f"{path.name}: status {fm.get('status')!r} is unknown; "
        f"must be one of {sorted(_ALLOWED_STATUSES)}"
    ]


def _check_description_non_empty(path: Path, fm: dict[str, Any]) -> list[str]:
    desc = fm.get("description")
    if isinstance(desc, str) and desc.strip():
        return []
    return [f"{path.name}: description must be a non-empty string"]


def _check_date_fields(path: Path, fm: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _is_iso_date(fm.get("date-proposed")):
        errors.append(
            f"{path.name}: date-proposed must be ISO-8601 (YYYY-MM-DD), "
            f"got {fm.get('date-proposed')!r}"
        )
    for date_field in ("date-accepted", "date-invalidated"):
        value = fm.get(date_field)
        if value not in ("", None) and not _is_iso_date(value):
            errors.append(
                f"{path.name}: {date_field} must be ISO-8601 or empty, got {value!r}"
            )
    return errors


def _check_tags_non_empty(path: Path, fm: dict[str, Any]) -> list[str]:
    tags = fm.get("tags")
    if isinstance(tags, list) and tags:
        return []
    return [f"{path.name}: tags must be a non-empty list"]


def _check_id_references_exist(
    path: Path, fm: dict[str, Any], existing: set[str],
) -> list[str]:
    errors: list[str] = []
    for ref_field in ("supersedes", "superseded-by"):
        refs = fm.get(ref_field, [])
        if not isinstance(refs, list):
            errors.append(f"{path.name}: {ref_field} must be a list")
            continue
        for ref in refs:
            if not (isinstance(ref, str) and _ID_REF_RE.fullmatch(ref)):
                errors.append(
                    f"{path.name}: {ref_field} entry {ref!r} must be a 6-digit ID string"
                )
                continue
            if ref not in existing:
                errors.append(f"{path.name}: {ref_field} references unknown ADR {ref}")
    return errors


# --- Tag membership check --------------------------------------------------

def _check_tag_membership(adr_dir: Path, paths: list[Path]) -> list[str]:
    tags_path = adr_dir / "_tags.md"
    if not tags_path.is_file():
        return [f"_tags.md missing at {tags_path}"]
    allowed = set(parse_tags_file(tags_path).keys())
    errors: list[str] = []
    for path, fm in iter_frontmatters(paths):
        for tag in fm.get("tags") or []:
            if tag not in allowed:
                errors.append(
                    f"{path.name}: unknown tag {tag!r} (add it to _tags.md before use)"
                )
    return errors


# --- Body structure check --------------------------------------------------

def _check_body_structure(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        body = _body_after_frontmatter(text).lstrip("\n")
        errors.extend(_check_h1_present(path, body))
        errors.extend(_check_header_table(path, body))
        errors.extend(_check_required_sections(path, body))
    return errors


def _check_h1_present(path: Path, body: str) -> list[str]:
    first_meaningful = next((line for line in body.splitlines() if line.strip()), "")
    if first_meaningful.startswith("# "):
        return []
    return [f"{path.name}: expected H1 immediately after frontmatter"]


def _check_header_table(path: Path, body: str) -> list[str]:
    try:
        table = parse_header_table(body)
    except ValueError as exc:
        return [f"{path.name}: {exc}"]
    errors = [
        f"{path.name}: header table missing row '{field}'"
        for field in _REQUIRED_TABLE_FIELDS if field not in table
    ]
    if table.get("Authors", "").strip() in ("", "—"):
        errors.append(f"{path.name}: Authors must be non-empty")
    return errors


def _check_required_sections(path: Path, body: str) -> list[str]:
    errors: list[str] = []
    for section in _REQUIRED_SECTIONS:
        pattern = re.compile(rf"^## {re.escape(section)}\s*$", re.MULTILINE)
        if not pattern.search(body):
            errors.append(f"{path.name}: missing required section '## {section}'")
    return errors


# --- Frontmatter ↔ table consistency check ---------------------------------

# (frontmatter_field, table_row_label, kind)
# kind: "scalar" — direct stringification; "date" — empty ↔ em-dash;
#       "list" — list ↔ comma-joined, empty list ↔ em-dash.
_CONSISTENCY_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("status", "Status", "scalar"),
    ("date-proposed", "Date Proposed", "scalar"),
    ("date-accepted", "Date Accepted", "date"),
    ("date-invalidated", "Date Invalidated", "date"),
    ("tags", "Tags", "list"),
    ("supersedes", "Supersedes", "list"),
    ("superseded-by", "Superseded By", "list"),
)


def _expected_table_value(fm_value: object, kind: str) -> str:
    if kind == "date":
        return str(fm_value) if fm_value else "—"
    if kind == "list":
        return _normalize_list(fm_value)
    return str(fm_value)


def _check_consistency(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text()
        try:
            fm = parse_frontmatter(text)
            table = parse_header_table(_body_after_frontmatter(text))
        except (ValueError, TypeError):
            continue
        for fm_field, table_label, kind in _CONSISTENCY_PAIRS:
            fm_value = fm.get(fm_field)
            table_value = table.get(table_label, "").strip()
            expected = _expected_table_value(fm_value, kind)
            if expected != table_value:
                errors.append(
                    f"{path.name}: {table_label} mismatch — "
                    f"frontmatter {fm_value!r} ↔ table {table_value!r}"
                )
    return errors


# --- Merge gate check ------------------------------------------------------

def _check_merge_gate(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path, fm in iter_frontmatters(paths):
        errors.extend(_check_status_for_merge(path, fm))
    return errors


def _check_status_for_merge(path: Path, fm: dict[str, Any]) -> list[str]:
    status = fm.get("status")
    date_accepted = fm.get("date-accepted") or ""
    date_invalidated = fm.get("date-invalidated") or ""
    superseded_by = fm.get("superseded-by") or []
    errors: list[str] = []

    if status == "Proposed":
        errors.append(f"{path.name}: merge gate — status 'Proposed' blocks merge")

    if status in {"Accepted", "Deprecated", "Superseded"} and not _is_iso_date(date_accepted):
        errors.append(
            f"{path.name}: status {status!r} requires date-accepted to be a valid date"
        )

    if status in {"Deprecated", "Superseded"}:
        if not _is_iso_date(date_invalidated):
            errors.append(
                f"{path.name}: status {status!r} requires date-invalidated to be a valid date"
            )
        elif _is_iso_date(date_accepted) and date_invalidated < date_accepted:
            errors.append(
                f"{path.name}: date-invalidated ({date_invalidated}) "
                f"must be on or after date-accepted ({date_accepted})"
            )

    if status in {"Proposed", "Accepted"} and date_invalidated:
        errors.append(
            f"{path.name}: status {status!r} requires date-invalidated to be empty"
        )

    if status == "Superseded" and not superseded_by:
        errors.append(
            f"{path.name}: status 'Superseded' requires non-empty superseded-by"
        )

    return errors


# --- Orchestrator + CLI ----------------------------------------------------

def validate_repo(adr_dir: Path, *, merge_gate: bool = False) -> list[str]:
    errors: list[str] = []
    paths = enumerate_adrs(adr_dir)
    errors.extend(_check_numbering(paths))
    errors.extend(_check_frontmatter_schema(paths))
    errors.extend(_check_tag_membership(adr_dir, paths))
    errors.extend(_check_body_structure(paths))
    errors.extend(_check_consistency(paths))
    if merge_gate:
        errors.extend(_check_merge_gate(paths))
    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate ADR repository.")
    parser.add_argument("--adr-dir", type=Path, default=Path("docs/adr"))
    parser.add_argument(
        "--merge-gate", action="store_true",
        help="Enforce the merge gate (status must be Accepted/Deprecated/Superseded).",
    )
    args = parser.parse_args(argv)
    errors = validate_repo(args.adr_dir, merge_gate=args.merge_gate)
    for err in errors:
        print(f"ADR-VALIDATE: {err}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
