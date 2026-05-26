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

## Secrets — Never Commit

**Never commit secrets to this repository.** This is a hard rule, ratified by ADR 000002 (`docs/adr/000002-secrets-in-version-control.md`). It binds you the same way it binds human contributors.

Never commit:

- Environment files: `.env`, `.env.*`, and any file the local toolchain reads from disk to populate environment variables.
- Local config overrides: `application-local.*` (`.yml`, `.yaml`, `.properties`) and any other `*-local.*`.
- Certificate / keystore material: `*.pem`, `*.key`, `*.jks`, `*.p12`, `*.crt`.
- Inline secret values — passwords, OAuth client secrets, JWT signing keys, database URLs with embedded credentials, third-party API tokens — anywhere they appear (code, configuration, tests, fixtures, comments, commit messages, PR descriptions).

Only `*.example` templates are committed; they document expected variable **names** without real **values**.

If you realize a secret was about to be (or already was) staged or committed, **stop**. Do not push. Do not write a "fix" commit that deletes the file — the secret remains in history. Read the leak-response drill in ADR 000002 and follow it in order: rotate at the source first, then rewrite history with `git-filter-repo`, then force-push with `--force-with-lease`, then notify clone holders to re-clone.

Pre-commit hooks (`gitleaks`) and a CI job catch most accidents, but they are a secondary check. The primary defense is not putting the secret there in the first place.
