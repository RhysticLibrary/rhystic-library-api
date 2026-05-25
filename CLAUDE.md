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

- Dev deps: `requirements-dev.txt` (pytest, pyyaml).
- Tests: `pytest` from repo root runs the ADR script tests.
- Validator: `python tools/adr/validate.py` (add `--merge-gate` to mirror CI).
