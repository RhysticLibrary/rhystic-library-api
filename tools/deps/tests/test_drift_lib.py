"""Unit tests for drift_lib."""

from __future__ import annotations

from textwrap import dedent

import pytest
from drift_lib import Finding, Sighting, normalize_name, parse_precommit_config, parse_requirements, parse_workflow


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


class TestParseRequirements:
    def test_extracts_pkg_and_specifier_with_line_number(self, tmp_path):
        reqs = tmp_path / "requirements-dev.txt"
        reqs.write_text("pytest>=9.0.3\npyyaml>=6.0.3\n")
        sightings = parse_requirements(reqs, root=tmp_path)
        assert sightings == [
            Sighting(package="pytest", file="requirements-dev.txt", location="line 1", version=">=9.0.3"),
            Sighting(package="pyyaml", file="requirements-dev.txt", location="line 2", version=">=6.0.3"),
        ]

    def test_skips_comments_and_blanks(self, tmp_path):
        reqs = tmp_path / "requirements-dev.txt"
        reqs.write_text("# top comment\n\npytest>=9.0.3\n  # indented\n")
        sightings = parse_requirements(reqs, root=tmp_path)
        assert len(sightings) == 1
        assert sightings[0].package == "pytest"
        assert sightings[0].location == "line 3"

    def test_unpinned_entry_yields_empty_version(self, tmp_path):
        reqs = tmp_path / "requirements-dev.txt"
        reqs.write_text("ruff\n")
        sightings = parse_requirements(reqs, root=tmp_path)
        assert sightings == [
            Sighting(package="ruff", file="requirements-dev.txt", location="line 1", version=""),
        ]


class TestParseWorkflow:
    def test_extracts_uses_action_pins(self, tmp_path):
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text(
            dedent("""
                jobs:
                  build:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v6
                      - uses: actions/setup-python@v6
            """)
        )
        sightings = parse_workflow(wf, root=tmp_path)
        packages = {s.package for s in sightings}
        assert packages == {"actions/checkout", "actions/setup-python"}
        for s in sightings:
            assert s.version == "v6"
            assert s.location == "uses"
            assert s.file == ".github/workflows/ci.yml"

    def test_extracts_inline_version_pins_in_run_blocks(self, tmp_path):
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text(
            dedent("""
                jobs:
                  lint:
                    runs-on: ubuntu-latest
                    steps:
                      - name: markdownlint
                        run: npx --yes markdownlint-cli2@0.22.1 "**/*.md"
            """)
        )
        sightings = parse_workflow(wf, root=tmp_path)
        # uses: parser may or may not see anything; run-block parser should see one.
        run_sightings = [s for s in sightings if s.location == "run"]
        assert run_sightings == [
            Sighting(
                package="markdownlint-cli2",
                file=".github/workflows/ci.yml",
                location="run",
                version="0.22.1",
            ),
        ]

    def test_ignores_non_version_at_signs(self, tmp_path):
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text(
            dedent("""
                jobs:
                  build:
                    runs-on: ubuntu-latest
                    steps:
                      - name: pull image
                        run: docker pull foo/bar@sha256:abcdef
            """)
        )
        sightings = parse_workflow(wf, root=tmp_path)
        # The sha256 digest must not be captured as a version.
        assert sightings == []
