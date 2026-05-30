# Multi-Module Domain Structure ADR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author one ADR (`000015`) recording the decision to structure `rhystic-library-api` as a domain-sliced multi-module Maven build, following the project's ADR process, and land it as one PR.

**Architecture:** The ADR is scaffolded with `tools/adr/new_adr.py`, filled from the design spec (`docs/superpowers/specs/2026-05-29-multi-module-structure-design.md`), validated with `tools/adr/validate.py`, and left at status `Proposed`. No tag change is needed — `architecture` already exists in `docs/adr/_tags.md`. All work happens on the existing `multi-module-domain-structure-adr` branch and lands as one PR.

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

Run: `git branch --show-current && git status --short && ls docs/superpowers/specs/2026-05-29-multi-module-structure-design.md`
Expected: branch is `multi-module-domain-structure-adr`; clean (or only this plan untracked); the spec file exists.

If you are not on the branch, run `git checkout multi-module-domain-structure-adr`. If the branch does not exist, create it from an up-to-date `main`: `git checkout main && git pull && git checkout -b multi-module-domain-structure-adr`.

---

## Task 1: Read the spec and the ADR process

**Files:**
- Read: `docs/superpowers/specs/2026-05-29-multi-module-structure-design.md`
- Read: `docs/adr/000001-adr-process-and-structure.md`
- Read: `docs/adr/_template.md`

- [ ] **Step 1: Invoke the creating-an-adr skill**

Use the `creating-an-adr` skill. It is the supported authoring path; it scaffolds, validates, and walks the merge flow, and guarantees conformance to `000001`. Do not hand-copy `_template.md`.

- [ ] **Step 2: Read the source material**

Read the three files above. The spec is the source of truth for content; `000001` governs structure, status lifecycle, and the reference-direction rule (an ADR may link only to **earlier** ids). Confirm the latest existing ADR id:

Run: `ls docs/adr/ | grep -E '^0000' | tail -1`
Expected: `000014-docker-compose-containerization.md` — so the new ADR is `000015`.

---

## Task 2: Scaffold ADR 000015

**Files:**
- Create: `docs/adr/000015-multi-module-domain-structure.md` (created by the script)

- [ ] **Step 1: Inspect the scaffold helper**

Run: `python tools/adr/new_adr.py --help`
Expected: usage text confirming the script exists and how it takes the slug argument.

- [ ] **Step 2: Scaffold the ADR**

Run: `python tools/adr/new_adr.py multi-module-domain-structure`
Expected: a new file `docs/adr/000015-multi-module-domain-structure.md` is created from the template with id `000015`, `status: Proposed`, `date-proposed` set to today, and empty `date-accepted`.

- [ ] **Step 3: Verify the scaffold**

Run: `git status --short docs/adr/`
Expected: the new `000015-multi-module-domain-structure.md` shows as untracked.

---

## Task 3: Fill in the ADR content

**Files:**
- Modify: `docs/adr/000015-multi-module-domain-structure.md`

- [ ] **Step 1: Write the frontmatter and body**

Replace the scaffolded file's contents with the following. Keep the `id`, `date-proposed`, and any other generator-populated values the scaffold produced — only the example values below for those fields may differ; trust the generator for `id` and dates.

````markdown
---
id: "000015"
name: multi-module-domain-structure
description: Structure the application as a domain-sliced multi-module Maven build — a non-building parent, a boot aggregator, and per-domain impl/types/client subtrees with a strict dependency graph — to enforce isolation now and enable cheap extraction to microservices later.
status: Proposed
date-proposed: "2026-05-29"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000015: Multi-Module Maven Structure Sliced by Domain

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

`rhystic-library-api` records its foundational stack choices as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). The language and framework are Java and Spring Boot ([`000003`](000003-java-spring-boot-application-framework.md)), the build tool is Maven ([`000004`](000004-maven-build-tool.md)), and the data-access layer is Spring Data JPA with Hibernate ([`000007`](000007-spring-data-jpa-hibernate-data-access.md)). What is still undecided is how the source is **organized**: a single-module monolith, or a multi-module build, and along which seams.

This decision is shaped by a stated long-term direction. Today the whole application ships in one repo and runs as one process. In the far future, each business domain is expected to become its own microservice (and likely its own repo), and a separate frontend API — a different application outside this repo — will consume these domains' HTTP endpoints. The structure chosen now should make that future a cheap, mechanical extraction rather than a rewrite, while enforcing clean domain boundaries from the first line of code.

## Decision Drivers

- **Enforced domain isolation.** Domain boundaries should be guaranteed by the build graph, not by convention — a forbidden cross-domain dependency should fail to compile, not merely fail review.
- **Cheap future extraction.** Each domain should be liftable into its own microservice/repo with minimal rework; the seams that will become network boundaries should already be network-shaped.
- **Reuse by a separate frontend API.** The per-domain HTTP APIs built here are consumed by a future frontend API in another repo, so domain-specific APIs are needed regardless of extraction.
- **Centralized build governance.** Dependency and plugin versions should be managed in one place so every module stays consistent.

## Considered Options

- **Domain-sliced multi-module modulith** — a non-building parent, a single `boot` aggregator, and one self-contained subtree per domain (implementation, wire DTOs, HTTP client) with a strict dependency graph; cross-domain calls go over HTTP. The chosen option.
- **Single-module monolith** — all code in one module; simplest to start, but boundaries are unenforced and extraction later means untangling mutual references.
- **Multi-module grouped by layer** — modules grouped as "all DTOs", "all clients", "all impls"; makes the no-cross-dependency rule visible and eases per-layer config, but a domain's pieces scatter across parents so extraction is per-child surgery, not a subtree lift.
- **Multi-module with direct, acyclic module-to-module dependencies** — domains depend on each other's modules directly as long as the graph stays acyclic; simpler than HTTP clients, but couples domains at compile time and makes extraction a rewrite.

## Decision Outcome

Adopt a **domain-sliced multi-module Maven build**.

**Topology.**

- A **parent** packaging pom (`rhystic-library-api`) centralizes dependency management and plugin management and produces no deployable artifact.
- A **`boot`** module is the only aggregator that assembles a running application. It depends on every `<domain>-impl` so their controllers are hosted, and it owns runtime configuration — including the base URLs the clients point at.
- Each business domain (`users`, `cards`, `organizations`, …) is a **per-domain aggregator pom** (`<domain>/`, a plural noun, builds nothing) grouping three leaf modules:
  - `<domain>-impl` — controllers, services, repositories, and JPA entities.
  - `<domain>-types` — the request/response DTOs exchanged over the API; **no JPA, plain data**.
  - `<domain>-client` — a client interface plus an HTTP implementation; depends on `<domain>-types`.

```
rhystic-library-api/                 parent, packaging = pom (dependency + plugin management only)
├── boot/                            Spring Boot entrypoint; aggregates and runs the impls
├── users/                           per-domain aggregator pom (builds nothing)
│   ├── users-impl/                   controllers · services · repositories · entities
│   ├── users-types/                  request/response DTOs — no JPA
│   └── users-client/                 HTTP client (interface + impl) → users-types
├── cards/
│   └── cards-impl/  cards-types/  cards-client/
└── organizations/
    └── organizations-impl/  organizations-types/  organizations-client/
```

**Dependency rules.** Allowed: `boot` → every `<domain>-impl`; `<domain>-impl` → its own `<domain>-types`; `<domain>-impl` → another domain's `<other>-client` (transitively pulling `<other>-types`); `<domain>-client` → its own `<domain>-types`. Forbidden: `<domain>-impl` → another `<domain>-impl` (no implementation ever sees another's entities, services, or repositories); anything → `boot`; `<domain>-types` → anything domain-specific. So `organizations-impl` needing user data depends on `users-client` → `users-types`, and **never** on `users-impl`.

**Cross-domain calls go over HTTP.** A `<domain>-client` is self-contained — its only dependency is its own `-types`, so it never needs the target domain's implementation. The sole difference between "monolith" and "extracted" is the base URL the client points at, configured in `boot`. Inside the single `boot` process this makes a cross-domain call a real **loopback HTTP request** (serialize, traverse the web stack, hit the other controller in the same JVM, with internal auth applying). This overhead is **accepted deliberately**: it is the price of strict isolation (an in-process direct call is impossible without breaking the core invariant), it makes every cross-domain call remote-shaped so extraction is a configuration change rather than a rewrite, and the same domain-specific APIs are what the future frontend API consumes, so building them now is not speculative.

**Naming convention.** `<domain>-impl` (not `-app`, which overpromises for a library `boot` hosts, nor `-service`, which collides with the Spring `@Service` layer); `<domain>-types` (not `-models`, since these are wire data, not the JPA domain model); plural domain directories. Coordinate convention: groupId `com.rhysticlibrary`, artifactIds matching module names, so extraction is a clean lift of coordinates.

**Shared cross-cutting types — sanctioned, deferred.** Types belonging to no single domain (pagination wrappers, a standard error envelope, common value objects) are anticipated. This ADR sanctions a future `common-types` leaf module that any `-types`/`-client`/`-impl` may depend on, but does not create it now — it is added the day a genuinely shared type appears, without a new decision, avoiding a junk-drawer module on day one.

The following are **deferred to the implementing build change** and may be refined without amending this ADR: the concrete initial domain set (beyond the illustrative `users`/`cards`/`organizations`), the exact HTTP-client technology and internal-auth mechanism, whether and when to introduce `common-types`, and per-module plugin/dependency specifics under the parent's management.

## Consequences

- **Positive**
  - Domain boundaries are enforced by the build graph — a forbidden dependency fails to compile rather than slipping through review.
  - Each domain extracts to its own microservice/repo as a near one-move lift; cross-domain calls are already remote-shaped.
  - The per-domain HTTP APIs are reusable by the future separate frontend API.
  - The parent centralizes dependency and plugin management, keeping every module consistent.
- **Negative**
  - More modules and poms to maintain than a single-module build; more Maven ceremony.
  - In-process cross-domain calls pay real HTTP serialization and round-trip overhead and require internal auth — accepted deliberately.
  - A domain needing another's data must define and version a DTO contract and client up front rather than reaching into a shared object.
  - Slicing domains too finely risks premature fragmentation; domain boundaries must be chosen with care.

## Pros and Cons of the Options

### Domain-sliced multi-module modulith

- Pros: boundaries enforced by the build graph; one-move per-domain extraction; cross-domain seams already network-shaped; APIs reusable by the frontend; centralized build governance.
- Cons: most modules/poms to maintain; loopback HTTP overhead in-process; contracts and clients must be defined up front.

### Single-module monolith

- Pros: simplest to start; no inter-module wiring; no cross-domain serialization.
- Cons: boundaries unenforced; extraction later means untangling mutual references — exactly the future cost this decision avoids.

### Multi-module grouped by layer

- Pros: the no-cross-dependency rule is visually obvious; uniform per-layer configuration is easy.
- Cons: a domain's pieces scatter across separate parents, so extracting a domain is per-child surgery rather than lifting one subtree.

### Multi-module with direct, acyclic module-to-module dependencies

- Pros: simpler than HTTP clients; no serialization overhead between domains.
- Cons: couples domains at compile time; extraction becomes a rewrite, not a configuration change.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — the framework whose application this build structures; `boot` is its entrypoint.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — the build tool whose multi-module/parent-pom model this decision uses.
- [`000007-spring-data-jpa-hibernate-data-access.md`](000007-spring-data-jpa-hibernate-data-access.md) — the JPA entities that live in `<domain>-impl` and are deliberately kept out of `<domain>-types`.
````

- [ ] **Step 2: Reconcile generator-populated fields**

Confirm the `id` line in the frontmatter and the `id` the scaffold assigned match (`000015`), and that `date-proposed` matches what the generator wrote. If the generator assigned a different id (because another ADR landed first), update the id, the filename references, the title heading, and the `Date Proposed`/frontmatter accordingly. The body links must all point to **earlier** ids — `000001`, `000003`, `000004`, `000007` are all earlier than `000015` and safe.

---

## Task 4: Validate

**Files:**
- Read: `docs/adr/000015-multi-module-domain-structure.md`

- [ ] **Step 1: Run the ADR validator**

Run: `python tools/adr/validate.py`
Expected: passes. The validator checks frontmatter shape, that every tag is in `_tags.md` (`architecture` is present), the status lifecycle, and the reference-direction rule. Fix any reported issue and re-run until clean.

- [ ] **Step 2: Run the markdown/secrets pre-commit hooks against the file**

Run: `pre-commit run --files docs/adr/000015-multi-module-domain-structure.md`
Expected: `markdownlint`, secret detection, and the ADR validator hooks pass (other hooks report "no files to check"). Fix any markdownlint findings (line length, list spacing) and re-run until clean.

---

## Task 5: Commit and open the PR

- [ ] **Step 1: Stage and commit**

Run:

```bash
git add docs/adr/000015-multi-module-domain-structure.md docs/superpowers/plans/2026-05-29-multi-module-domain-structure-adr.md
git commit -m "$(cat <<'EOF'
Add ADR 000015: multi-module Maven structure sliced by domain

Record the decision to structure the app as a domain-sliced Maven
modulith: a non-building parent, a boot aggregator, and per-domain
impl/types/client subtrees with a strict dependency graph. Cross-domain
calls go over HTTP so each domain can extract to its own microservice
cheaply. Status Proposed.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds; pre-commit hooks pass. (The spec was committed in an earlier commit on this branch; this commit adds the ADR and this plan.)

- [ ] **Step 2: Push the branch**

Run: `git push -u origin multi-module-domain-structure-adr`
Expected: branch pushed; PR-create URL printed.

- [ ] **Step 3: Open the PR**

Run:

```bash
gh pr create --title "Add ADR 000015: multi-module domain structure" --body "$(cat <<'EOF'
Adds ADR 000015 recording the decision to structure rhystic-library-api as a
domain-sliced multi-module Maven build.

- Non-building parent (dependency + plugin management); a single boot aggregator.
- Per-domain subtree of impl / types / client modules with a strict dependency
  graph — no impl ever depends on another domain's impl.
- Cross-domain calls go over HTTP via per-domain clients, so each domain can be
  extracted to its own microservice (and repo) as a near one-move lift; the same
  APIs serve a future separate frontend API.
- Loopback-HTTP overhead in-process is an accepted, deliberate trade-off.
- common-types module sanctioned but deferred.

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

- **Do not flip status to `Accepted`.** The ADR ships as `Proposed`; the prior ADR batches were authored Proposed and accepted via the merge flow. Leave `date-accepted` empty.
- **Reference earlier ids only.** Per `000001`, an immutable ADR cannot point at a later one. All links here are to `000001`, `000003`, `000004`, `000007`.
- **No `_tags.md` change.** `architecture` already exists; do not add a tag.
- **No `pom.xml`, modules, or application code in this PR.** This work authors the *decision record* only. The actual parent pom, module poms, and domain code are a separate, downstream implementation that this ADR governs but does not perform — the same separation prior infrastructure ADRs kept from their implementing changes.
