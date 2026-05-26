"""Unit tests for drift_lib."""

from __future__ import annotations

from textwrap import dedent

import pytest
from drift_lib import (
    Finding,
    Sighting,
    analyze_sightings,
    normalize_name,
    parse_precommit_config,
    parse_requirements,
    parse_workflow,
    scan_root,
)


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


class TestAnalyzeSightings:
    def test_single_sighting_packages_are_dropped(self):
        sightings = [
            Sighting(package="lonely", file="a.txt", location="line 1", version="1.0"),
        ]
        assert analyze_sightings(sightings) == []

    def test_matching_versions_emit_in_sync(self):
        sightings = [
            Sighting(package="pyyaml", file="a.txt", location="line 1", version=">=6.0.3"),
            Sighting(package="pyyaml", file="b.yaml", location="hook=foo", version=">=6.0.3"),
        ]
        findings = analyze_sightings(sightings)
        assert len(findings) == 1
        assert findings[0].package == "pyyaml"
        assert findings[0].status == "in_sync"
        assert findings[0].recommendation == "in sync (informational)"

    def test_drift_recommends_bumping_lagging_to_highest(self):
        sightings = [
            Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3"),
            Sighting(package="pyyaml", file=".pre-commit-config.yaml", location="hook=adr-validate", version=">=6.0"),
        ]
        findings = analyze_sightings(sightings)
        assert len(findings) == 1
        f = findings[0]
        assert f.status == "drift"
        assert f.recommendation == "bump .pre-commit-config.yaml (hook=adr-validate) to >=6.0.3"

    def test_drift_with_multiple_lagging_lists_them(self):
        sightings = [
            Sighting(package="actions/checkout", file=".github/workflows/a.yml", location="uses", version="v6"),
            Sighting(package="actions/checkout", file=".github/workflows/b.yml", location="uses", version="v5"),
            Sighting(package="actions/checkout", file=".github/workflows/c.yml", location="uses", version="v5"),
        ]
        findings = analyze_sightings(sightings)
        assert len(findings) == 1
        f = findings[0]
        assert f.status == "drift"
        assert ".github/workflows/b.yml" in f.recommendation
        assert ".github/workflows/c.yml" in f.recommendation
        assert "v6" in f.recommendation

    def test_v_prefix_and_plain_versions_are_treated_as_in_sync(self):
        # Same version expressed with and without leading 'v' should not be drift.
        sightings = [
            Sighting(package="markdownlint-cli2", file=".pre-commit-config.yaml", location="repo", version="v0.22.1"),
            Sighting(package="markdownlint-cli2", file=".github/workflows/ci.yml", location="run", version="0.22.1"),
        ]
        findings = analyze_sightings(sightings)
        assert len(findings) == 1
        assert findings[0].status == "in_sync"

    def test_equivalent_specifiers_with_different_raw_strings_are_in_sync(self):
        # Both >=6.0.3 and ==6.0.3 normalize to the same Version. They are
        # different *specifiers* but the same version pin — treat as in_sync.
        # (Conservative call: equal underlying Version => in_sync.)
        sightings = [
            Sighting(package="pyyaml", file="a.txt", location="line 1", version=">=6.0.3"),
            Sighting(package="pyyaml", file="b.txt", location="line 2", version="==6.0.3"),
        ]
        findings = analyze_sightings(sightings)
        assert len(findings) == 1
        assert findings[0].status == "in_sync"


class TestScanRoot:
    def test_clean_fixture_emits_only_in_sync_findings_or_empty(self, fixture_repo):
        root = fixture_repo("clean")
        findings = scan_root(root)
        # All findings must be in_sync if any are present.
        for f in findings:
            assert f.status == "in_sync", f"unexpected drift in clean fixture: {f}"

    def test_returns_empty_when_no_files_exist(self, tmp_path):
        # tmp_path has none of the scanned files.
        assert scan_root(tmp_path) == []

    def test_scans_both_yml_and_yaml_workflow_extensions(self, tmp_path):
        # GitHub Actions accepts both .yml and .yaml. The scanner must handle both.
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            dedent("""
                jobs:
                  build:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v6
            """)
        )
        (wf_dir / "release.yaml").write_text(
            dedent("""
                jobs:
                  publish:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v5
            """)
        )
        findings = scan_root(tmp_path)
        drift = [f for f in findings if f.status == "drift"]
        assert len(drift) == 1
        assert drift[0].package == "actions/checkout"


class TestScanRootDriftCases:
    def test_additional_deps_drift_is_detected(self, fixture_repo):
        findings = scan_root(fixture_repo("drift_additional_deps"))
        drift = [f for f in findings if f.status == "drift"]
        assert len(drift) == 1
        f = drift[0]
        assert f.package == "pyyaml"
        assert ".pre-commit-config.yaml" in f.recommendation
        assert ">=6.0.3" in f.recommendation

    def test_inline_ci_drift_is_detected(self, fixture_repo):
        findings = scan_root(fixture_repo("drift_inline_ci"))
        drift = [f for f in findings if f.status == "drift"]
        assert len(drift) == 1
        assert drift[0].package == "markdownlint-cli2"

    def test_uses_action_drift_across_workflows_is_detected(self, fixture_repo):
        findings = scan_root(fixture_repo("drift_uses_action"))
        drift = [f for f in findings if f.status == "drift"]
        assert len(drift) == 1
        f = drift[0]
        assert f.package == "actions/checkout"
        assert "v6" in f.recommendation
        assert "release.yml" in f.recommendation
