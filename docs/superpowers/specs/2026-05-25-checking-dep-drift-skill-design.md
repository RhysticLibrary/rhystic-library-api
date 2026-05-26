# Design: `checking-dep-drift` skill

**Date:** 2026-05-25
**Status:** Approved (pending implementation)

## Goal

Give Claude a fast, low-token runbook for the cleanup work that follows a batch of merged dependabot PRs. The specific gap we are closing: `pre-commit autoupdate` bumps remote `rev:` pins, but it does not touch `additional_dependencies` inside hooks or inline version pins in CI shell steps. Drift here is silent — the hook env stays on the old floor, CI keeps installing the old version, and nothing fails until something else breaks.

This session caught one such drift by hand (`pyyaml>=6.0` on the `adr-validate` hook, while `requirements-dev.txt` had moved to `>=6.0.3`). The skill makes that check repeatable.

## Scope

In scope:

- A single-purpose script that scans `.pre-commit-config.yaml`, `requirements-dev.txt`, and `.github/workflows/*.yml`, reports version drift between matching packages, and exits with a status code indicating whether drift was found.
- A skill (`.claude/skills/checking-dep-drift/SKILL.md`) whose runbook tells Claude to run `pre-commit autoupdate`, then run the script, then apply fixes by hand, then verify and PR.
- Tests for the parsing/comparison logic and an end-to-end CLI test using fixture repos.

Out of scope:

- Auto-fixing drift. The script never writes files; Claude reads the report and edits config by hand.
- Querying upstream registries (PyPI, GitHub releases). The script only compares versions already present in the repo.
- Wrapping `pre-commit autoupdate`. It is a stable upstream CLI and a wrapper adds nothing.
- Proactive invocation. The skill description tells Claude to use it on explicit user request, not after observing recent `chore(deps)` commits.
- Other dependency ecosystems (npm `package.json`, Docker images, etc.) — not present in this repo today; add when they show up.

## Why a skill (and why a script)

Two artifacts because they do different jobs:

- The **script** is the parser and comparator. It is the cheap, repeatable part. Putting this logic in code (rather than asking Claude to read three files and reason about them) saves tokens on every invocation and removes a class of human-style reasoning errors.
- The **skill** is the runbook. It tells Claude what order to run things in, when to `pre-commit clean`, what counts as verification, and how to land the PR. None of that is in the script; none of the parsing is in the skill.

## File layout

```text
.claude/skills/checking-dep-drift/
  SKILL.md

tools/deps/
  check_drift.py        # CLI entry
  drift_lib.py          # parsing + comparison helpers
  tests/
    __init__.py
    test_drift_lib.py
    test_check_drift.py
    fixtures/
      clean/
      drift_additional_deps/
      drift_inline_ci/
      drift_uses_action/
      malformed/
```

Naming follows the existing `tools/adr/` precedent (directory per topic, `*_lib.py` for the importable library, CLI scripts at the top of the directory). Skill name follows the existing `searching-adrs` / `listing-adr-tags` gerund convention.

## Script: `tools/deps/check_drift.py`

### Invocation

```bash
python tools/deps/check_drift.py [--json] [--root PATH]
```

- `--json` — emit machine-readable JSON instead of the default human report.
- `--root` — repo root (defaults to current working directory). Used by tests so fixture trees can stand in for the real repo.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No drift found |
| `1` | Drift found (report on stdout) |
| `2` | Parse error or other failure (message on stderr) |

Claude can branch on the exit code without parsing the output.

### What it scans

| File | Extracts |
| --- | --- |
| `.pre-commit-config.yaml` | `repos[].rev`, `repos[].hooks[].additional_dependencies[]` |
| `requirements-dev.txt` | `<pkg><spec><version>` lines (PEP 508 lite; ignore comments and blank lines) |
| `.github/workflows/*.yml` | `uses: foo/bar@vN` action pins, and `@<semver>` patterns inside `run:` shell strings |

YAML is parsed with `pyyaml` (already a dev dep). Inline shell pins inside `run:` blocks use a regex over the string value once YAML has extracted it.

### Cross-reference and reporting

After extraction, package names are normalized (lowercase; `_` ↔ `-`) and grouped. Within each group:

- If all sighted version specifiers are equal → status `in_sync` (informational; reported only when the package appears in 2+ files, so Claude knows the pins are linked when bumping).
- If any specifiers differ → status `drift`; recommendation points to the highest version seen.

Version comparison is "best effort":

- Exact tags (`v6.0.0` vs `v5.0.0`) compared via `packaging.version.Version` after stripping a leading `v`.
- Floor specifiers (`>=6.0` vs `>=6.0.3`) compared by the version after the operator.
- If a version is unparseable, the script flags drift and includes the raw strings, leaving the call to Claude.

`packaging` is the comparator. It is already installed transitively in this repo's dev env (pulled by `pre-commit` / `pip`), but the implementation should add it explicitly to `requirements-dev.txt` rather than rely on transitive resolution.

### Report format

**Human (default):**

```text
DRIFT FOUND (2 findings):

pyyaml
  requirements-dev.txt:3                          >=6.0.3
  .pre-commit-config.yaml hook=adr-validate       >=6.0
  -> bump .pre-commit-config.yaml floor to >=6.0.3

markdownlint-cli2
  .pre-commit-config.yaml repo                    v0.22.1
  .github/workflows/ci.yml:31 (npx)               0.22.1
  -> in sync (informational)
```

**JSON (`--json`):**

```json
[
  {
    "package": "pyyaml",
    "status": "drift",
    "sightings": [
      {"file": "requirements-dev.txt", "location": "line 3", "version": ">=6.0.3"},
      {"file": ".pre-commit-config.yaml", "location": "hook=adr-validate", "version": ">=6.0"}
    ],
    "recommendation": "bump .pre-commit-config.yaml floor to >=6.0.3"
  }
]
```

Schema is stable so future tooling can consume it.

### What the script never does

- Never writes to any file.
- Never invokes `pre-commit autoupdate`.
- Never reaches the network.

These three constraints keep the blast radius small and the test surface tractable.

## Skill: `.claude/skills/checking-dep-drift/SKILL.md`

```markdown
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
   Exit 0 = clean, exit 1 = drift. Read the report; each finding has a `->` recommendation.

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
```

Notes on the skill body:

- The frontmatter `description` does double duty: tells Claude when to invoke, and explains why this exists separately from `pre-commit autoupdate`. Without the second clause, a reader could reasonably ask why we don't just run autoupdate.
- `pre-commit clean` is called out because the failure mode of skipping it is invisible — the cached hook env keeps running on the old floor.
- No file paths are mentioned in the skill body; all scanning paths live in the script. If we add `requirements-prod.txt` later, only the script changes.

## Testing

Two test files, each cheap, each catching a different class of bug.

### `tools/deps/tests/test_drift_lib.py` — unit tests

Pure-function tests for the parsing and comparison logic:

- Parse `.pre-commit-config.yaml` into `(repo_url, rev, [(hook_id, [additional_deps])])`.
- Parse `requirements-dev.txt` into `[(pkg, specifier)]`.
- Parse a workflow file: extract `uses:` action pins and `@<semver>` patterns from `run:` shell strings.
- Name normalization (`PyYAML` ↔ `pyyaml`, `markdownlint_cli2` ↔ `markdownlint-cli2`).
- Cross-reference: given a list of sightings, identify drift vs in-sync.
- Version comparison helper: `>=6.0` < `>=6.0.3`; exact tags compared via `packaging.version.Version`.
- Edge cases: hooks with no `additional_dependencies`, a workflow `run:` block with a non-version `@` (e.g., `@sha256:...`), a malformed YAML file.

### `tools/deps/tests/test_check_drift.py` — CLI end-to-end

Subprocess tests mirroring the `tools/adr/tests/test_skill_scripts.py` pattern. Each test points the script at a fixture repo via `--root` and asserts on exit code + output:

- Clean fixture → exit 0, empty findings.
- `drift_additional_deps/` fixture (the `pyyaml` case from this session) → exit 1, finding reports both sightings and recommends `>=6.0.3`.
- `drift_inline_ci/` fixture → exit 1, finding pairs `.pre-commit-config.yaml` with the workflow's `npx` line.
- `drift_uses_action/` fixture → exit 1, finding pairs the two workflows.
- `--json` produces a JSON array parseable with `json.loads` and matching the documented schema.
- `--root` resolves correctly.
- `malformed/` fixture → exit 2 with a stderr message.

### Fixtures

`tools/deps/tests/fixtures/` contains small repo-shaped trees with only the files the script reads:

| Fixture | Purpose |
| --- | --- |
| `clean/` | Versions aligned across all three file types |
| `drift_additional_deps/` | `pyyaml` floor mismatch between `requirements-dev.txt` and a hook |
| `drift_inline_ci/` | `markdownlint-cli2` pinned at different versions in `.pre-commit-config.yaml` and a workflow `run:` line |
| `drift_uses_action/` | `actions/checkout@v5` vs `@v6` across two workflows |
| `malformed/` | Busted YAML to exercise the exit-2 path |

### Coverage

Add `"tools/deps"` to `pyproject.toml [tool.coverage.run] source`. Add the CLI scripts (`tools/deps/check_drift.py`) to the `omit` list, matching the `tools/adr/*.py` CLI pattern — they are covered end-to-end via subprocess in `test_check_drift.py` but `coverage.py` does not follow subprocess boundaries, so including them would inflate uncovered counts.

`drift_lib.py` carries the measured coverage. The 92% `fail_under` threshold stays the gate.

## Open questions / future work

- **npm and Docker.** Not in this repo today. When they show up, extend the script's scan list rather than the skill's runbook.
- **Proactive invocation.** Currently manual. If the post-dependabot batch becomes a regular rhythm, consider a scheduled/automated trigger separately — out of scope here.
- **Auto-fix.** Deliberately left out. If repeated use shows the by-hand fix step is rote and low-judgment, a `--fix` flag could be added later as a focused follow-up; the current `--json` output already gives a future tool everything it needs.
