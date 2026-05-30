# Docker Compose Containerization ADR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author one ADR (`000014`) recording the decision to containerize the application with a multi-stage Docker image orchestrated by Docker Compose, following the project's ADR process, and land it as one PR.

**Architecture:** The ADR is scaffolded with `tools/adr/new_adr.py`, filled from the design spec (`docs/superpowers/specs/2026-05-29-docker-compose-containerization-design.md`), validated with `tools/adr/validate.py`, and left at status `Proposed`. No tag change is needed — `architecture` already exists in `docs/adr/_tags.md`. All work happens on the existing `docker-compose-containerization` branch and lands as one PR.

**Tech Stack:** Markdown ADRs, Python helper scripts under `tools/adr/`, the `creating-an-adr` skill, pre-commit hooks, GitHub PR flow.

---

## Conventions for every task

- Activate the repo's virtualenv once per shell session before running any
  `tools/adr/` script or `pre-commit`: `source .venv/bin/activate`.
- "Validate" means running `python tools/adr/validate.py` — the same check the CI
  `adr-validate` job runs. There is no application test suite involved.
- Author content directly into the scaffolded file; leave no `TODO`/`{{...}}`
  template tokens — `validate.py` and markdownlint flag them.
- The ADR stays `status: Proposed` with `date-accepted: ""`. Do not flip to
  `Accepted` — that happens on merge.

---

## Pre-flight

- [ ] **Step 0: Confirm the working branch and the committed spec**

Run: `git branch --show-current && git status --short && ls docs/superpowers/specs/2026-05-29-docker-compose-containerization-design.md`
Expected: branch is `docker-compose-containerization`; clean (or only this plan untracked); the spec file exists.

If you are not on the branch, run `git checkout docker-compose-containerization`. If the branch does not exist, create it from an up-to-date `main`: `git checkout main && git pull && git checkout -b docker-compose-containerization`.

---

## Task 1: Read the spec and the ADR process

**Files:**
- Read: `docs/superpowers/specs/2026-05-29-docker-compose-containerization-design.md`
- Read: `docs/adr/000001-adr-process-and-structure.md`
- Read: `docs/adr/_template.md`

- [ ] **Step 1: Invoke the creating-an-adr skill**

Use the `creating-an-adr` skill. It is the supported authoring path; it scaffolds, validates, and walks the merge flow, and guarantees conformance to `000001`. Do not hand-copy `_template.md`.

- [ ] **Step 2: Read the source material**

Read the three files above. The spec is the source of truth for content; `000001` governs structure, status lifecycle, and the reference-direction rule (an ADR may link only to **earlier** ids). Confirm the latest existing ADR id:

Run: `ls docs/adr/ | grep -E '^0000' | tail -1`
Expected: `000013-jacoco-coverage-gate.md` — so the new ADR is `000014`.

---

## Task 2: Scaffold ADR 000014

**Files:**
- Create: `docs/adr/000014-docker-compose-containerization.md` (created by the script)

- [ ] **Step 1: Inspect the scaffold helper**

Run: `python tools/adr/new_adr.py --help`
Expected: usage text confirming the script exists and how it takes the slug argument.

- [ ] **Step 2: Scaffold the ADR**

Run: `python tools/adr/new_adr.py docker-compose-containerization`
Expected: a new file `docs/adr/000014-docker-compose-containerization.md` is created from the template with id `000014`, `status: Proposed`, `date-proposed` set to today, and empty `date-accepted`.

- [ ] **Step 3: Verify the scaffold**

Run: `git status --short docs/adr/`
Expected: the new `000014-docker-compose-containerization.md` shows as untracked.

---

## Task 3: Fill in the ADR content

**Files:**
- Modify: `docs/adr/000014-docker-compose-containerization.md`

- [ ] **Step 1: Write the frontmatter and body**

Replace the scaffolded file's contents with the following. Keep the `id`, `date-proposed`, and any other generator-populated values the scaffold produced — only the example values below for those fields may differ; trust the generator for `id` and dates.

````markdown
---
id: "000014"
name: docker-compose-containerization
description: Containerize the application with a multi-stage Docker image orchestrated by Docker Compose — local dev now and interim single-host production (app container, external MySQL); CI stays on in-memory H2.
status: Proposed
date-proposed: "2026-05-29"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000014: Containerize the Application with Docker and Docker Compose

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | 2026-05-29                           |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | architecture                         |

## Context and Problem Statement

The foundational stack is fixed across prior ADRs: Java and Spring Boot ([`000003`](000003-java-spring-boot-application-framework.md)), Maven ([`000004`](000004-maven-build-tool.md)), MySQL ([`000005`](000005-mysql-relational-database.md)), Flyway ([`000006`](000006-flyway-schema-migrations.md)), and Spring Data JPA/Hibernate ([`000007`](000007-spring-data-jpa-hibernate-data-access.md)). What is still missing is a uniform, reproducible way to **run** the service and its runtime dependency, MySQL, without "works on my machine" drift — for developers now, and for production later.

Tests are deliberately outside this decision's path. The automated suite runs against in-memory H2 ([`000008`](000008-h2-test-database.md)), so it needs no container runtime, and this ADR does not change that.

## Decision Drivers

- **Reproducibility and parity.** The same application image should run in every environment, so behavior does not diverge between a developer laptop and production.
- **One-command local stack.** A new contributor should get the app plus its MySQL dependency running with a single command, with no bespoke local setup.
- **Configuration out of the image.** Environment-specific values — and especially secrets — must be injected at runtime, never baked into the image, honoring the secrets posture of [`000002`](000002-secrets-in-version-control.md).
- **Honest production scope.** Whatever is chosen for production now, the point at which it must be reconsidered should be recorded explicitly rather than discovered later.

## Considered Options

- **Docker image + Docker Compose** — a multi-stage Dockerfile builds the image; Compose orchestrates the app and (locally) MySQL. The chosen option.
- **Plain Dockerfile + run-instructions docs** — containerizes the app but leaves the database and multi-service wiring to manual, documented steps; reintroduces the drift this decision exists to remove.
- **Kubernetes / Helm from day one** — a full orchestrator with a large operational surface; premature for a greenfield single service with no current scaling need.
- **No containerization (run on host)** — the "works on my machine" drift problem itself; rejected.

## Decision Outcome

Adopt **Docker with Docker Compose**.

- Package the application as a **Docker image** built by a **multi-stage Dockerfile**: a build stage compiles the jar with the Maven toolchain ([`000004`](000004-maven-build-tool.md)); a runtime stage copies the jar into a slim JRE base image.
- Orchestrate with **Docker Compose** using **base + override layering**:
  - `compose.yaml` — base; defines the **app** service.
  - `compose.override.yaml` — auto-loaded by `docker compose` locally; adds a **throwaway MySQL** service plus developer conveniences (port exposure, a named volume). `docker compose up` brings up the full stack.
  - `compose.prod.yaml` — composed on top for production; runs the **app only** against an **external/managed MySQL** via environment variables, with no MySQL service and no dev conveniences.
- **Configuration comes from the environment, not the image.** Honoring [`000002`](000002-secrets-in-version-control.md), values are injected via environment variables sourced from a git-ignored `.env`, with a committed `.env.example` documenting variable *names* only — never real values.

The base + override layering is chosen over a single profile-gated file (which tangles dev and prod concerns and makes it easy to start the dev database in production by mistake) and over standalone per-environment files (which duplicate the app service and drift over time). Layering is the idiomatic Compose convention: local "just works", and the production delta stays small, explicit, and reviewable.

**Production stance — interim, and named as such.** Docker Compose is the **initial production runtime on a single host**: app-container-only, with MySQL as an external/managed instance kept out of the single-host blast radius. This is explicitly an interim choice, not a permanent endorsement. A future ADR will reconsider a real orchestrator (Kubernetes, ECS, or similar) when scaling, zero-downtime rollout, or multi-host needs arrive — the same "adopt the simple thing now, revisit when it bites" posture taken for the test database in [`000008`](000008-h2-test-database.md).

**CI is out of scope for now.** CI continues to run the H2 suite directly ([`000008`](000008-h2-test-database.md)), with no Compose stack. The door is left open to add a Compose-based smoke test or a Testcontainers-style fidelity pass later, if divergence or deployment confidence warrants it.

The following are **deferred to the implementing build change** and may be refined without amending this ADR (mirroring how [`000013`](000013-jacoco-coverage-gate.md) deferred its exclusion globs): the exact base images and JRE version, healthcheck definitions, and the final compose file and service names.

## Consequences

- **Positive**
  - One `docker compose up` gives any contributor the full app + MySQL stack with no bespoke setup.
  - Dev/prod parity on the application image reduces environment-specific surprises.
  - Configuration — and secrets — stay out of the image and out of version control, consistent with [`000002`](000002-secrets-in-version-control.md).
  - The production delta is a small, reviewable override layer rather than a separate, drifting file.
- **Negative**
  - Docker becomes a prerequisite for local development.
  - Multiple compose files must be kept coherent.
  - Compose-in-production is a known interim ceiling; the team carries an implicit commitment to revisit it (likely a real orchestrator) as the service grows.
  - Base-image and JRE choices require ongoing security patching.

## Pros and Cons of the Options

### Docker image + Docker Compose

- Pros: reproducible image across environments; one-command local stack; clean separation of config from image; idiomatic, widely understood tooling.
- Cons: Docker required locally; several compose files to maintain; Compose is a weak production orchestrator beyond a single host.

### Plain Dockerfile + run-instructions docs

- Pros: minimal tooling; containerizes the app without learning Compose.
- Cons: database and multi-service wiring stay manual and drift-prone; loses the one-command stack that motivates this decision.

### Kubernetes / Helm from day one

- Pros: production-grade orchestration, scaling, and rollout from the start.
- Cons: large operational surface and learning curve with no current need; premature for a greenfield single service.

### No containerization (run on host)

- Pros: nothing new to install or learn.
- Cons: the "works on my machine" drift this decision exists to eliminate; no parity between environments.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000002-secrets-in-version-control.md`](000002-secrets-in-version-control.md) — secrets posture that governs how configuration is injected (env vars, git-ignored `.env`, committed `.env.example`).
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — the application being containerized.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — the build that produces the jar the image packages.
- [`000005-mysql-relational-database.md`](000005-mysql-relational-database.md) — the database run as a throwaway Compose service locally and as an external instance in production.
- [`000008-h2-test-database.md`](000008-h2-test-database.md) — why CI needs no Compose stack, and the interim-then-revisit posture this ADR mirrors.
````

- [ ] **Step 2: Reconcile generator-populated fields**

Confirm the `id` line in the frontmatter and the `id` the scaffold assigned match (`000014`), and that `date-proposed` matches what the generator wrote. If the generator assigned a different id (because another ADR landed first), update the id, the filename references, the title heading, and the `Date Proposed`/frontmatter accordingly. The body links must all point to **earlier** ids — `000001`–`000008` are all earlier than `000014` and safe.

---

## Task 4: Validate

**Files:**
- Read: `docs/adr/000014-docker-compose-containerization.md`

- [ ] **Step 1: Run the ADR validator**

Run: `python tools/adr/validate.py`
Expected: passes. The validator checks frontmatter shape, that every tag is in `_tags.md` (`architecture` is present), the status lifecycle, and the reference-direction rule. Fix any reported issue and re-run until clean.

- [ ] **Step 2: Run the markdown/secrets pre-commit hooks against the file**

Run: `pre-commit run --files docs/adr/000014-docker-compose-containerization.md`
Expected: `markdownlint`, secret detection, and the ADR validator hooks pass (other hooks report "no files to check"). Fix any markdownlint findings (line length, list spacing) and re-run until clean.

---

## Task 5: Commit and open the PR

- [ ] **Step 1: Stage and commit**

Run:

```bash
git add docs/adr/000014-docker-compose-containerization.md docs/superpowers/plans/2026-05-29-docker-compose-containerization-adr.md
git commit -m "$(cat <<'EOF'
Add ADR 000014: containerize with Docker and Docker Compose

Record the decision to package the app as a multi-stage Docker image and
orchestrate it with Docker Compose (base + override layering): local dev now,
interim single-host production (app container; external MySQL), CI left on
in-memory H2. Status Proposed.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds; pre-commit hooks pass.

- [ ] **Step 2: Push the branch**

Run: `git push -u origin docker-compose-containerization`
Expected: branch pushed; PR-create URL printed.

- [ ] **Step 3: Open the PR**

Run:

```bash
gh pr create --title "Add ADR 000014: Docker Compose containerization" --body "$(cat <<'EOF'
Adds ADR 000014 recording the decision to containerize the application with a
multi-stage Docker image orchestrated by Docker Compose.

- Combined ADR: Docker image + Docker Compose orchestration.
- Base + override compose layering: local dev (app + throwaway MySQL) and
  interim single-host production (app only; external/managed MySQL).
- CI stays on in-memory H2 (000008); no Compose stack in CI for now.
- Config/secrets injected via env vars + git-ignored .env, honoring 000002.
- Production-orchestrator (K8s/ECS) reconsideration deferred to a future ADR.

Authored at status Proposed for review. Spec and plan included under
docs/superpowers/.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR created against `main`. The `adr-validate` CI job runs and passes.

- [ ] **Step 4: Report the PR URL**

Report the PR URL back to the user. Do **not** flip the ADR to `Accepted` — acceptance happens on merge, per the project's ADR lifecycle.

---

## Notes for the executor

- **Do not flip status to `Accepted`.** The ADR ships as `Proposed`; the prior ADR batches (000005–000013) were authored Proposed and accepted via the merge flow. Leave `date-accepted` empty.
- **Reference earlier ids only.** Per `000001`, an immutable ADR cannot point at a later one. All links here are to `000001`–`000008`.
- **No `_tags.md` change.** `architecture` already exists; do not add a tag.
- **No application code, Dockerfile, or compose files in this PR.** This work authors the *decision record* only. The actual Dockerfile and `compose.*.yaml` files are a separate, downstream implementation that this ADR governs but does not perform — the same separation the code-quality ADRs kept from the `pom.xml`.
