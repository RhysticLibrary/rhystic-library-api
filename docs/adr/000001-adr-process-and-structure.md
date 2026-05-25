---
id: "000001"
name: adr-process-and-structure
description: Establishes the ADR process, file structure, required sections, and CI gates.
status: Accepted
date-proposed: "2026-05-24"
date-accepted: "2026-05-24"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [documentation, meta, process]
---

# ADR 000001: ADR Process and Structure

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Accepted                             |
| Date Proposed    | 2026-05-24                           |
| Date Accepted    | 2026-05-24                           |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | documentation, meta, process         |

## Context and Problem Statement

`rhystic-library-api` is a brand-new project. Significant technical decisions accumulate quickly in a project's first months — choices about libraries, schemas, deployment models, conventions, and trade-offs that future contributors (human and AI) need to understand to make consistent follow-on decisions. Without a deliberate record, the *why* behind those choices is lost to chat history and faulty memory within weeks.

We need a lightweight, durable Architecture Decision Record (ADR) process from day one — before the first non-trivial design choice — so the project's reasoning is captured as it happens rather than reconstructed later.

## Considered Options

- **No formal process; rely on commit messages and PR descriptions.** Cheap and zero-friction, but commit messages are rarely written for posterity and PR descriptions decay along with the PR UI.
- **Nygard-style minimal ADRs (Context / Decision / Consequences).** Three sections, very lean. Easy to write, but loses *alternatives considered*, which is the field most useful to future readers.
- **MADR-style rich ADRs** with explicit Considered Options, Decision Outcome, optional Decision Drivers / Pros-Cons / Links, plus a frontmatter mirror and a human header table. More structure; more friction per ADR; far better for audit and AI-assisted exploration.
- **Long-form architecture docs in a wiki.** Discoverable for humans but not version-controlled with the code, and substantially heavier per decision.

## Decision Outcome

We adopt the **MADR-style rich ADR** approach, with project-specific choices documented in this section.

### File layout

- All ADRs live in `docs/adr/`.
- Filename: `NNNNNN-kebab-slug.md` (6-digit zero-padded ID, no gaps, no reuse, starting at `000001`).
- Two companion files (underscore-prefixed to sort first and visually separate):
  - [`docs/adr/_template.md`](_template.md) — copy-paste skeleton for new ADRs.
  - [`docs/adr/_tags.md`](_tags.md) — alphabetical list of allowed tags.
- One decision per ADR — never bundle two independent concerns. Future supersession would otherwise be impossible to scope.

### Frontmatter (machine-readable)

Every ADR begins with a YAML frontmatter block:

```yaml
---
id: "NNNNNN"
name: kebab-slug
description: One-sentence summary.
status: Proposed | Accepted | Deprecated | Superseded
date-proposed: "YYYY-MM-DD"
date-accepted: "YYYY-MM-DD"  # or "" until accepted
date-invalidated: ""          # set when status flips to Deprecated/Superseded
supersedes: ["NNNNNN", ...]   # list of ADR IDs; [] when none
superseded-by: ["NNNNNN", ...]
tags: [tag1, tag2]            # every tag must appear in _tags.md
---
```

Dates are quoted ISO-8601 strings; the empty case is `""` so all tools parse them identically. ADR cross-references use **IDs, not filenames**, since IDs are immutable but slugs can in principle be renamed.

### Body structure

An H1 follows the frontmatter, then a human-readable key-value table mirroring the frontmatter, then MADR-style sections in fixed order:

| Section                          | Required? |
|----------------------------------|-----------|
| Context and Problem Statement    | Required  |
| Decision Drivers                 | Optional  |
| Considered Options               | Required  |
| Decision Outcome                 | Required  |
| Consequences                     | Required  |
| Pros and Cons of the Options     | Optional  |
| Links                            | Optional  |

The header table has eight rows (`Status`, `Date Proposed`, `Date Accepted`, `Date Invalidated`, `Authors`, `Supersedes`, `Superseded By`, `Tags`). Empty values render as em-dash (`—`). Authors are bare names, comma-separated. Dates are ISO 8601.

### Status lifecycle and mutability

- `Proposed` — written but not yet merged to `main`. Free to edit during PR review.
- `Accepted` — the ADR commit is on `main`. From this point the body is **immutable**.
- `Deprecated` — the decision no longer applies; nothing replaces it. Set `date-invalidated`.
- `Superseded` — replaced by one or more newer ADRs; populate `superseded-by` and `date-invalidated`.

After acceptance, the only legal changes are metadata (status flip, `date-invalidated`, `superseded-by`, and mirroring those in the header table). Any substantive change requires a new ADR that supersedes the old.

The PR that introduces a new ADR must flip `Proposed` → `Accepted` and populate `Date Accepted` before merge. CI enforces this via the merge gate (see below).

### Tags

Every tag in an ADR's `tags` list MUST appear in [`_tags.md`](_tags.md). To introduce a new tag, add it to `_tags.md` (alphabetically, with a one-line description) in the same change that uses it. The skill `creating-an-adr` ships a helper script `add_tag.py` that does this automatically.

### CI validation

Two CI jobs (see `.github/workflows/ci.yml`) gate every PR and every push to `main`:

- **`markdown-lint`** — standard Markdown linter (`markdownlint-cli2`) over `**/*.md`.
- **`adr-validate`** — custom Python validator at `tools/adr/validate.py`. Run locally via `python tools/adr/validate.py`; CI runs it with `--merge-gate` to enforce the status invariants. The validator checks:
  - **Numbering** — filenames match `NNNNNN-kebab.md`, IDs sequential with no gaps or duplicates, frontmatter `id`/`name` match the filename.
  - **Frontmatter schema** — all required fields present, types correct, status in allowed set, dates ISO-8601, referenced ADR IDs exist.
  - **Tag membership** — every tag is in `_tags.md`.
  - **Body structure** — H1 present, header table present with all eight rows, Authors non-empty, all four required sections present.
  - **Frontmatter ↔ header table consistency** — every paired field matches (with empty string ↔ em-dash equivalence for dates, list ↔ comma-joined equivalence for tags/supersedes).
  - **Merge gate** (only with `--merge-gate`) — status must be Accepted/Deprecated/Superseded; date-accepted required for any of those; date-invalidated required and on-or-after date-accepted for Deprecated/Superseded; date-invalidated must be empty for Proposed/Accepted; Superseded requires non-empty `superseded-by`.

### Claude skills

Three project-level skills under `.claude/skills/` provide Claude operational entry points for the ADR system. Each `SKILL.md` documents when to invoke and what scripts to call; the scripts live in `tools/adr/` and are written in Python:

- [`.claude/skills/searching-adrs/`](../../.claude/skills/searching-adrs/SKILL.md) — `list_adrs.py`, `find_adrs.py`, `show_adr.py`.
- [`.claude/skills/listing-adr-tags/`](../../.claude/skills/listing-adr-tags/SKILL.md) — `list_tags.py`, `tag_usage.py`.
- [`.claude/skills/creating-an-adr/`](../../.claude/skills/creating-an-adr/SKILL.md) — `new_adr.py`, `add_tag.py`.

Scripts read only frontmatter (never bodies), keeping output token-efficient even as the corpus grows.

### Bootstrap quirk for this ADR

This is the very first ADR. Per the lifecycle rule, "Accepted" means *committed to main*. The strict reading of that rule would block this ADR from ever being merged, since CI requires `Accepted` status to merge. We resolve the chicken-and-egg by giving this single bootstrap ADR `status: Accepted` from its introducing commit. Every subsequent ADR follows the normal flow: `Proposed` during development, flipped to `Accepted` immediately before merge.

## Consequences

- **Positive**
  - Every significant decision has a frozen, versioned record with rationale and considered alternatives.
  - Frontmatter makes ADRs scriptable; the skills + helper scripts give Claude precise, low-token discovery and authoring tools.
  - CI catches structural drift (missing sections, unknown tags, gap in numbering) before merge, removing review burden.
  - The one-decision-per-ADR rule keeps supersession clean and scoped.
- **Negative**
  - Each significant decision now requires writing an ADR — non-trivial friction for small calls. Authors must judge the bar (the skill `creating-an-adr` is the place to document that bar over time).
  - Two CI jobs add a small but non-zero PR latency.
  - The validator and skill scripts are project-owned code that must be maintained alongside the codebase proper.

## Links

- Design spec: [`docs/superpowers/specs/2026-05-24-adr-process-design.md`](../superpowers/specs/2026-05-24-adr-process-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-05-24-adr-process.md`](../superpowers/plans/2026-05-24-adr-process.md)
- MADR (Markdown Architecture Decision Records): <https://adr.github.io/madr/>
- Michael Nygard's original ADR post: <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
