---
name: listing-adr-tags
description: Use when picking tags for a new ADR or surveying which topics already have decisions recorded. Always check before assigning a tag — unknown tags fail CI.
---

# Listing ADR Tags

Allowed tags live in [`docs/adr/_tags.md`](../../../docs/adr/_tags.md). Every tag used in an ADR's frontmatter MUST appear there. Adding a tag that isn't in `_tags.md` fails the `adr-validate` CI job.

Run scripts from the repo root.

## When to use

- Before writing the `tags:` field on a new ADR.
- When deciding whether to introduce a new tag vs reuse an existing one.
- When surveying which areas of the system already have recorded decisions.

## Scripts

### List every allowed tag with its description

```bash
python tools/adr/list_tags.py
```

Output: `<tag>\t<description>`, one per line, alphabetical.

### See which ADRs use each tag

```bash
python tools/adr/tag_usage.py
```

Output: `<tag>\t<id1>,<id2>,...`, one per line, alphabetical. Tags with zero ADRs appear with an empty list — that's useful for spotting stale tags.

## Adding a new tag

If no existing tag fits, add a new one with the `creating-an-adr` skill's `add_tag.py` script (inserts alphabetically and idempotently). Then use it in your ADR's `tags:` field.
