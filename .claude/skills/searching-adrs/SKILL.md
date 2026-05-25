---
name: searching-adrs
description: Use when looking up existing Architecture Decision Records by id, tag, status, or keyword. Use this BEFORE making a design choice that may already have a recorded decision.
---

# Searching ADRs

All ADRs live under `docs/adr/` as `NNNNNN-kebab-slug.md`. Prefer the scripts below over reading files directly — they parse only frontmatter, so they stay cheap as the corpus grows. The first ADR ([`000001-adr-process-and-structure.md`](../../../docs/adr/000001-adr-process-and-structure.md)) is the source of truth for the process.

Run scripts from the repo root.

## When to use

- Before proposing a design or implementation that touches an area likely to have prior decisions.
- When asked "why does this codebase do X?" — there may be an ADR explaining it.
- When triaging deprecated/superseded ADRs.

## Scripts

### Overview of all ADRs

```bash
python tools/adr/list_adrs.py
```

Prints one line per ADR sorted by ID: `<id>\t<status>\t[<tags>]\t<description>`. Use this as the entry point when scanning.

### Filtered lookup

```bash
python tools/adr/find_adrs.py [--tag TAG] [--status STATUS] [--search KEYWORD]
```

Filters AND together. `--search` does case-insensitive substring match against `name` and `description`. Useful examples:

- Find all process decisions: `--tag process`
- Find every still-in-force ADR: `--status Accepted`
- Find ADRs about logging: `--search logging`

### Read a single ADR's frontmatter

```bash
python tools/adr/show_adr.py <id>
```

Where `<id>` is the 6-digit ID (e.g. `000001`). Outputs JSON. Use this to inspect supersedes/superseded-by relationships, status, or full tag list. Read the file directly with the `Read` tool when you need the body.

## Falling back to direct reads

When you've identified the candidate ADR(s), read the full file with the `Read` tool to get context, decision, consequences, and links.
