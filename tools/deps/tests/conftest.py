"""Shared fixtures for dep-drift tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixture_repo():
    """Return a callable that resolves a fixture-tree path by name."""

    def _resolve(name: str) -> Path:
        path = FIXTURES_DIR / name
        if not path.is_dir():
            raise FileNotFoundError(f"fixture tree not found: {path}")
        return path

    return _resolve
