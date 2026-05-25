"""Pure-function library for cross-file dependency drift detection."""

from __future__ import annotations

from dataclasses import dataclass


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
