"""Pure-function library for cross-file dependency drift detection."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml
from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version


@dataclass
class Sighting:
    """One occurrence of a package version pin in some file."""

    package: str
    file: str
    location: str
    version: str


@dataclass
class Finding:
    """The result of comparing all sightings of a single package."""

    package: str
    status: str  # "drift" | "in_sync"
    sightings: list[Sighting]
    recommendation: str


def normalize_name(name: str) -> str:
    """Lowercase + collapse underscores to hyphens for cross-file matching.

    Slashes are preserved so action references like ``actions/checkout`` keep
    their namespace.
    """
    return name.lower().replace("_", "-")


def parse_precommit_config(path: Path, root: Path) -> list[Sighting]:
    """Extract sightings from a ``.pre-commit-config.yaml`` file.

    Returns one sighting per ``rev:`` (using the repo URL's last segment as the
    package name) plus one per entry in any hook's ``additional_dependencies``.
    """
    with path.open() as fh:
        data = yaml.safe_load(fh)

    rel = str(path.relative_to(root))
    sightings: list[Sighting] = []

    for repo in (data or {}).get("repos", []) or []:
        repo_url = repo.get("repo", "")
        rev = repo.get("rev")
        if repo_url and repo_url != "local" and rev:
            basename = repo_url.rstrip("/").rsplit("/", 1)[-1]
            sightings.append(
                Sighting(
                    package=normalize_name(basename),
                    file=rel,
                    location="repo",
                    version=str(rev),
                )
            )
        for hook in repo.get("hooks", []) or []:
            hook_id = hook.get("id", "?")
            for dep in hook.get("additional_dependencies", []) or []:
                try:
                    req = Requirement(dep)
                except InvalidRequirement:
                    continue
                sightings.append(
                    Sighting(
                        package=normalize_name(req.name),
                        file=rel,
                        location=f"hook={hook_id}",
                        version=str(req.specifier) or "",
                    )
                )
    return sightings


_INLINE_VERSION_RE = re.compile(r"\b([a-zA-Z][\w\-]*(?:/[a-zA-Z][\w\-]*)?)@(v?\d+(?:\.\d+)*)\b")


def _walk(node):
    """Yield every dict in a nested YAML structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def parse_workflow(path: Path, root: Path) -> list[Sighting]:
    """Extract sightings from a GitHub Actions workflow YAML file."""
    with path.open() as fh:
        data = yaml.safe_load(fh)

    rel = str(path.relative_to(root))
    sightings: list[Sighting] = []

    for node in _walk(data):
        uses_val = node.get("uses")
        if isinstance(uses_val, str) and "@" in uses_val:
            ref, version = uses_val.split("@", 1)
            if ref and version:
                sightings.append(
                    Sighting(
                        package=normalize_name(ref),
                        file=rel,
                        location="uses",
                        version=version,
                    )
                )
        run_val = node.get("run")
        if isinstance(run_val, str):
            for match in _INLINE_VERSION_RE.finditer(run_val):
                ref, version = match.group(1), match.group(2)
                sightings.append(
                    Sighting(
                        package=normalize_name(ref),
                        file=rel,
                        location="run",
                        version=version,
                    )
                )

    return sightings


def _strip_to_version(raw: str) -> Version | None:
    """Return a :class:`Version` from a raw spec string, or ``None``.

    Handles leading specifier operators (``>=``, ``==``, ``~=``, etc.) and a
    leading ``v`` (as used by GitHub release tags).
    """
    stripped = raw.lstrip("<>=!~").strip()
    if stripped.startswith("v"):
        stripped = stripped[1:]
    if not stripped:
        return None
    try:
        return Version(stripped)
    except InvalidVersion:
        return None


def analyze_sightings(sightings: list[Sighting]) -> list[Finding]:
    """Group sightings by package and emit one Finding per cross-referenced package."""
    groups: dict[str, list[Sighting]] = defaultdict(list)
    for s in sightings:
        groups[s.package].append(s)

    findings: list[Finding] = []
    for package, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        versions = {s.version for s in group}
        if len(versions) == 1:
            findings.append(
                Finding(
                    package=package,
                    status="in_sync",
                    sightings=list(group),
                    recommendation="in sync (informational)",
                )
            )
            continue

        # Drift — find highest parseable version among sightings.
        parsed = [(s, _strip_to_version(s.version)) for s in group]
        parseable = [(s, v) for s, v in parsed if v is not None]
        if not parseable:
            # All unparseable — report as drift with raw strings.
            recommendation = f"bump to one of: {sorted(versions)} (no parseable versions)"
            findings.append(
                Finding(package=package, status="drift", sightings=list(group), recommendation=recommendation)
            )
            continue

        highest_sighting, highest_version = max(parseable, key=lambda pair: pair[1])
        lagging = [s for s, v in parsed if v != highest_version]
        if len(lagging) == 1:
            s = lagging[0]
            recommendation = f"bump {s.file} ({s.location}) to {highest_sighting.version}"
        else:
            laggers = ", ".join(f"{s.file}:{s.location}" for s in lagging)
            recommendation = f"bump to {highest_sighting.version} (lagging: {laggers})"

        findings.append(Finding(package=package, status="drift", sightings=list(group), recommendation=recommendation))

    return findings


def parse_requirements(path: Path, root: Path) -> list[Sighting]:
    """Extract sightings from a pip ``requirements.txt``-style file."""
    rel = str(path.relative_to(root))
    sightings: list[Sighting] = []
    for lineno, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            req = Requirement(line)
        except InvalidRequirement:
            continue
        sightings.append(
            Sighting(
                package=normalize_name(req.name),
                file=rel,
                location=f"line {lineno}",
                version=str(req.specifier),
            )
        )
    return sightings
