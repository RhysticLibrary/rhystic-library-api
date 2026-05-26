# Secrets-in-Version-Control ADR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land ADR `000002-secrets-in-version-control` and wire its enforcement: a `gitleaks` pre-commit hook, a `.gitignore` broadened to cover `*-local.*`, and a blunt, inline no-secrets section in `CLAUDE.md` citing the new ADR.

**Architecture:** This is a policy ADR with light tooling work. The ADR file is scaffolded and validated using the existing `tools/adr/` helpers (`new_adr.py`, `add_tag.py`, `validate.py`) per ADR 000001's process. The pre-commit hook layers on the framework already in `.pre-commit-config.yaml`. The CI `gitleaks` job already exists in `.github/workflows/ci.yml`; this plan does not modify it but does add a final manual step to confirm it is a required check in branch protection.

**Tech Stack:** Python 3 (existing ADR helpers), pre-commit framework, gitleaks (`gitleaks/gitleaks` upstream pre-commit hook + `gitleaks/gitleaks-action@v2` already in CI).

**Spec:** `docs/superpowers/specs/2026-05-25-secrets-policy-design.md`

**Branch:** `adr-secrets-policy` (already created; spec already committed at `a9a3e8c`).

---

## File Structure

```text
docs/adr/
  _tags.md                                  # add `security` tag (via add_tag.py)
  000002-secrets-in-version-control.md      # NEW — scaffolded by new_adr.py, body filled by hand

.gitignore                                  # broaden to cover *-local.*
.pre-commit-config.yaml                     # add gitleaks hook
CLAUDE.md                                   # add inline blunt no-secrets section citing ADR 000002
```

**Responsibilities:**

- `_tags.md` — alphabetical list of allowed ADR tags. Modified only via `add_tag.py` so the insertion point and frontmatter stay valid.
- `000002-secrets-in-version-control.md` — the policy ADR; structure is fixed by ADR 000001 (frontmatter + header table + four required sections).
- `.gitignore` — repo-wide ignore patterns; the secrets section is the source of truth for which file types are blocked at the Git layer.
- `.pre-commit-config.yaml` — local enforcement; gitleaks runs on staged changes before each commit.
- `CLAUDE.md` — always-loaded project instructions for Claude. The no-secrets rule lives here in blunt, inline form so enforcement does not depend on the ADR being loaded.

**No code (Python source) changes.** The "tests" for this work are:
- `python3 tools/adr/validate.py` — ADR structural integrity while iterating (Proposed-tolerant).
- `python3 tools/adr/validate.py --merge-gate` — ADR merge gate (requires Accepted + date-accepted).
- `pre-commit run --all-files` — confirms the new gitleaks hook installs and the repo is clean.
- CI on the PR — runs `gitleaks-action@v2` plus the validator and markdown lint.

---

## Tasks

### Task 1: Add the `security` tag

The ADR's frontmatter will declare `tags: [security, process]`. The `process` tag already exists in `_tags.md`; `security` does not. The validator fails on any unknown tag, so the tag must exist before the ADR file is added.

**Files:**
- Modify: `docs/adr/_tags.md` (via helper script)

- [ ] **Step 1: Add the tag via `add_tag.py`**

Run from repo root:

```bash
python3 tools/adr/add_tag.py security "Decisions about security posture, secrets handling, and threat-model trade-offs."
```

The script inserts the tag at the correct alphabetical position and preserves the file's existing format.

- [ ] **Step 2: Verify the tag landed and the file still parses**

```bash
git diff docs/adr/_tags.md
```

Expected: a single new bullet line `- **security** — Decisions about security posture, secrets handling, and threat-model trade-offs.` inserted between `process` and the end of the list (or wherever alphabetical order dictates — `security` sorts after `process`).

```bash
python3 tools/adr/validate.py
```

Expected: exits 0 (no ADR yet references the tag, but the tag list itself parses).

- [ ] **Step 3: Commit**

```bash
git add docs/adr/_tags.md
git commit -m "$(cat <<'EOF'
Add `security` ADR tag

Introduced for the secrets-in-version-control ADR. Future
security-posture decisions will reuse this tag.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Scaffold the ADR file

Use `new_adr.py` to copy `_template.md` into `docs/adr/<next-id>-secrets-in-version-control.md` with `id`, `name`, and `date-proposed` pre-filled. **Do not copy `_template.md` by hand** — the script keeps the ID sequence correct and avoids transcription errors.

**Files:**
- Create: `docs/adr/000002-secrets-in-version-control.md` (ID assigned by `new_adr.py`; expected to be `000002` since only `000001` exists)

- [ ] **Step 1: Scaffold via `new_adr.py`**

```bash
python3 tools/adr/new_adr.py secrets-in-version-control
```

Expected stdout: a line printing the new file path, e.g. `docs/adr/000002-secrets-in-version-control.md`.

- [ ] **Step 2: Verify the scaffold**

```bash
ls docs/adr/
```

Expected: a new file `000002-secrets-in-version-control.md` appears alongside `000001-adr-process-and-structure.md`.

```bash
head -15 docs/adr/000002-secrets-in-version-control.md
```

Expected: frontmatter with `id: "000002"`, `name: secrets-in-version-control`, `date-proposed: "2026-05-25"`, `status: Proposed`. (If the printed ID differs because more ADRs have landed in the meantime, substitute that ID in every subsequent step.)

- [ ] **Step 3: Do not commit yet** — the file still contains `TODO` placeholders from the template and will fail the validator. Task 3 fills the body, and the scaffold + body land in one commit.

---

### Task 3: Fill the ADR body

Replace every `TODO` from the template with the content from the spec (`docs/superpowers/specs/2026-05-25-secrets-policy-design.md`). The ADR is the canonical decision record; the spec is its design brief. Status stays `Proposed` until Task 7.

**Files:**
- Modify: `docs/adr/000002-secrets-in-version-control.md`

- [ ] **Step 1: Update frontmatter**

Open `docs/adr/000002-secrets-in-version-control.md` and edit the frontmatter to:

```yaml
---
id: "000002"
name: secrets-in-version-control
description: Forbids committing secrets, enumerates the file types and inline-value forms covered, names the runtime model and leak-response drill, and pins gitleaks as the defense-in-depth enforcement.
status: Proposed
date-proposed: "2026-05-25"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [security, process]
---
```

- [ ] **Step 2: Update the header table**

Replace the H1 and header table with:

```markdown
# ADR 000002: Secrets in Version Control

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | 2026-05-25                           |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | security, process                    |
```

- [ ] **Step 3: Fill `## Context and Problem Statement`**

Replace the section with:

```markdown
## Context and Problem Statement

The project will soon accumulate runtime dependencies that require secrets — database credentials, third-party API tokens, OAuth client secrets, JWT signing keys, certificates. Once a secret reaches Git history it must be treated as compromised: clones, mirrors, CI caches, and GitHub's search index distribute it beyond our reach within seconds. We need a project-wide rule that secrets never enter the repo, an enumerated definition of "secret" so the rule is unambiguous at review time, a runtime model that makes following the rule the path of least resistance, an enforcement mechanism that catches mistakes before they propagate, and a written response drill so an incident does not require improvisation.
```

- [ ] **Step 4: Delete the optional `## Decision Drivers` section**

Per the template comment ("optional: delete this section if it doesn't add value"), remove the entire `## Decision Drivers` block. The Context section already conveys the drivers narratively.

- [ ] **Step 5: Fill `## Considered Options`**

Replace with:

```markdown
## Considered Options

Approach:

- **No formal rule; rely on reviewer vigilance and `.gitignore`.** Cheapest. Fails the first time a file type slips past `.gitignore` and a reviewer is rushed. No drill for the inevitable leak.
- **Policy without tooling.** Write the rule, no scanner. Aligns expectations but every enforcement is a human catching a human. Doesn't survive contact with AI-authored commits that don't know the rule exists.
- **Pre-commit scanner only.** Catches most accidents at the developer's machine. Bypassable on `--no-verify`, uninstalled hooks, or fresh clones — a comfort layer, not a gate.
- **CI scanner only.** Unbypassable, but the secret has already reached the remote by the time CI runs — every accident triggers a rotation drill. Wastes the cheap local-catch opportunity.
- **Policy + pre-commit + CI scanner with named tooling and a written leak-response drill.** *(Chosen.)* Defense in depth: pre-commit makes the easy path the safe path; CI is the gate that catches missed hooks; the drill removes ambiguity in an incident.

Scanner:

- **`gitleaks`.** *(Chosen.)* Single Go binary. First-class pre-commit hook and GitHub Action (already wired in CI). Mature rule set. No SaaS dependency. No new language ecosystem in the repo.
- **`trufflehog`.** Strong verified-scanning (actively checks tokens against live providers). Heavier; verification step is slower.
- **`detect-secrets`.** Best baseline-file workflow for grandfathering false positives. Strong fit only if we had legacy history to baseline — we don't.
- **`ggshield` (GitGuardian).** Strongest detection corpus, but SaaS-backed; requires a GitGuardian account and API key in CI. Adds an external service dependency to the security path.

History-rewrite tool for the leak-response drill:

- **`git-filter-repo`.** *(Chosen as preferred.)* Upstream-recommended replacement for the deprecated `git filter-branch`. Precise and well-documented.
- **`bfg-repo-cleaner`.** Acceptable for very large repos where filter-repo is too slow. Less precise.
- **Tool-agnostic ("use whatever").** Rejected — in the heat of an incident, a named tool removes a decision.
```

- [ ] **Step 6: Fill `## Decision Outcome`**

Replace with:

```markdown
## Decision Outcome

### The rule

No credential, API key, token, certificate, or local environment file is committed to this repository, ever. The rule binds humans and AI agents equally; AI agents inherit it through CLAUDE.md.

### What counts as a secret (enumerated, non-exhaustive)

- **Environment files**: `.env`, `.env.*`, and any file the local toolchain reads from disk to populate environment variables.
- **Local config overrides**: `application-local.*` (`.yml`, `.yaml`, `.properties`) and any other `*-local.*`.
- **Certificate / keystore material**: `*.pem`, `*.key`, `*.jks`, `*.p12`, `*.crt`.
- **Inline secret values**: passwords, OAuth client secrets, JWT signing keys, database URLs with embedded credentials, third-party API tokens — anywhere they appear, including code, configuration, tests, fixtures, comments, commit messages, and PR descriptions.

The enumeration is non-exhaustive. A new secret-bearing file type means extending `.gitignore`; "I'll just be careful this once" is not an exception.

### Runtime model

Secrets load at runtime from environment variables or a managed secret store. The specific store is out of scope for this ADR and will be decided when infrastructure lands. Only `*.example` templates are committed — they document expected variable **names** without real **values**.

### Enforcement (defense in depth)

- **`.gitignore`** carries the patterns from the enumeration above.
- **Pre-commit hook**: `gitleaks` runs via the existing pre-commit framework on the staged diff. Blocks the commit on a finding. Fast feedback at developer velocity.
- **CI job**: the existing `gitleaks` job in `.github/workflows/ci.yml` runs on every pull request and every push to `main`. This ADR ratifies it as a required check in branch protection — the unbypassable gate.
- **CLAUDE.md**: states the no-secrets rule inline and bluntly — the enumerated file types and inline-value forms repeated explicitly — and cites this ADR as the ratifying source. The rule is enforceable from CLAUDE.md alone, without relying on the model deciding to read the ADR mid-edit.

### Leak-response drill

If a secret is committed — even briefly, even on a feature branch, even before push — treat it as compromised. CI caches, mirrors, and clones distribute it within seconds. The order is non-negotiable:

1. **Rotate the secret immediately** at its source (provider console, secret store, etc.). Assume a third party already has the committed value.
2. **Remove from history** with `git-filter-repo` (preferred). `bfg-repo-cleaner` is acceptable for very large repos where filter-repo is too slow. Do **not** rely on `git rm` in a follow-up commit — the secret remains in history and in every consumer's cache.
3. **Force-push the cleaned branch** with `--force-with-lease`.
4. **Notify** anyone with a clone: they must re-clone, not pull.
```

- [ ] **Step 7: Fill `## Consequences`**

Replace with:

```markdown
## Consequences

- **Positive**
  - One unambiguous rule that humans and AI agents can apply at edit time.
  - Defense in depth: pre-commit catches the easy cases at dev velocity; CI catches the bypassed cases at gate velocity.
  - `gitleaks` is a single binary, no SaaS dependency, no new language ecosystem in the repo.
  - The leak-response drill removes decision-making from an incident — the order is written and the tool is named.
  - CLAUDE.md statement makes the rule load-bearing for every Claude session without depending on ADR discovery.
- **Negative**
  - Two scan layers add small but non-zero latency: a few seconds on `git commit`, a CI job on every PR.
  - `gitleaks` false positives will happen (high-entropy strings, sample tokens in tests). The cost is a tuned allowlist file plus the discipline to actually tune it rather than disable the scan.
  - Forward-only enforcement means any pre-existing leak in history is unaddressed. Acceptable here (repo is days old, verified clean) but would need a separate remediation effort on an older codebase.
  - A managed secret store is out of scope; until that's decided, "runtime secret loading" means environment variables in practice. A follow-up ADR is implied once infrastructure lands.
```

- [ ] **Step 8: Delete the optional `## Pros and Cons of the Options` section**

Per the template comment, remove the entire block. Considered Options already lists the trade-offs inline.

- [ ] **Step 9: Fill `## Links`**

Replace with:

```markdown
## Links

- Design spec: [`docs/superpowers/specs/2026-05-25-secrets-policy-design.md`](../superpowers/specs/2026-05-25-secrets-policy-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-05-25-secrets-policy.md`](../superpowers/plans/2026-05-25-secrets-policy.md)
- ADR 000001 — ADR Process and Structure: [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md)
- `gitleaks`: <https://github.com/gitleaks/gitleaks>
- `git-filter-repo`: <https://github.com/newren/git-filter-repo>
```

- [ ] **Step 10: Run the validator (no merge gate)**

```bash
python3 tools/adr/validate.py
```

Expected: exits 0. The validator checks numbering, frontmatter schema, tag membership, body structure, and frontmatter↔table consistency. It tolerates `Proposed` because `--merge-gate` is not set.

If it errors, fix the reported issue and re-run before moving on. Common pitfalls:
- Header table values that don't match frontmatter (e.g., tags in a different order).
- An accidental missing required section header.
- A typo in a section heading (must match exactly: `## Context and Problem Statement`, etc.).

- [ ] **Step 11: Commit**

```bash
git add docs/adr/000002-secrets-in-version-control.md
git commit -m "$(cat <<'EOF'
Add ADR 000002: secrets in version control

Records the no-secrets-in-VCS rule, the enumerated file types and
inline-value forms it covers, the runtime model (env vars or
managed secret store; only *.example templates committed), the
defense-in-depth enforcement (gitleaks pre-commit + existing CI
job + CLAUDE.md), and the rotate-then-rewrite leak-response drill.

Status remains Proposed; flipped to Accepted in a later commit
once enforcement is wired and the merge gate is ready.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Broaden `.gitignore` to cover `*-local.*`

The ADR enumerates `application-local.*` **and any other `*-local.*`**. The current `.gitignore` only lists the Spring-specific case. Add the broader pattern (and the `!*-local.example` re-include so template files can still be committed).

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Inspect the current state**

```bash
grep -n "local" .gitignore
```

Expected current matches:
- A line `application-local.*` under a `# === Spring Boot local config ===` header.

(The existing `.env*` + `!.env.example` lines under `# === Environment and secrets ===` are already correct and need no changes.)

- [ ] **Step 2: Add the broader `*-local.*` pattern**

Edit `.gitignore`. Under the existing `# === Environment and secrets ===` section, after the `*.crt` line, add:

```gitignore
*-local.*
!*-local.example
```

Leave the existing `application-local.*` line in place under its `# === Spring Boot local config ===` header — keep the contextual header for future readers, even though it is now technically redundant with the broader pattern.

- [ ] **Step 3: Verify the diff**

```bash
git diff .gitignore
```

Expected: two added lines (`*-local.*` and `!*-local.example`) under the secrets section. No other changes.

- [ ] **Step 4: Confirm no currently-tracked file is now ignored**

```bash
git check-ignore -v $(git ls-files) 2>/dev/null
```

Expected: empty output. (Any tracked file that newly matches an ignore pattern would still be tracked but should be flagged for review. In this repo there are no `*-local.*` files committed today.)

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "$(cat <<'EOF'
Broaden .gitignore to cover *-local.* per ADR 000002

The ADR's enumeration of secret-bearing file types includes any
*-local.* file, not just Spring Boot's application-local.*. The
matching *.example re-include keeps template files committable.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Add the gitleaks pre-commit hook

Pre-commit hook scans staged changes only (`gitleaks protect --staged` semantics), which is fast enough to run on every commit. The CI job continues to do full-history scans.

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Add the gitleaks repo block**

Open `.pre-commit-config.yaml`. After the existing `markdownlint-cli2` block and **before** the `repo: local` block (so external repos stay grouped together), add:

```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.0.0  # placeholder; bumped to latest by `pre-commit autoupdate` in the next step
    hooks:
      - id: gitleaks
```

- [ ] **Step 2: Bump to the latest stable rev**

```bash
pre-commit autoupdate --repo https://github.com/gitleaks/gitleaks
```

Expected: the `rev:` placeholder is replaced with the latest stable tag (e.g. `v8.27.2` or later — whatever the upstream release is at run time). Confirm with:

```bash
grep -A1 "gitleaks/gitleaks" .pre-commit-config.yaml
```

- [ ] **Step 3: Install the hook and run it against the whole repo**

```bash
pre-commit install
pre-commit run gitleaks --all-files
```

Expected: `Passed` for the gitleaks hook. The repo is days old and inspected clean; the scan should find no leaks.

If gitleaks reports findings, **stop and investigate before continuing**. Do not commit and do not add allowlist entries to suppress real findings — work the leak-response drill from the ADR (rotate, rewrite history, force-push, notify).

If the findings are clearly false positives (e.g., a fixture string in test data), add a targeted entry to a new `.gitleaks.toml` allowlist at the repo root and re-run. The spec's default is "no project allowlist file unless justified"; this is the justification point.

- [ ] **Step 4: Verify the hook fires on a synthetic leak**

This is a one-time check that the wiring works. Do **not** commit the test secret.

```bash
echo 'AWS_SECRET_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE/wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"' > /tmp/fake-secret.txt
git add /tmp/fake-secret.txt 2>/dev/null || true
# Stage a real file change in the repo (e.g., an extra newline in a scratch file) to trigger pre-commit;
# OR run gitleaks directly:
gitleaks protect --staged --no-banner --redact 2>&1 || echo "exit: $?"
rm /tmp/fake-secret.txt
```

Expected: gitleaks reports a finding (non-zero exit). This confirms the binary is installed and configured. If `gitleaks` is not on PATH, the pre-commit hook still works (the framework manages the binary) — this verification step can be skipped, but `pre-commit run gitleaks --all-files` from Step 3 is sufficient on its own.

- [ ] **Step 5: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "$(cat <<'EOF'
Add gitleaks pre-commit hook per ADR 000002

Layers a fast staged-diff scan on top of the existing CI gitleaks
job, giving developers feedback at commit time before secrets
reach the remote.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Update CLAUDE.md with the inline no-secrets rule

CLAUDE.md is always loaded into the session context; ADRs are not. The rule must be enforceable from CLAUDE.md alone, in blunt explicit terms — not a "see ADR X" pointer.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the new section**

Open `CLAUDE.md`. After the existing `## Architecture Decision Records` section (which ends with the line about helper scripts), append:

```markdown

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
```

- [ ] **Step 2: Verify the diff**

```bash
git diff CLAUDE.md
```

Expected: only the new section appended below the existing `## Architecture Decision Records` block. No other changes.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
Add inline no-secrets rule to CLAUDE.md citing ADR 000002

CLAUDE.md is always loaded; ADRs are not. The rule must be
enforceable from CLAUDE.md alone, in blunt explicit terms, so
Claude sessions honor it without needing to discover the ADR
mid-edit.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Flip the ADR to Accepted and run the merge gate

Per ADR 000001, the PR that introduces a new ADR must flip status `Proposed` → `Accepted` and populate `date-accepted` before merge. CI runs `validate.py --merge-gate` and will block the merge otherwise.

**Files:**
- Modify: `docs/adr/000002-secrets-in-version-control.md` (metadata only)

- [ ] **Step 1: Update frontmatter**

In `docs/adr/000002-secrets-in-version-control.md`, change:

```yaml
status: Proposed
date-accepted: ""
```

to:

```yaml
status: Accepted
date-accepted: "2026-05-25"
```

- [ ] **Step 2: Update the header table to match**

Change the two corresponding rows:

```markdown
| Status           | Proposed                             |
| Date Proposed    | 2026-05-25                           |
| Date Accepted    | —                                    |
```

to:

```markdown
| Status           | Accepted                             |
| Date Proposed    | 2026-05-25                           |
| Date Accepted    | 2026-05-25                           |
```

- [ ] **Step 3: Run the merge-gate validator**

```bash
python3 tools/adr/validate.py --merge-gate
```

Expected: exits 0. The merge gate checks that status is `Accepted/Deprecated/Superseded`, `date-accepted` is populated, `date-invalidated` is empty for `Proposed/Accepted`, and `superseded-by` is non-empty only for `Superseded`. All those should hold.

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000002-secrets-in-version-control.md
git commit -m "$(cat <<'EOF'
Flip ADR 000002 to Accepted

Status: Accepted. Date Accepted: 2026-05-25. Merge-gate validator
passes locally.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Open the PR

The branch `adr-secrets-policy` now contains the spec, the security tag, the ADR, the .gitignore broadening, the gitleaks pre-commit hook, the CLAUDE.md update, and the Proposed→Accepted flip.

- [ ] **Step 1: Final local check — all pre-commit hooks against all files**

```bash
pre-commit run --all-files
```

Expected: every hook passes. If the gitleaks hook reports a finding, work the leak-response drill from the ADR; do not push. If markdownlint or ruff fails, fix and amend the relevant commit (do not amend Accepted-status commits if pre-commit reformats them — the ADR body is mutable until merge).

- [ ] **Step 2: Push the branch**

```bash
git push -u origin adr-secrets-policy
```

- [ ] **Step 3: Open the PR**

```bash
gh pr create --title "Add ADR 000002: secrets in version control" --body "$(cat <<'EOF'
## Summary

- Adds ADR 000002 forbidding secrets in version control, with an enumerated definition, runtime model, defense-in-depth enforcement, and a rotate-then-rewrite leak-response drill.
- Adds a `security` tag to `docs/adr/_tags.md`.
- Broadens `.gitignore` to cover `*-local.*` (with `!*-local.example` re-include for templates).
- Adds a `gitleaks` pre-commit hook layered on the existing `gitleaks` CI job.
- Adds a blunt, inline no-secrets section to `CLAUDE.md` citing ADR 000002.

## Spec & Plan

- Spec: `docs/superpowers/specs/2026-05-25-secrets-policy-design.md`
- Plan: `docs/superpowers/plans/2026-05-25-secrets-policy.md`

## Test plan

- [ ] CI `adr-validate` (merge gate) green
- [ ] CI `markdown-lint` green
- [ ] CI `gitleaks` green
- [ ] CI `lint-python` + `python-tests` green (no Python code changed; should be unaffected)
- [ ] After merge: confirm `gitleaks` is added to branch-protection required checks (out-of-repo settings change; see Task 9 of the plan).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL when the command completes.

---

### Task 9: After merge — confirm `gitleaks` is a required check

This is a one-time **manual** action on GitHub's web UI; it cannot be done from the CLI without admin-scoped tokens, and it is out of scope for the PR diff itself.

- [ ] **Step 1: Open the repo's branch protection settings**

In a browser: `Settings → Branches → Branch protection rules → main → Edit`.

- [ ] **Step 2: Add `gitleaks` to the required status checks**

Under **Require status checks to pass before merging**, search for `gitleaks` in the check list and add it. The other CI jobs (`markdown-lint`, `lint-python`, `python-tests`, `adr-validate`) should already be listed; if not, add them too.

- [ ] **Step 3: Save**

Confirm the settings change saves and the `gitleaks` check now appears in the required list. From this point, any PR with a gitleaks finding fails the merge gate.

---

## Done

After Task 9, the ADR is on `main`, enforcement is wired at three layers (`.gitignore`, pre-commit, required CI check), and CLAUDE.md carries the rule for every future Claude session. Future follow-up: a managed secret store ADR once infrastructure decisions are made.
