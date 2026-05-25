"""Shared helpers for ADR scripts."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_ADR_FILENAME_RE = re.compile(r"^(\d{6})-[a-z0-9-]+\.md$")
_TAG_LINE_RE = re.compile(r"^-\s*\*\*(?P<tag>[a-z0-9-]+)\*\*\s*[—–-]\s*(?P<desc>.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\|\s*(?P<key>[^|]+?)\s*\|\s*(?P<value>[^|]+?)\s*\|\s*$")


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the YAML frontmatter block at the start of `text`."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("no frontmatter block at start of document")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"malformed YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def enumerate_adrs(adr_dir: Path) -> list[Path]:
    """Return ADR file paths sorted by 6-digit ID."""
    if not adr_dir.is_dir():
        return []
    matches = []
    for path in adr_dir.iterdir():
        if path.name.startswith("_"):
            continue
        if _ADR_FILENAME_RE.match(path.name):
            matches.append(path)
    return sorted(matches, key=lambda p: p.name)


def parse_tags_file(tags_path: Path) -> dict[str, str]:
    """Return {tag-slug: description} parsed from a _tags.md file."""
    tags: dict[str, str] = {}
    for line in tags_path.read_text().splitlines():
        match = _TAG_LINE_RE.match(line)
        if match:
            tags[match.group("tag")] = match.group("desc")
    return tags


def parse_header_table(text: str) -> dict[str, str]:
    """Return {field: value} parsed from the key-value header table."""
    rows: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.startswith("|") and "Field" in line and "Value" in line:
            in_table = True
            continue
        if in_table and re.match(r"^\|[-:\s|]+\|$", line):
            continue
        if in_table:
            match = _TABLE_ROW_RE.match(line)
            if match:
                rows[match.group("key")] = match.group("value")
            else:
                break
    if not rows:
        raise ValueError("could not locate header table")
    return rows
