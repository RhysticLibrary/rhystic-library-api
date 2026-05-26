# Design: Secrets-in-Version-Control Policy ADR

**Date:** 2026-05-25
**Status:** Approved (pending implementation)

## Goal

Establish a project-wide rule, enforced by tooling, that secrets never enter this repository — together with a written response drill for the inevitable accident. The ADR captures the policy; the implementing change wires the enforcement (`.gitignore` patterns, pre-commit hook, CI job) and updates CLAUDE.md so the rule is load-bearing for every Claude session.

The repo is days old. We codify the rule now, before secrets-bearing infrastructure (database credentials, third-party API tokens, OAuth clients, JWT keys, certificates) starts landing — not after the first leak.

## Scope

In scope:

- A new ADR — provisionally `000002-secrets-in-version-control.md` — that records the policy, the runtime model, the enforcement mechanism, and the leak-response drill.
- A new `security` tag added to `docs/adr/_tags.md`.
- `.gitignore` updates to cover the enumerated secret-bearing file types.
- A `gitleaks` pre-commit hook added to the existing pre-commit framework.
- The **existing** `gitleaks` CI job (`.github/workflows/ci.yml`, `gitleaks` job using `gitleaks/gitleaks-action@v2`) confirmed as a required check in branch protection. The job already exists; this ADR ratifies it as the unbypassable gate.
- A CLAUDE.md update that states the no-secrets rule **inline and bluntly**, then cites the ADR as the ratifying source. The rule must be enforceable from CLAUDE.md alone.

Out of scope:

- Picking a managed secret store (Vault, AWS Secrets Manager, Spring Cloud Config Server, etc.). The runtime model is "environment variables or a managed secret store"; the specific store is a separate decision once infrastructure lands.
- A baseline scan of existing history. Enforcement is forward-only — acceptable here because the repo is days old and verified clean by inspection.
- Commit message conventions and the AI `Co-Authored-By` trailer. Originally bundled with this request; deferred to a separate ADR.
- The branching and merge model (main-only, squash-merge, force-push policy, required checks, no `--no-verify`). Deferred to a separate ADR.
- A custom `gitleaks` rule set. Start with upstream defaults; add project-specific rules only when a false negative or false positive justifies one.

## Context and Problem Statement

The project will soon accumulate runtime dependencies that require secrets — database credentials, third-party API tokens, OAuth client secrets, JWT signing keys, certificates. Once a secret reaches Git history it must be treated as compromised: clones, mirrors, CI caches, and GitHub's search index distribute it beyond our reach within seconds. We need:

1. A project-wide rule that secrets never enter the repo.
2. An enumerated definition of "secret" so the rule is unambiguous at review time.
3. A runtime model that makes following the rule the path of least resistance.
4. An enforcement mechanism that catches mistakes before they propagate.
5. A written response drill so an incident does not require improvisation.

## Considered Options

- **No formal rule; rely on reviewer vigilance and `.gitignore`.** Cheapest. Fails the first time a file type slips past `.gitignore` and a reviewer is rushed. No drill for the inevitable leak.
- **Policy without tooling.** Write the rule, no scanner. Aligns expectations but every enforcement is a human catching a human. Doesn't survive contact with AI-authored commits that don't know the rule exists.
- **Pre-commit scanner only.** Catches most accidents at the developer's machine. Bypassable on `--no-verify`, uninstalled hooks, or fresh clones — so it's a comfort layer, not a gate.
- **CI scanner only.** Unbypassable, but the secret has already reached the remote by the time CI runs — every accident triggers a rotation drill. Wastes the cheap local-catch opportunity.
- **Policy + pre-commit + CI scanner with named tooling and a written leak-response drill.** *(Chosen.)* Defense in depth: pre-commit makes the easy path the safe path; CI is the gate that catches missed hooks; the drill removes ambiguity in an incident.

Scanner alternatives considered for the chosen approach:

- **`gitleaks`.** *(Chosen.)* Single Go binary. First-class pre-commit hook and GitHub Action. Mature rule set. No SaaS dependency. No new language ecosystem in the repo.
- **`trufflehog`.** Strong verified-scanning (actively checks tokens against live providers). Heavier; verification step is slower. Better suited when false-positive cost is high.
- **`detect-secrets`.** Best baseline-file workflow for grandfathering false positives. Less GitHub-Action-native. Strong fit only if we had legacy history to baseline — we don't.
- **`ggshield` (GitGuardian).** Strongest detection corpus, but SaaS-backed; requires a GitGuardian account and API key in CI. Adds an external service dependency to the security path.

History-rewrite tool alternatives:

- **`git-filter-repo`.** *(Chosen as preferred.)* Upstream-recommended replacement for the deprecated `git filter-branch`. Precise and well-documented.
- **`bfg-repo-cleaner`.** Acceptable for very large repos where filter-repo is too slow. Less precise.
- **Tool-agnostic ("use whatever").** Rejected — in the heat of an incident, a named tool removes a decision.

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

Secrets load at runtime from environment variables or a managed secret store. (The specific store is out of scope for this ADR.) Only `*.example` templates are committed — they document expected variable **names** without real **values**.

### Enforcement (defense in depth)

- **`.gitignore`** carries the patterns from the enumeration above.
- **Pre-commit hook**: `gitleaks` runs via the existing pre-commit framework on the staged diff. Blocks the commit on a finding. Fast feedback at developer velocity.
- **CI job**: the existing `gitleaks` job in `.github/workflows/ci.yml` runs on every pull request and every push to `main`. This ADR ratifies it as a required check in branch protection — the unbypassable gate.
- **CLAUDE.md**: states the no-secrets rule **inline and bluntly** — the enumerated file types and inline-value forms repeated explicitly — and cites this ADR as the ratifying source. The rule must be enforceable from CLAUDE.md alone, without relying on the model deciding to read the ADR mid-edit.

### Leak-response drill

If a secret is committed — even briefly, even on a feature branch, even before push — treat it as compromised. CI caches, mirrors, and clones distribute it within seconds. The order is non-negotiable:

1. **Rotate the secret immediately** at its source (provider console, secret store, etc.). Assume a third party already has the committed value.
2. **Remove from history** with `git-filter-repo` (preferred). `bfg-repo-cleaner` is acceptable for very large repos where filter-repo is too slow. Do **not** rely on `git rm` in a follow-up commit — the secret remains in history and in every consumer's cache.
3. **Force-push the cleaned branch** with `--force-with-lease`.
4. **Notify** anyone with a clone: they must re-clone, not pull.

## Consequences

**Positive**

- One unambiguous rule that humans and AI agents can apply at edit time.
- Defense in depth: pre-commit catches the easy cases at dev velocity; CI catches the bypassed cases at gate velocity.
- `gitleaks` is a single binary, no SaaS dependency, no new language ecosystem in the repo.
- The leak-response drill removes decision-making from an incident — the order is written and the tool is named.
- CLAUDE.md statement makes the rule load-bearing for every Claude session without depending on ADR discovery.

**Negative**

- Two scan layers add small but non-zero latency: a few seconds on `git commit`, a CI job on every PR.
- `gitleaks` false positives will happen (high-entropy strings, sample tokens in tests). The cost is a tuned allowlist file plus the discipline to actually tune it rather than disable the scan.
- Forward-only enforcement means any pre-existing leak in history is unaddressed. Acceptable here (repo is days old, verified clean) but would need a separate remediation effort on an older codebase.
- A managed secret store is out of scope; until that's decided, "runtime secret loading" means environment variables in practice. A follow-up ADR is implied once infrastructure lands.

## Implementation Notes

**Use the existing ADR tooling, not hand-editing.** The `creating-an-adr` skill and its helper scripts under `tools/adr/` are the supported path; they enforce frontmatter shape, alphabetical tag ordering, and merge-gate compliance, and they read only frontmatter so they cost far fewer tokens than reading whole files. Specifically:

- Invoke the `creating-an-adr` skill and follow its runbook.
- Run `python tools/adr/new_adr.py` to scaffold the ADR file with correct ID, filename, and frontmatter — do not copy `_template.md` by hand.
- Run `python tools/adr/add_tag.py security "<one-line description>"` to add the `security` tag — do not edit `_tags.md` by hand.
- Run `python tools/adr/validate.py` locally before opening the PR, and `python tools/adr/validate.py --merge-gate` before flipping status to `Accepted`.

Concrete artifacts the implementing PR will touch:

- `docs/adr/NNNNNN-secrets-in-version-control.md` — the ADR file. ID is whatever `new_adr.py` assigns at scaffold time (likely `000002`).
- `docs/adr/_tags.md` — `security` tag added via `add_tag.py`.
- `.gitignore` — verify the existing entries cover the enumeration (the current file already lists `.env*`, `*.pem`, `*.key`, `*.p12`, `*.jks`, `*.crt`, `application-local.*`). Add any missing patterns; cross-check against the ADR's enumerated list as the source of truth.
- `.pre-commit-config.yaml` — add the `gitleaks` hook. Pin the rev; `pre-commit autoupdate` plus the `checking-dep-drift` skill keep it current.
- `.github/workflows/ci.yml` — **not modified.** The `gitleaks` job already exists. The implementing PR's responsibility is to confirm the job is configured as a required check in branch protection (out-of-repo settings change at adoption time).
- `CLAUDE.md` — add an explicit, blunt section near the top stating the no-secrets rule with the enumerated file types and inline-value forms, citing the new ADR by ID.

Allowlist: start with `gitleaks` defaults and no project-specific allowlist file. Add `.gitleaks.toml` only when the first justified false positive shows up.

## Open Questions

- Whether the pre-commit hook should scan only the staged diff (fast) or the full repo (thorough). Default is diff-only for speed; the existing CI job already does full-history scans on every PR.
