"""Unit tests for drift_lib."""

from __future__ import annotations

from textwrap import dedent

import pytest
from drift_lib import Finding, Sighting, normalize_name, parse_precommit_config


class TestDataClasses:
    """Tests for Sighting and Finding dataclasses."""

    def test_sighting_holds_package_file_location_version(self):
        """Sighting stores package, file, location, and version fields."""
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        assert s.package == "pyyaml"
        assert s.file == "requirements-dev.txt"
        assert s.location == "line 3"
        assert s.version == ">=6.0.3"

    def test_finding_holds_package_status_sightings_recommendation(self):
        """Finding stores package, status, sightings, and recommendation fields."""
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        f = Finding(package="pyyaml", status="drift", sightings=[s], recommendation="bump to >=6.0.3")
        assert f.package == "pyyaml"
        assert f.status == "drift"
        assert f.sightings == [s]
        assert f.recommendation == "bump to >=6.0.3"


class TestNormalizeName:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("PyYAML", "pyyaml"),
            ("pyyaml", "pyyaml"),
            ("markdownlint_cli2", "markdownlint-cli2"),
            ("Markdownlint-CLI2", "markdownlint-cli2"),
            ("actions/checkout", "actions/checkout"),
            ("ACTIONS/CHECKOUT", "actions/checkout"),
        ],
    )
    def test_lowercases_and_normalizes_separators(self, raw, expected):
        assert normalize_name(raw) == expected


class TestParsePrecommitConfig:
    def test_extracts_rev_pins_using_repo_basename(self, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(
            dedent("""
                repos:
                  - repo: https://github.com/astral-sh/ruff-pre-commit
                    rev: v0.15.14
                    hooks:
                      - id: ruff-check
            """)
        )
        sightings = parse_precommit_config(config, root=tmp_path)
        assert sightings == [
            Sighting(
                package="ruff-pre-commit",
                file=".pre-commit-config.yaml",
                location="repo",
                version="v0.15.14",
            ),
        ]

    def test_extracts_additional_dependencies(self, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(
            dedent("""
                repos:
                  - repo: local
                    hooks:
                      - id: adr-validate
                        name: ADR validator
                        entry: python tools/adr/validate.py
                        language: python
                        additional_dependencies: ["pyyaml>=6.0"]
            """)
        )
        sightings = parse_precommit_config(config, root=tmp_path)
        assert sightings == [
            Sighting(
                package="pyyaml",
                file=".pre-commit-config.yaml",
                location="hook=adr-validate",
                version=">=6.0",
            ),
        ]

    def test_local_repo_emits_no_rev_sighting(self, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(
            dedent("""
                repos:
                  - repo: local
                    hooks:
                      - id: foo
                        name: foo
                        entry: foo
                        language: system
            """)
        )
        assert parse_precommit_config(config, root=tmp_path) == []

    def test_hook_without_additional_deps_is_skipped(self, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(
            dedent("""
                repos:
                  - repo: https://github.com/pre-commit/pre-commit-hooks
                    rev: v6.0.0
                    hooks:
                      - id: end-of-file-fixer
            """)
        )
        sightings = parse_precommit_config(config, root=tmp_path)
        # Only the rev sighting — no additional_dependencies entries.
        assert len(sightings) == 1
        assert sightings[0].package == "pre-commit-hooks"
