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

5. **Commit on a hyphen-separated branch with no type prefix** (e.g., `bump-pre-commit-hooks`, not `chore/bump-pre-commit-hooks`), push, open a PR.

## Falling back to direct reads

If a finding looks suspicious, read the file directly with the `Read` tool to confirm the script's interpretation.
