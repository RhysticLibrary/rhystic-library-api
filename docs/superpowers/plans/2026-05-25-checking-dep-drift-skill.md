# `checking-dep-drift` Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `checking-dep-drift` skill backed by a Python script (`tools/deps/check_drift.py`) that reports cross-file dependency version drift — the gap `pre-commit autoupdate` doesn't cover.

**Architecture:** One CLI script (`check_drift.py`) over a pure-function library (`drift_lib.py`). The script scans `.pre-commit-config.yaml` (`rev:` + `additional_dependencies`), `requirements-dev.txt`, and `.github/workflows/*.yml` (action `uses:` pins + inline `@<semver>` in `run:` blocks), normalizes package names, groups sightings, and reports drift. Never writes files; never reaches the network. Skill (`.claude/skills/checking-dep-drift/SKILL.md`) is the runbook that wraps `pre-commit autoupdate` + this script + verification + commit.

**Tech Stack:** Python 3.10+, `pyyaml`, `packaging`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-05-25-checking-dep-drift-skill-design.md`

---

## File Structure

```text
.claude/skills/checking-dep-drift/
  SKILL.md                              # skill manifest + runbook

tools/deps/
  __init__.py                           # empty; makes the dir tidy
  drift_lib.py                          # parsing + comparison helpers
  check_drift.py                        # CLI entry
  tests/
    __init__.py
    conftest.py                         # fixture-tree helpers
    test_drift_lib.py                   # unit tests
    test_check_drift.py                 # subprocess CLI tests
    fixtures/
      clean/
        .pre-commit-config.yaml
        requirements-dev.txt
        .github/workflows/ci.yml
      drift_additional_deps/
        .pre-commit-config.yaml
        requirements-dev.txt
        .github/workflows/ci.yml
      drift_inline_ci/
        .pre-commit-config.yaml
        requirements-dev.txt
        .github/workflows/ci.yml
      drift_uses_action/
        .pre-commit-config.yaml
        requirements-dev.txt
        .github/workflows/{ci.yml,release.yml}
      malformed/
        .pre-commit-config.yaml         # broken YAML

requirements-dev.txt                    # add `packaging>=21.0`
pyproject.toml                          # add tools/deps to pythonpath + coverage source
```

**Responsibilities:**

- `drift_lib.py` — all parsing, name normalization, drift analysis. Pure functions over `Path` inputs; returns dataclasses. Tested directly.
- `check_drift.py` — argparse + I/O + formatting + exit codes. Thin shell over `drift_lib`. Tested via subprocess.
- `tests/conftest.py` — `fixture_repo` fixture that points pytest at the `fixtures/<name>/` directory.
- `SKILL.md` — runbook only; references the script but never duplicates its logic.

---

## Task 1: Bootstrap project structure

**Files:**
- Modify: `requirements-dev.txt`
- Modify: `pyproject.toml`
- Create: `tools/deps/__init__.py`
- Create: `tools/deps/tests/__init__.py`

- [ ] **Step 1: Add `packaging` to dev requirements**

Edit `requirements-dev.txt`. The current contents are:
```text
pytest>=9.0.3
pytest-cov>=7.1.0
pyyaml>=6.0.3
ruff>=0.15.14
pre-commit>=4.6.0
```

Add one line so it becomes:
```text
pytest>=9.0.3
pytest-cov>=7.1.0
pyyaml>=6.0.3
packaging>=21.0
ruff>=0.15.14
pre-commit>=4.6.0
```

- [ ] **Step 2: Update `pyproject.toml` for coverage + pythonpath**

In `pyproject.toml`:

1. Under `[tool.pytest.ini_options]`, change `pythonpath = ["tools/adr"]` to `pythonpath = ["tools/adr", "tools/deps"]`.
2. Under `[tool.pytest.ini_options]`, change `testpaths = ["tools/adr/tests"]` to `testpaths = ["tools/adr/tests", "tools/deps/tests"]`.
3. Under `[tool.coverage.run]`, change `source = ["tools/adr"]` to `source = ["tools/adr", "tools/deps"]`.
4. Under `[tool.coverage.run] omit`, after the existing ADR entries, add: `"tools/deps/check_drift.py",`

- [ ] **Step 3: Create empty `__init__.py` files**

```bash
mkdir -p tools/deps/tests/fixtures
touch tools/deps/__init__.py tools/deps/tests/__init__.py
```

- [ ] **Step 4: Install the new dep into the venv**

Run: `source .venv/bin/activate && pip install -r requirements-dev.txt`
Expected: `packaging` already satisfied or freshly installed; no errors.

- [ ] **Step 5: Confirm pytest still discovers nothing new yet**

Run: `pytest`
Expected: existing ADR tests still pass; no errors from the new empty `tools/deps/tests/` directory.

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt pyproject.toml tools/deps/__init__.py tools/deps/tests/__init__.py
git commit -m "feat(deps): scaffold tools/deps for dep-drift checker"
```

---

## Task 2: Build the `clean` fixture and conftest helper

**Files:**
- Create: `tools/deps/tests/conftest.py`
- Create: `tools/deps/tests/fixtures/clean/.pre-commit-config.yaml`
- Create: `tools/deps/tests/fixtures/clean/requirements-dev.txt`
- Create: `tools/deps/tests/fixtures/clean/.github/workflows/ci.yml`

- [ ] **Step 1: Create the conftest helper**

Create `tools/deps/tests/conftest.py`:

```python
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
```

- [ ] **Step 2: Create the `clean` fixture tree**

Create `tools/deps/tests/fixtures/clean/.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: end-of-file-fixer

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.14
    hooks:
      - id: ruff-check

  - repo: local
    hooks:
      - id: adr-validate
        name: ADR validator
        entry: python tools/adr/validate.py
        language: python
        pass_filenames: false
        additional_dependencies: ["pyyaml>=6.0.3"]
```

Create `tools/deps/tests/fixtures/clean/requirements-dev.txt`:
```text
pytest>=9.0.3
pyyaml>=6.0.3
ruff>=0.15.14
```

Create `tools/deps/tests/fixtures/clean/.github/workflows/ci.yml`:
```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Lint
        run: ruff check .
```

- [ ] **Step 3: Confirm fixture discovery doesn't break collection**

Run: `pytest tools/deps/tests/ -v`
Expected: no tests collected, no errors.

- [ ] **Step 4: Commit**

```bash
git add tools/deps/tests/conftest.py tools/deps/tests/fixtures/clean/
git commit -m "test(deps): add conftest + clean fixture tree"
```

---

## Task 3: Define `Sighting` and `Finding` dataclasses

**Files:**
- Create: `tools/deps/drift_lib.py`
- Create: `tools/deps/tests/test_drift_lib.py`

- [ ] **Step 1: Write the failing test**

Create `tools/deps/tests/test_drift_lib.py`:

```python
"""Unit tests for drift_lib."""

from __future__ import annotations

import pytest

from drift_lib import Finding, Sighting


class TestDataClasses:
    def test_sighting_holds_package_file_location_version(self):
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        assert s.package == "pyyaml"
        assert s.file == "requirements-dev.txt"
        assert s.location == "line 3"
        assert s.version == ">=6.0.3"

    def test_finding_holds_package_status_sightings_recommendation(self):
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        f = Finding(package="pyyaml", status="drift", sightings=[s], recommendation="bump to >=6.0.3")
        assert f.package == "pyyaml"
        assert f.status == "drift"
        assert f.sightings == [s]
        assert f.recommendation == "bump to >=6.0.3"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestDataClasses -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'drift_lib'`

- [ ] **Step 3: Create `drift_lib.py` with the dataclasses**

Create `tools/deps/drift_lib.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestDataClasses -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): add Sighting and Finding dataclasses"
```

---

## Task 4: Name normalization

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from drift_lib import normalize_name


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestNormalizeName -v`
Expected: FAIL — `ImportError: cannot import name 'normalize_name'`.

- [ ] **Step 3: Implement `normalize_name`**

Append to `tools/deps/drift_lib.py`:

```python
def normalize_name(name: str) -> str:
    """Lowercase + collapse underscores to hyphens for cross-file matching.

    Slashes are preserved so action references like ``actions/checkout`` keep
    their namespace.
    """
    return name.lower().replace("_", "-")
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestNormalizeName -v`
Expected: PASS (6 parameterized cases).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): add normalize_name helper"
```

---

## Task 5: Parse `.pre-commit-config.yaml`

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

The parser pulls two kinds of pins:
- `repos[].rev` — the repo basename (last URL segment) is the package name; version is the raw `rev:` string.
- `repos[].hooks[].additional_dependencies[]` — entry is a PEP 508 requirement like `pyyaml>=6.0`; split into name + specifier.

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from pathlib import Path
from textwrap import dedent

from drift_lib import parse_precommit_config


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
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParsePrecommitConfig -v`
Expected: FAIL — `ImportError: cannot import name 'parse_precommit_config'`.

- [ ] **Step 3: Implement `parse_precommit_config`**

Append to `tools/deps/drift_lib.py`:

```python
from pathlib import Path

import yaml
from packaging.requirements import InvalidRequirement, Requirement


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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParsePrecommitConfig -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): parse pre-commit config rev pins and additional_dependencies"
```

---

## Task 6: Parse `requirements-dev.txt`

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from drift_lib import parse_requirements


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
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParseRequirements -v`
Expected: FAIL — `ImportError: cannot import name 'parse_requirements'`.

- [ ] **Step 3: Implement `parse_requirements`**

Append to `tools/deps/drift_lib.py`:

```python
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParseRequirements -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): parse requirements-dev.txt entries"
```

---

## Task 7: Parse GitHub workflow files

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

Two pin types in a workflow YAML:
- `uses: foo/bar@vN` — extracted from the YAML tree at any depth.
- `@<semver>` inside `run:` shell strings — regex captures `(identifier)@(v?digits.digits...)`.

The regex must NOT match `@sha256:abc...` (no colons after the version) and must NOT match bare email-like `@` in URLs (it requires a version after the `@`, starting with `v` + digit or just digits).

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from drift_lib import parse_workflow


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
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParseWorkflow -v`
Expected: FAIL — `ImportError: cannot import name 'parse_workflow'`.

- [ ] **Step 3: Implement `parse_workflow`**

Append to `tools/deps/drift_lib.py`:

```python
import re

_INLINE_VERSION_RE = re.compile(
    r"\b([a-zA-Z][\w\-]*(?:/[a-zA-Z][\w\-]*)?)@(v?\d+(?:\.\d+)*)\b"
)


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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestParseWorkflow -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): parse workflow uses pins and inline run version refs"
```

---

## Task 8: Group sightings and analyze drift

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

`analyze_sightings` takes a flat list, groups by `package`, and emits one `Finding` per package that appears in 2+ sightings. Single-sighting packages are dropped (nothing to compare). Status: `"in_sync"` if all `version` strings are equal, else `"drift"`.

For drift recommendations:
- Find the highest version (parsing with `packaging.version.Version` after stripping a leading `v` and any leading `>=`/`==`/`~=`/etc).
- Single lagging sighting → `f"bump {file} ({location}) to {highest_raw}"`.
- Multiple lagging → `f"bump to {highest_raw} (lagging: {file1:location1}, {file2:location2}, ...)"`.

For in-sync, the recommendation is literally `"in sync (informational)"`.

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from drift_lib import analyze_sightings


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
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestAnalyzeSightings -v`
Expected: FAIL — `ImportError: cannot import name 'analyze_sightings'`.

- [ ] **Step 3: Implement `analyze_sightings`**

Append to `tools/deps/drift_lib.py`:

```python
from collections import defaultdict

from packaging.version import InvalidVersion, Version


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

        findings.append(
            Finding(package=package, status="drift", sightings=list(group), recommendation=recommendation)
        )

    return findings
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestAnalyzeSightings -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): group sightings and detect drift with recommendations"
```

---

## Task 9: `scan_root` orchestration

**Files:**
- Modify: `tools/deps/drift_lib.py`
- Modify: `tools/deps/tests/test_drift_lib.py`

`scan_root(root: Path)` runs all parsers over the relevant files in a repo root and returns `list[Finding]`. Missing files are silently skipped (a repo without a `requirements-dev.txt` is valid).

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
from drift_lib import scan_root


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
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestScanRoot -v`
Expected: FAIL — `ImportError: cannot import name 'scan_root'`.

- [ ] **Step 3: Implement `scan_root`**

Append to `tools/deps/drift_lib.py`:

```python
def scan_root(root: Path) -> list[Finding]:
    """Scan a repo root for cross-file dependency drift."""
    sightings: list[Sighting] = []

    precommit = root / ".pre-commit-config.yaml"
    if precommit.is_file():
        sightings.extend(parse_precommit_config(precommit, root=root))

    reqs = root / "requirements-dev.txt"
    if reqs.is_file():
        sightings.extend(parse_requirements(reqs, root=root))

    workflows_dir = root / ".github" / "workflows"
    if workflows_dir.is_dir():
        for wf in sorted(workflows_dir.glob("*.yml")):
            sightings.extend(parse_workflow(wf, root=root))

    return analyze_sightings(sightings)
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestScanRoot -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/drift_lib.py tools/deps/tests/test_drift_lib.py
git commit -m "feat(deps): add scan_root orchestration over a repo tree"
```

---

## Task 10: Build the drift fixture trees

**Files:**
- Create: `tools/deps/tests/fixtures/drift_additional_deps/{.pre-commit-config.yaml,requirements-dev.txt,.github/workflows/ci.yml}`
- Create: `tools/deps/tests/fixtures/drift_inline_ci/{.pre-commit-config.yaml,requirements-dev.txt,.github/workflows/ci.yml}`
- Create: `tools/deps/tests/fixtures/drift_uses_action/{.pre-commit-config.yaml,requirements-dev.txt,.github/workflows/ci.yml,.github/workflows/release.yml}`

- [ ] **Step 1: `drift_additional_deps/` — pyyaml floor mismatch**

`tools/deps/tests/fixtures/drift_additional_deps/.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: adr-validate
        name: ADR validator
        entry: python tools/adr/validate.py
        language: python
        additional_dependencies: ["pyyaml>=6.0"]
```

`tools/deps/tests/fixtures/drift_additional_deps/requirements-dev.txt`:
```text
pyyaml>=6.0.3
```

`tools/deps/tests/fixtures/drift_additional_deps/.github/workflows/ci.yml`:
```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
```

- [ ] **Step 2: `drift_inline_ci/` — markdownlint-cli2 mismatch**

`tools/deps/tests/fixtures/drift_inline_ci/.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/DavidAnson/markdownlint-cli2
    rev: v0.23.0
    hooks:
      - id: markdownlint-cli2
```

`tools/deps/tests/fixtures/drift_inline_ci/requirements-dev.txt`:
```text
pytest>=9.0.3
```

`tools/deps/tests/fixtures/drift_inline_ci/.github/workflows/ci.yml`:
```yaml
name: CI
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: markdownlint
        run: npx --yes markdownlint-cli2@0.22.1 "**/*.md"
```

- [ ] **Step 3: `drift_uses_action/` — actions/checkout @v5 vs @v6**

`tools/deps/tests/fixtures/drift_uses_action/.pre-commit-config.yaml`:
```yaml
repos: []
```

`tools/deps/tests/fixtures/drift_uses_action/requirements-dev.txt`:
```text
pytest>=9.0.3
```

`tools/deps/tests/fixtures/drift_uses_action/.github/workflows/ci.yml`:
```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
```

`tools/deps/tests/fixtures/drift_uses_action/.github/workflows/release.yml`:
```yaml
name: Release
on:
  release:
    types: [created]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
```

- [ ] **Step 4: Commit fixtures**

```bash
git add tools/deps/tests/fixtures/drift_additional_deps tools/deps/tests/fixtures/drift_inline_ci tools/deps/tests/fixtures/drift_uses_action
git commit -m "test(deps): add drift fixture trees"
```

---

## Task 11: `scan_root` drift cases

**Files:**
- Modify: `tools/deps/tests/test_drift_lib.py`

- [ ] **Step 1: Write the failing tests**

Append to `tools/deps/tests/test_drift_lib.py`:

```python
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
```

- [ ] **Step 2: Run to verify all pass**

Run: `pytest tools/deps/tests/test_drift_lib.py::TestScanRootDriftCases -v`
Expected: PASS (3 tests). The drift logic is already implemented; these tests just exercise it end-to-end through fixtures.

- [ ] **Step 3: Commit**

```bash
git add tools/deps/tests/test_drift_lib.py
git commit -m "test(deps): cover scan_root drift cases via fixtures"
```

---

## Task 12: CLI human report + exit codes

**Files:**
- Create: `tools/deps/check_drift.py`
- Create: `tools/deps/tests/test_check_drift.py`

- [ ] **Step 1: Write the failing tests**

Create `tools/deps/tests/test_check_drift.py`:

```python
"""Subprocess tests for check_drift.py CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

DEPS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DEPS_DIR / "check_drift.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestExitCodes:
    def test_clean_fixture_exits_zero(self):
        result = run_cli("--root", str(FIXTURES / "clean"))
        assert result.returncode == 0, result.stderr
        assert "no drift" in result.stdout.lower() or result.stdout.strip() == ""

    def test_drift_fixture_exits_one(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"))
        assert result.returncode == 1, result.stderr
        assert "pyyaml" in result.stdout
        assert ">=6.0.3" in result.stdout

    def test_human_report_lists_sightings_under_package_header(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"))
        assert result.returncode == 1
        # Package name appears, then sighting files appear in subsequent lines.
        lines = result.stdout.splitlines()
        pkg_idx = next(i for i, line in enumerate(lines) if "pyyaml" in line)
        body = "\n".join(lines[pkg_idx:])
        assert ".pre-commit-config.yaml" in body
        assert "requirements-dev.txt" in body
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tools/deps/tests/test_check_drift.py::TestExitCodes -v`
Expected: FAIL — script does not exist, subprocess returns non-zero with `No such file or directory`.

- [ ] **Step 3: Implement `check_drift.py`**

Create `tools/deps/check_drift.py`:

```python
#!/usr/bin/env python3
"""Report cross-file dependency drift in this repo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from drift_lib import Finding, scan_root


def format_human(findings: list[Finding]) -> str:
    drift = [f for f in findings if f.status == "drift"]
    if not drift:
        return "no drift\n"

    out: list[str] = [f"DRIFT FOUND ({len(drift)} findings):", ""]
    for f in findings:
        if f.status != "drift":
            continue
        out.append(f.package)
        col_width = max(len(f"{s.file} {s.location}") for s in f.sightings) + 2
        for s in f.sightings:
            label = f"  {s.file} {s.location}".ljust(col_width + 2)
            out.append(f"{label}{s.version}")
        out.append(f"  -> {f.recommendation}")
        out.append("")
    return "\n".join(out) + "\n"


def format_json(findings: list[Finding]) -> str:
    payload = [
        {
            "package": f.package,
            "status": f.status,
            "sightings": [
                {"file": s.file, "location": s.location, "version": s.version}
                for s in f.sightings
            ],
            "recommendation": f.recommendation,
        }
        for f in findings
    ]
    return json.dumps(payload, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repo root (default: cwd)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit JSON instead of human text")
    args = parser.parse_args(argv)

    try:
        findings = scan_root(args.root)
    except Exception as exc:  # noqa: BLE001 — surfacing parser errors via exit 2
        print(f"check_drift: failed to scan {args.root}: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        sys.stdout.write(format_json(findings))
    else:
        sys.stdout.write(format_human(findings))

    return 1 if any(f.status == "drift" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tools/deps/tests/test_check_drift.py::TestExitCodes -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/deps/check_drift.py tools/deps/tests/test_check_drift.py
git commit -m "feat(deps): add check_drift.py CLI with human report and exit codes"
```

---

## Task 13: CLI `--json` output

**Files:**
- Modify: `tools/deps/tests/test_check_drift.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/deps/tests/test_check_drift.py`:

```python
class TestJsonOutput:
    def test_json_flag_emits_parseable_array(self):
        result = run_cli("--root", str(FIXTURES / "drift_additional_deps"), "--json")
        assert result.returncode == 1, result.stderr
        payload = json.loads(result.stdout)
        assert isinstance(payload, list)
        assert len(payload) == 1
        entry = payload[0]
        assert entry["package"] == "pyyaml"
        assert entry["status"] == "drift"
        assert entry["recommendation"].startswith("bump")
        files_seen = {s["file"] for s in entry["sightings"]}
        assert ".pre-commit-config.yaml" in files_seen
        assert "requirements-dev.txt" in files_seen

    def test_json_clean_fixture_returns_empty_array(self):
        result = run_cli("--root", str(FIXTURES / "clean"), "--json")
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        # Clean fixture has no drift; in-sync findings are still informational
        # entries — but we should never emit drift entries.
        assert all(entry["status"] != "drift" for entry in payload)
```

- [ ] **Step 2: Run to verify it passes**

Run: `pytest tools/deps/tests/test_check_drift.py::TestJsonOutput -v`
Expected: PASS (2 tests). The JSON output is already wired up in Task 12; these tests exercise it.

- [ ] **Step 3: Commit**

```bash
git add tools/deps/tests/test_check_drift.py
git commit -m "test(deps): cover --json output via the existing implementation"
```

---

## Task 14: Malformed-YAML handling (exit 2)

**Files:**
- Create: `tools/deps/tests/fixtures/malformed/.pre-commit-config.yaml`
- Modify: `tools/deps/tests/test_check_drift.py`

- [ ] **Step 1: Create the malformed fixture**

`tools/deps/tests/fixtures/malformed/.pre-commit-config.yaml`:
```yaml
repos:
  - repo: [unbalanced
    rev: v1.0.0
```

- [ ] **Step 2: Write the failing test**

Append to `tools/deps/tests/test_check_drift.py`:

```python
class TestMalformedYaml:
    def test_malformed_yaml_exits_two_with_stderr_message(self):
        result = run_cli("--root", str(FIXTURES / "malformed"))
        assert result.returncode == 2
        assert "check_drift" in result.stderr
```

- [ ] **Step 3: Run to verify it passes**

Run: `pytest tools/deps/tests/test_check_drift.py::TestMalformedYaml -v`
Expected: PASS. The `try/except Exception` in `main()` already catches the YAML parse error from Task 12.

- [ ] **Step 4: Commit**

```bash
git add tools/deps/tests/fixtures/malformed tools/deps/tests/test_check_drift.py
git commit -m "test(deps): cover malformed-yaml exit-2 path"
```

---

## Task 15: Write the skill manifest

**Files:**
- Create: `.claude/skills/checking-dep-drift/SKILL.md`

- [ ] **Step 1: Create the skill directory and SKILL.md**

```bash
mkdir -p .claude/skills/checking-dep-drift
```

Create `.claude/skills/checking-dep-drift/SKILL.md` with this exact content:

````markdown
---
name: checking-dep-drift
description: Use when checking pre-commit hook versions and cross-file dependency drift, typically after a batch of dependabot PRs has merged. Bumps `rev:` pins via `pre-commit autoupdate` and reports drift that autoupdate doesn't catch (e.g., `additional_dependencies`, inline CI version pins).
---

# Checking dependency drift

`pre-commit autoupdate` only bumps `rev:` pins on remote hook repos. It does NOT touch:
- `additional_dependencies:` inside hooks (e.g., `pyyaml>=6.0` on `adr-validate`)
- Inline version pins in CI shell steps (e.g., `npx ... markdownlint-cli2@0.22.1`)
- `uses: foo/bar@vN` consistency across workflow files

This skill walks the after-dependabot cleanup so those don't silently drift.

## When to use

- User asks to check pre-commit hooks / dependency drift after dependabot activity.
- Before opening a manual dep-bump PR, to find related pins worth bumping together.

## Runbook

1. **Sync remote pins.**
   ```bash
   pre-commit autoupdate
   ```
   Review the resulting diff to `.pre-commit-config.yaml`. Each bumped `rev:` is a candidate for changelog check if the major changed.

2. **Check for cross-file drift.**
   ```bash
   python tools/deps/check_drift.py
   ```
   Exit 0 = clean, exit 1 = drift, exit 2 = parse error. Read the report; each finding has a `->` recommendation.

3. **Apply fixes by hand.** For each drift finding, edit the lower-version side to match the higher. Most common: `additional_dependencies` floors in `.pre-commit-config.yaml` lagging behind `requirements-dev.txt`.

4. **Verify.**
   ```bash
   pre-commit clean        # only needed if additional_dependencies changed
   pre-commit run --all-files
   pytest                  # cheap and catches hook-env regressions
   ```

5. **Commit on a flat-named branch** (e.g., `bump-pre-commit-hooks`), push, open a PR.

## Falling back to direct reads

If a finding looks suspicious, read the file directly with the `Read` tool to confirm the script's interpretation.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/checking-dep-drift/SKILL.md
git commit -m "feat(skill): add checking-dep-drift runbook"
```

---

## Task 16: Real-repo smoke test and coverage gate

**Files:** none modified — verification only.

- [ ] **Step 1: Run the script against the real repo**

Run: `python tools/deps/check_drift.py`
Expected: exit code `0`, "no drift" output. (We fixed the pyyaml drift in PR #9; nothing else should be out of sync.)

If the script reports unexpected drift, investigate before proceeding — the script may be over-eager, or a real new drift may have appeared.

- [ ] **Step 2: Run the full test suite with coverage**

Run: `pytest --cov=tools/adr --cov=tools/deps --cov-report=term-missing`
Expected: all tests pass; coverage threshold (92%) holds. Inspect `term-missing` output for `drift_lib.py`; raise via additional tests if coverage on that file is materially below 90%.

- [ ] **Step 3: Run pre-commit on all files**

Run: `pre-commit run --all-files`
Expected: all hooks pass (the new files include valid YAML, formatted Python, and no markdown lint issues).

- [ ] **Step 4: No commit required**

Verification only. If everything is clean, this task is done.

---

## Self-Review

**Spec coverage:**

- ✅ `tools/deps/check_drift.py` + `tools/deps/drift_lib.py` — Tasks 3–9, 12.
- ✅ `--json` and `--root` flags — Tasks 12, 13.
- ✅ Exit codes 0/1/2 — Tasks 12, 14.
- ✅ Scans `.pre-commit-config.yaml` (rev + additional_dependencies), `requirements-dev.txt`, `.github/workflows/*.yml` (uses + inline run) — Tasks 5, 6, 7.
- ✅ Name normalization — Task 4.
- ✅ Cross-reference with drift/in_sync findings + recommendations — Task 8.
- ✅ Fixture trees: clean, drift_additional_deps, drift_inline_ci, drift_uses_action, malformed — Tasks 2, 10, 14.
- ✅ Unit + CLI tests — Tasks 3–9, 11, 12, 13, 14.
- ✅ `pyproject.toml` coverage + pythonpath updates; `packaging` in requirements-dev.txt — Task 1.
- ✅ SKILL.md with runbook — Task 15.
- ✅ Real-repo verification — Task 16.

**Placeholder scan:** No TBDs, no "add appropriate X", every code step shows actual code, every test step shows actual asserts. Exact file paths throughout.

**Type consistency:**
- `Sighting(package, file, location, version)` — used consistently across all parser and analyzer tasks.
- `Finding(package, status, sightings, recommendation)` — same.
- `scan_root(root)` signature unchanged across Tasks 9, 11.
- `parse_*(path, root=...)` keyword `root` consistent across all three parsers.
- `format_human` / `format_json` introduced together in Task 12; not referenced elsewhere.
