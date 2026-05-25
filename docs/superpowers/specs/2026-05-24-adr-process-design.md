# Design: ADR Process and Structure

**Date:** 2026-05-24
**Status:** Approved (pending implementation)

## Goal

Establish a lightweight, durable Architecture Decision Record (ADR) process for `rhystic-library-api` so that significant decisions are captured one-per-document, are easy for both humans and Claude to discover, and form a permanent, auditable history of how the system evolved.

## Scope

This spec covers:

- The directory layout, filename convention, and ID scheme for ADRs.
- The frontmatter schema (machine-readable) and the in-document table (human-readable).
- The required and optional body sections, based on MADR.
- Mutability rules and the status lifecycle.
- The `_template.md` and `_tags.md` companion files.
- README.md and CLAUDE.md updates to make ADRs discoverable.
- The content and self-references of the first ADR, which defines the process itself.

Out of scope: generating an ADR index page, automating supersedes/superseded-by linkage, or enforcing body immutability in CI (the last is hard to do robustly and is left as a convention for now). Those are future work and would each warrant their own ADRs.

## Location and File Conventions

- All ADRs live under `docs/adr/`.
- ADR filenames: `NNNNNN-kebab-slug.md`, where `NNNNNN` is a 6-digit zero-padded ID.
- IDs start at `000001`, are strictly sequential, and have **no gaps and no reuse** — even if an ADR is rejected or withdrawn, its number is burned.
- The slug is short kebab-case describing the decision (e.g., `000001-adr-process-and-structure.md`).
- Two underscore-prefixed companion files (the underscore is intentional so they sort first and are visually distinct from real ADRs):
  - `docs/adr/_template.md` — copy-paste skeleton for new ADRs.
  - `docs/adr/_tags.md` — alphabetically sorted list of allowed tags with one-line descriptions.

## One Decision Per ADR

Each ADR captures exactly one decision. If a single change touches two independent concerns, it gets two ADRs. Bundling makes future supersession painful (you can't supersede half a decision) and clouds the audit trail.

## Frontmatter (machine-readable)

Every ADR starts with a YAML frontmatter block. This is the canonical machine-readable representation; the in-document table is its human mirror.

```yaml
---
id: "000001"
name: adr-process-and-structure
description: Establishes the ADR process, file structure, and required sections.
status: Proposed
date-proposed: "2026-05-24"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [meta, process, documentation]
---
```

Field rules:

- `id` — quoted string to preserve the leading zeros (YAML would otherwise parse `000001` as integer `1`).
- `name` — kebab-case slug, must match the filename slug.
- `description` — one-sentence summary. Used by Claude when scanning frontmatter to decide which ADR to open.
- `status` — one of: `Proposed`, `Accepted`, `Deprecated`, `Superseded`.
- `date-proposed` — ISO-8601 date string (`YYYY-MM-DD`), quoted. Required from the moment the ADR is drafted.
- `date-accepted` — ISO-8601 date string, quoted; empty string `""` until the ADR is accepted.
- `date-invalidated` — ISO-8601 date string, quoted; the date the ADR transitioned to `Deprecated` or `Superseded`. Empty `""` while the ADR is still in force. One field covers both states because a single ADR cannot be both deprecated and superseded.
- `supersedes` — list of ADR IDs (strings) that this ADR replaces. Empty list when none.
- `superseded-by` — list of ADR IDs (strings) that replace this ADR. Empty list when none.
- `tags` — list of tags. Every tag MUST appear in `_tags.md`.

Dates are quoted strings (rather than YAML native dates) so the empty case is representable as `""` and so all tools parse them identically.

We reference superseded ADRs by **ID, not filename**, because IDs are immutable but slugs can in principle be renamed.

## Body Structure

Immediately after the frontmatter:

1. **H1 title** in the format `# ADR NNNNNN: Title in Title Case`.
2. **Human-readable key-value table** (key-value layout chosen over horizontal because seven columns is unreadable in a single row).
3. **MADR-style sections** in fixed order.

### Header table

```markdown
| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | 2026-05-24                           |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | meta, process, documentation         |
```

- Dates use ISO 8601 (`YYYY-MM-DD`).
- Empty fields render as an em-dash (`—`) so the row never visually collapses.
- `Date Invalidated` is populated when status flips to `Deprecated` or `Superseded`; it answers "when did we stop considering this decision in force?".
- Authors are bare names (no email, no GitHub handle), comma-separated when multiple.
- `Tags` lists tag slugs comma-separated.

### Sections (in this order)

| Section                          | Required? |
|----------------------------------|-----------|
| Context and Problem Statement    | Required  |
| Decision Drivers                 | Optional  |
| Considered Options               | Required  |
| Decision Outcome                 | Required  |
| Consequences                     | Required  |
| Pros and Cons of the Options     | Optional  |
| Links                            | Optional  |

Notes on the choices:

- **Considered Options is required** — without listed alternatives, an ADR collapses into "we did X" and loses the *why-not-Y* that gives ADRs long-term value. "Do nothing" is a valid option to list.
- **Decision Drivers, Pros/Cons, Links are optional** — for small decisions, forcing them produces padding. Authors include them when they add real value.
- **Links** captures external references (RFCs, docs, blog posts, tickets, PRs). Cross-references to other ADRs are already covered by `supersedes` / `superseded-by`.

## Status Lifecycle and Mutability

- `Proposed` — written but not yet merged to `main`. Free to edit during review.
- `Accepted` — the ADR commit is on the default branch (`main`). At this point the ADR body is **immutable**.
- `Deprecated` — the decision no longer applies but nothing has replaced it.
- `Superseded` — replaced by one or more newer ADRs; `superseded-by` is populated.

After acceptance, the only legal changes are metadata:

- Flipping `status` to `Deprecated` or `Superseded`.
- Populating `date-invalidated` with the date of the flip.
- Populating `superseded-by` (only when status becomes `Superseded`).
- Mirroring those changes in the header table.

Any substantive change requires a **new** ADR that supersedes the old one. This preserves a frozen historical record of what we believed at each point in time.

This implies a small workflow rule: the PR that introduces a new ADR must also flip its `status` from `Proposed` to `Accepted` and populate `Date Accepted` before merge. CI enforces this (see below).

## CI Validation

Two CI jobs run on every pull request and on pushes to `main`. Both must pass to merge.

### Job 1: `markdown-lint`

Standard Markdown lint over `**/*.md` (configurable exclusions). Catches malformed tables, inconsistent heading levels, broken link syntax, trailing whitespace, etc. Tool choice (e.g., `markdownlint-cli2`) and configuration file are an implementation detail; the spec only requires that some Markdown linter runs and blocks merge on failure.

### Job 2: `adr-validate`

A single custom validator script that walks `docs/adr/*.md` (excluding files whose names start with `_`) and enforces every ADR-specific rule. Implementation language is an implementation-plan detail; Python is a reasonable default since it needs no project dependencies and runs natively in standard CI runners.

The validator must check:

**Numbering**

- Every ADR filename matches `^[0-9]{6}-[a-z0-9-]+\.md$`.
- IDs are strictly sequential starting at `000001` — no gaps, no duplicates.
- The `id` field in the frontmatter matches the numeric prefix in the filename.
- The `name` field in the frontmatter matches the slug portion of the filename.

**Frontmatter schema**

- The file begins with a YAML block delimited by `^---$`.
- All required fields are present: `id`, `name`, `description`, `status`, `date-proposed`, `date-accepted`, `date-invalidated`, `supersedes`, `superseded-by`, `tags`.
- `id` is a quoted 6-digit string.
- `status` is one of: `Proposed`, `Accepted`, `Deprecated`, `Superseded`.
- `description` is a non-empty string.
- `date-proposed` is a quoted ISO-8601 date string (always required).
- `date-accepted` is a quoted ISO-8601 date string or empty (`""`).
- `date-invalidated` is a quoted ISO-8601 date string or empty (`""`).
- `supersedes` and `superseded-by` are lists of 6-digit ID strings (possibly empty); referenced IDs must exist in `docs/adr/`.
- `tags` is a non-empty list.

**Tag membership**

- Every tag in every ADR's `tags` list appears in `docs/adr/_tags.md`.

**Body structure**

- An H1 follows the frontmatter.
- A key-value header table follows the H1 with all eight fields present (`Status`, `Date Proposed`, `Date Accepted`, `Date Invalidated`, `Authors`, `Supersedes`, `Superseded By`, `Tags`).
- `Authors` is non-empty.
- All required sections are present as level-2 headings in the prescribed order: `Context and Problem Statement`, `Considered Options`, `Decision Outcome`, `Consequences`. Optional sections may appear in their prescribed positions but are not required.

**Frontmatter ↔ header table consistency**

The frontmatter is the canonical machine representation; the header table is its human mirror. The two MUST agree. The validator checks each pairing explicitly:

| Frontmatter field   | Header table row   | Comparison                                                                       |
|---------------------|--------------------|----------------------------------------------------------------------------------|
| `status`            | `Status`           | Exact string match (e.g. `Proposed` == `Proposed`).                              |
| `date-proposed`     | `Date Proposed`    | Same ISO-8601 date.                                                              |
| `date-accepted`     | `Date Accepted`    | Same ISO-8601 date, or empty frontmatter `""` ↔ table em-dash `—`.               |
| `date-invalidated`  | `Date Invalidated` | Same ISO-8601 date, or empty frontmatter `""` ↔ table em-dash `—`.               |
| `supersedes`        | `Supersedes`       | Same set of IDs (table renders comma-separated; empty list ↔ em-dash `—`).       |
| `superseded-by`     | `Superseded By`    | Same set of IDs (table renders comma-separated; empty list ↔ em-dash `—`).       |
| `tags`              | `Tags`             | Same set of tag slugs (table renders comma-separated).                           |

`Authors` lives only in the header table (it has no frontmatter counterpart and is exempt from this check). `id`, `name`, and `description` live only in frontmatter.

Any mismatch — e.g. `status: Proposed` in frontmatter but `Status | Accepted` in the table — fails the validator.

**Merge gate (status invariant)**

- For ADRs being introduced or modified in the change, `status` must be `Accepted`, `Deprecated`, or `Superseded`. `Proposed` is allowed during PR development but blocks merge.
- If `status` is `Accepted`, `Deprecated`, or `Superseded`, `date-accepted` must be a valid ISO-8601 date.
- If `status` is `Deprecated` or `Superseded`, `date-invalidated` must be a valid ISO-8601 date and must be on or after `date-accepted`.
- If `status` is `Proposed` or `Accepted`, `date-invalidated` must be empty.
- If `status` is `Superseded`, `superseded-by` must be non-empty.

The validator should produce clear, file-and-line-anchored error messages so authors can fix issues without re-running the script repeatedly.

## `_template.md`

A complete copy-paste skeleton with placeholders. Every required section is present and waiting to be filled in. Optional sections are present but flagged with an HTML comment so authors know they can delete them:

```markdown
<!-- optional: delete this section if it doesn't add value -->
```

The template should be runnable as-is: copy it, rename, fill in the placeholders, and you have a valid Proposed ADR.

## `_tags.md`

A short prologue followed by an alphabetically sorted bulleted list. Each entry is a bolded tag slug, an em-dash, and a one-line description.

```markdown
# Allowed ADR Tags

Every tag used in an ADR's frontmatter MUST appear in this list. Before introducing a new tag, add it here (alphabetically) with a short description.

- **documentation** — Decisions about docs, READMEs, comments, or written artifacts.
- **meta** — Decisions about the ADR process itself.
- **process** — Decisions about how work is done (workflow, conventions, ceremony).
```

The initial seed contains the three tags that ADR 000001 will use on itself. Future ADRs grow this list.

## README.md Changes

The current `README.md` is a single line. Replace it with a brief project description plus a short pointer section:

```markdown
## Architecture Decisions

Significant technical decisions are captured as Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/). Each ADR represents a single decision, is numbered sequentially (`NNNNNN-kebab-slug.md`), and is immutable once accepted — superseded decisions are replaced by newer ADRs rather than edited.

Start with [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md) to understand the process.
```

## Claude Skills

Three project-level skills under `.claude/skills/` carry the operational surface area for ADRs. Each skill is a `SKILL.md` describing when to invoke it and how, plus a `scripts/` directory of small helpers Claude calls via Bash rather than doing the work itself. The scripts exist for two reasons:

1. **Token efficiency** — reading every ADR file in full to answer "which ADRs are tagged `auth`?" is expensive. A 5-line script does it deterministically.
2. **Accuracy** — computing the next sequential ID, the alphabetical insertion point for a new tag, or parsing every frontmatter block is exactly the kind of work that benefits from a deterministic program rather than model judgement.

Implementation language for the scripts is a plan-level detail; **Python 3** is the recommended default since it has no project dependencies and runs uniformly on every CI runner and developer machine. Scripts read only frontmatter (not the body of each ADR) so output stays compact as the repo grows.

### Skill: `searching-adrs`

Invoked when Claude needs to find existing decisions by id, tag, status, or keyword.

Scripts:

- `scripts/list_adrs.py` — one line per ADR: id, status, tags, description. Default sort: id ascending. The "give me an overview" entry point.
- `scripts/find_adrs.py [--tag TAG] [--status STATUS] [--search KEYWORD]` — filter the list (filters AND together). `--search` matches against `name` and `description`. Output format matches `list_adrs.py`.
- `scripts/show_adr.py <id>` — print one ADR's frontmatter as JSON for fast structured consumption.

### Skill: `listing-adr-tags`

Invoked when Claude needs to discover allowed tags, either to pick tags for a new ADR or to survey topic areas.

Scripts:

- `scripts/list_tags.py` — print every tag and its description from `_tags.md`, one per line.
- `scripts/tag_usage.py` — for each tag, list the ADR ids that use it. Useful when finding decisions adjacent to a known topic.

### Skill: `creating-an-adr`

Invoked when Claude is authoring a new ADR end-to-end. The skill's `SKILL.md` walks through the full checklist: which sections are required, what to fill into the human table, when to flip status, and the immutability rule once merged.

Scripts:

- `scripts/new_adr.py <slug>` — compute the next sequential ID, copy `_template.md` to `docs/adr/<NNNNNN>-<slug>.md`, pre-fill `id`, `name`, and `date-proposed` (today's date), and print the new file path so Claude can immediately open it for editing.
- `scripts/add_tag.py <slug> "<description>"` — append a new tag to `_tags.md` at the correct alphabetical position. Convenience only; the validator catches bad ordering at PR time regardless.

## CLAUDE.md Changes

Create a new `CLAUDE.md` at the repo root with a short "## Architecture Decision Records" section that points at sources of truth rather than restating them. It contains only:

1. **Where ADRs live** — `docs/adr/`, with companion files `_template.md` and `_tags.md`.
2. **The canonical source of truth** — ADR [`000001-adr-process-and-structure.md`](docs/adr/000001-adr-process-and-structure.md). Includes the full process, structure, status lifecycle, and immutability rules.
3. **The three skills**, by location, with one sentence each on when to invoke them:
   - `.claude/skills/searching-adrs/` — when looking up existing decisions by id, tag, status, or keyword.
   - `.claude/skills/listing-adr-tags/` — when picking tags for a new ADR or surveying topic areas.
   - `.claude/skills/creating-an-adr/` — when authoring a new ADR.

CLAUDE.md deliberately does NOT embed grep examples, tag lists, or the creation checklist. Those live in the skills (and their scripts) so they can evolve without churning CLAUDE.md.

## ADR 000001 (the first ADR)

The first ADR is the meta-ADR that codifies everything in this spec. Specifically it will:

- Use ID `000001`, slug `adr-process-and-structure`, tags `[meta, process, documentation]`.
- Be created with `status: Proposed`, then flipped to `Accepted` once merged to `main`.
- In its body, explicitly link to both `_template.md` and `_tags.md` (in the Decision Outcome and/or Links sections) so any Claude session reading the ADR has a direct path to the artifacts it needs to author a new ADR.
- Use the full set of required sections, plus Links, so it doubles as a worked example.

## Implementation Checklist (preview)

The writing-plans skill will produce the detailed step ordering. At a glance, the work is:

1. Create `docs/adr/`.
2. Write `docs/adr/_tags.md` with the seed tags.
3. Write `docs/adr/_template.md`.
4. Write `docs/adr/000001-adr-process-and-structure.md` (this codifies the spec).
5. Update `README.md` with the project description and ADR pointer section.
6. Create `CLAUDE.md` with the slim pointer set (location + ADR 000001 + three skill paths).
7. Create the three project-level skills under `.claude/skills/` (`searching-adrs`, `listing-adr-tags`, `creating-an-adr`), each with a `SKILL.md` and the helper scripts described above.
8. Implement the `adr-validate` script and wire up the `markdown-lint` and `adr-validate` CI jobs.
9. Run both CI jobs locally against the new ADR (and exercise each skill's scripts) to confirm they pass before opening the PR.
10. Commit everything together so the rules, the artifacts that demonstrate them, the skills that operate on them, and the CI that enforces them all land in the same commit.
