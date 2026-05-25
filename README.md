# rhystic-library-api

API for the Rhystic Library.

> **Status:** the application code is not yet in this repository. Build tooling,
> framework, and module layout will be captured as ADRs before any application
> code lands. What's here today is the ADR process itself and the tooling that
> supports it.

## Architecture Decisions

Significant technical decisions are captured as Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/). Each ADR represents a single decision, is numbered sequentially (`NNNNNN-kebab-slug.md`), and is immutable once accepted — superseded decisions are replaced by newer ADRs rather than edited.

Start with [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md) to understand the process. Two companion files live alongside the ADRs:

- [`_template.md`](docs/adr/_template.md) — copy-paste skeleton for new ADRs.
- [`_tags.md`](docs/adr/_tags.md) — allowed tag list.

## Repository layout

```text
.
├── docs/
│   └── adr/                       # ADR records (NNNNNN-kebab-slug.md)
├── tools/
│   └── adr/                       # Python tooling supporting the ADR process
│       ├── adr_lib.py             # Shared parsing helpers
│       ├── cli_format.py          # Shared CLI output formatting
│       ├── validate.py            # CI validator (numbering, schema, tags,
│       │                          #   body structure, frontmatter ↔ table,
│       │                          #   merge-gate)
│       ├── list_adrs.py           # Discovery scripts
│       ├── find_adrs.py
│       ├── show_adr.py
│       ├── list_tags.py           # Tag scripts
│       ├── tag_usage.py
│       ├── new_adr.py             # Creation scripts
│       ├── add_tag.py
│       └── tests/                 # pytest suite for tools/adr
├── .claude/skills/                # Project-level Claude skills (wrap the scripts above)
├── .github/workflows/ci.yml       # CI definition
├── .github/dependabot.yml         # Weekly dependency PRs
├── .pre-commit-config.yaml        # Local git hooks
├── .editorconfig, .gitignore,     # Cross-language repo hygiene
│   .markdownlint.jsonc
├── pyproject.toml                 # Python tooling config (pytest, ruff, coverage)
└── requirements-dev.txt           # Python dev dependencies
```

The Python tooling under `tools/adr/` is scoped to the ADR process. It is independent of any future application code.

## Local setup

Requires **Python 3.10+** (CI uses 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pre-commit install   # one-time: enables format + lint + ADR validation on every commit
```

## Common commands

```bash
# Test suite (with coverage; the project's coverage floor is 92%)
pytest --cov=tools/adr

# Python lint and format
ruff check tools/adr
ruff format tools/adr             # auto-fixes formatting
ruff format --check tools/adr     # CI-style check (no edits)

# Validate ADRs
python tools/adr/validate.py              # local mode (allows Proposed status)
python tools/adr/validate.py --merge-gate # CI mode (Proposed blocks merge)

# Discover existing ADRs
python tools/adr/list_adrs.py
python tools/adr/find_adrs.py --tag <tag> --status Accepted
python tools/adr/show_adr.py 000001

# Tag operations
python tools/adr/list_tags.py
python tools/adr/tag_usage.py
python tools/adr/add_tag.py <slug> "Description"

# Scaffold a new ADR
python tools/adr/new_adr.py <kebab-slug>

# Run every pre-commit hook against the whole tree
pre-commit run --all-files
```

## Continuous integration

CI runs on every pull request and every push to `main`. All jobs must pass to merge.

| Job | What it does |
| --- | --- |
| `markdown-lint` | `markdownlint-cli2` over `**/*.md` (excludes `docs/superpowers/**`) |
| `lint-python` | `ruff check` + `ruff format --check` against `tools/adr` |
| `python-tests` | `pytest --cov=tools/adr` (coverage floor: 92%) |
| `adr-validate` | `python tools/adr/validate.py --merge-gate` |
| `gitleaks` | Secret scan |

Dependabot opens weekly PRs for Python (`pip`) and GitHub Actions updates.
