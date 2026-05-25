# CLAUDE.md

Project-level guidance for Claude working in this repository.

## Architecture Decision Records

- **Where:** `docs/adr/`. Companion files: `_template.md` and `_tags.md`.
- **Source of truth:** [`docs/adr/000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md). Read this once when you need full detail on the ADR process, structure, status lifecycle, or immutability rules.
- **Skills (use these instead of grepping by hand):**
  - `.claude/skills/searching-adrs/` — when looking up existing decisions by id, tag, status, or keyword.
  - `.claude/skills/listing-adr-tags/` — when picking tags for a new ADR or surveying topic areas.
  - `.claude/skills/creating-an-adr/` — when authoring a new ADR (scaffolds, validates, walks the merge flow).

Each skill ships helper scripts under `tools/adr/` that parse only frontmatter — prefer them over reading whole files when the question can be answered from metadata.

## Python tooling

- Python 3.10+ required; CI uses 3.12.
- Dev deps in `requirements-dev.txt`: pytest, pytest-cov, pyyaml, ruff, pre-commit.
- Tests: `pytest --cov=tools/adr` (coverage floor in `pyproject.toml` is 92%).
- Lint: `ruff check tools/adr`. Format: `ruff format tools/adr` (or `--check` for CI-style).
- Validator: `python tools/adr/validate.py` (add `--merge-gate` to mirror CI).
- Pre-commit hooks run ruff, markdownlint, file hygiene, and the ADR validator
  on every commit. Activate once with `pre-commit install`. Don't bypass with
  `--no-verify`; if a hook fails, fix the underlying issue.

## CI checks (must all pass to merge)

- `markdown-lint` — markdownlint over `**/*.md` (excluding `docs/superpowers/**`).
- `lint-python` — `ruff check` + `ruff format --check`.
- `tests` — `pytest --cov=tools/adr --cov-fail-under=92`.
- `adr-validate` — `python tools/adr/validate.py --merge-gate`.
- `gitleaks` — secret scan.

Dependabot opens weekly PRs for Python and GitHub Actions updates.
