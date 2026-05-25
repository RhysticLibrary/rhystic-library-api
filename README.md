# rhystic-library-api

API for the Rhystic Library.

## Architecture Decisions

Significant technical decisions are captured as Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/). Each ADR represents a single decision, is numbered sequentially (`NNNNNN-kebab-slug.md`), and is immutable once accepted — superseded decisions are replaced by newer ADRs rather than edited.

Start with [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md) to understand the process. Two companion files live alongside the ADRs:

- [`_template.md`](docs/adr/_template.md) — copy-paste skeleton for new ADRs.
- [`_tags.md`](docs/adr/_tags.md) — allowed tag list.

## Development

Requires **Python 3.10+** (CI uses 3.12). Set up the dev environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install   # one-time: enables format + lint + ADR validation on every commit
```

Run the test suite (with coverage):

```bash
pytest --cov=tools/adr
```

Lint and format Python locally (CI checks the same):

```bash
ruff check tools/adr
ruff format tools/adr            # auto-fixes formatting
ruff format --check tools/adr    # CI-style check
```

Validate ADRs locally:

```bash
python tools/adr/validate.py              # development mode (no merge gate)
python tools/adr/validate.py --merge-gate # CI mode
```
