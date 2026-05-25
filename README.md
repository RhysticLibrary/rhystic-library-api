# rhystic-library-api

API for the Rhystic Library.

## Architecture Decisions

Significant technical decisions are captured as Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/). Each ADR represents a single decision, is numbered sequentially (`NNNNNN-kebab-slug.md`), and is immutable once accepted — superseded decisions are replaced by newer ADRs rather than edited.

Start with [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md) to understand the process. Two companion files live alongside the ADRs:

- [`_template.md`](docs/adr/_template.md) — copy-paste skeleton for new ADRs.
- [`_tags.md`](docs/adr/_tags.md) — allowed tag list.

## Development

Set up the Python tooling used by ADR scripts and CI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run the ADR test suite:

```bash
pytest
```

Validate ADRs locally:

```bash
python tools/adr/validate.py            # development mode
python tools/adr/validate.py --merge-gate  # CI mode
```
