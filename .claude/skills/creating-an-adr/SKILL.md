---
name: creating-an-adr
description: Use when authoring a new Architecture Decision Record. Walks through the full creation flow — scaffold, fill, validate, flip status, merge — and ensures the new ADR conforms to ADR 000001.
---

# Creating an ADR

All ADRs live under `docs/adr/`. The first ADR ([`000001-adr-process-and-structure.md`](../../../docs/adr/000001-adr-process-and-structure.md)) is the canonical source of truth — every rule below comes from there.

Run scripts from the repo root.

## When to use

- A non-trivial design choice that future contributors will need to understand.
- A change in conventions, workflow, tools, or constraints that affects how code is written.
- A reversal or refinement of an earlier decision (write a new ADR; supersede the old).

Not every change needs an ADR. If a future contributor would shrug at the choice, skip the ADR.

## End-to-end flow

1. **Pick (or add) tags.** Use the `listing-adr-tags` skill to see what's available. If you need a new tag, run:
   ```bash
   python tools/adr/add_tag.py <slug> "Short description."
   ```
2. **Scaffold the ADR.** Choose a kebab-slug that captures the decision:
   ```bash
   python tools/adr/new_adr.py <slug>
   ```
   This computes the next sequential ID, copies [`docs/adr/_template.md`](../../../docs/adr/_template.md) to `docs/adr/<id>-<slug>.md`, pre-fills `id`, `name`, and `date-proposed` (today), and prints the new path.
3. **Fill in the ADR.** Open the file. Required sections (NEVER delete):
   - `## Context and Problem Statement`
   - `## Considered Options`
   - `## Decision Outcome`
   - `## Consequences`

   Optional sections (delete if they don't add value):
   - `## Decision Drivers`
   - `## Pros and Cons of the Options`
   - `## Links`

   Also fill the header table: Authors, Tags, and update Status (still `Proposed` at this point).

4. **Keep frontmatter and table in sync.** The validator checks every paired field. Whenever you change a status, date, tag, or supersedes value in one, mirror it in the other.

5. **Validate locally** during iteration:
   ```bash
   python tools/adr/validate.py
   ```
   Drops the merge-gate check so `Proposed` doesn't fail. Fix every error before opening the PR.

6. **Flip to Accepted before merge.** Just before the PR merges, change:
   - Frontmatter: `status: Accepted`, `date-accepted: "YYYY-MM-DD"`.
   - Header table: `Status | Accepted`, `Date Accepted | YYYY-MM-DD`.

   Then run the merge-gate validator:
   ```bash
   python tools/adr/validate.py --merge-gate
   ```
   Must exit 0.

7. **Merge.** CI runs the merge-gate validator + markdown lint and gates the merge.

## Mutability after merge

Once an ADR is on `main`, the body is **immutable**. The only legal edits are metadata: flipping `status` to `Deprecated` or `Superseded`, populating `date-invalidated`, populating `superseded-by`. Mirror those in the header table.

To change a decision, write a new ADR that supersedes the old.

## Superseding an existing ADR

1. Scaffold a new ADR as above.
2. In its frontmatter, set `supersedes: ["<old-id>"]` and mirror in the table.
3. In a separate commit (or the same PR), edit the superseded ADR:
   - Frontmatter: `status: Superseded`, `date-invalidated: "<today>"`, `superseded-by: ["<new-id>"]`.
   - Header table: same three fields.
   - Body unchanged.
