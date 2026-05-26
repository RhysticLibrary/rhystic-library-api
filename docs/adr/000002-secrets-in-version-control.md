---
id: "000002"
name: secrets-in-version-control
description: Forbids committing secrets, enumerates the file types and inline-value forms covered, names the runtime model and leak-response drill, and pins gitleaks as the defense-in-depth enforcement.
status: Accepted
date-proposed: "2026-05-25"
date-accepted: "2026-05-25"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [security, process]
---

# ADR 000002: Secrets in Version Control

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Accepted                             |
| Date Proposed    | 2026-05-25                           |
| Date Accepted    | 2026-05-25                           |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | security, process                    |

## Context and Problem Statement

The project will soon accumulate runtime dependencies that require secrets — database credentials, third-party API tokens, OAuth client secrets, JWT signing keys, certificates. Once a secret reaches Git history it must be treated as compromised: clones, mirrors, CI caches, and GitHub's search index distribute it beyond our reach within seconds. We need a project-wide rule that secrets never enter the repo, an enumerated definition of "secret" so the rule is unambiguous at review time, a runtime model that makes following the rule the path of least resistance, an enforcement mechanism that catches mistakes before they propagate, and a written response drill so an incident does not require improvisation.

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

## Links

- Design spec: [`docs/superpowers/specs/2026-05-25-secrets-policy-design.md`](../superpowers/specs/2026-05-25-secrets-policy-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-05-25-secrets-policy.md`](../superpowers/plans/2026-05-25-secrets-policy.md)
- ADR 000001 — ADR Process and Structure: [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md)
- `gitleaks`: <https://github.com/gitleaks/gitleaks>
- `git-filter-repo`: <https://github.com/newren/git-filter-repo>
