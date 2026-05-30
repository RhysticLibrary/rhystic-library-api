---
id: "000014"
name: docker-compose-containerization
description: Containerize the application with a multi-stage Docker image orchestrated by Docker Compose — local dev now and interim single-host production (app container, external MySQL); CI stays on in-memory H2.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000014: Containerize the Application with Docker and Docker Compose

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Accepted                             |
| Date Proposed    | 2026-05-29                           |
| Date Accepted    | 2026-05-29                           |
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
  - `compose.yml` — base; defines the **app** service.
  - `compose.override.yml` — auto-loaded by `docker compose` locally; adds a **local MySQL** service plus developer conveniences (port exposure, a named volume for local persistence). `docker compose up` brings up the full stack.
  - `compose.prod.yml` — composed on top for production; runs the **app only** against an **external/managed MySQL** via environment variables, with no MySQL service and no dev conveniences.
- **Configuration comes from the environment, not the image.** Honoring [`000002`](000002-secrets-in-version-control.md), values are injected via environment variables sourced from a git-ignored `.env`, with a committed `.env.example` documenting variable *names* only — never real values.

The base + override layering is chosen over a single profile-gated file (which tangles dev and prod concerns and makes it easy to start the dev database in production by mistake) and over standalone per-environment files (which duplicate the app service and drift over time). Layering is the idiomatic Compose convention: local "just works", and the production delta stays small, explicit, and reviewable.

**Production stance — interim, and named as such.** Docker Compose is the **initial production runtime on a single host**: app-container-only, with MySQL as an external/managed instance kept out of the single-host failure domain. This is explicitly an interim choice, not a permanent endorsement. A future ADR will reconsider a real orchestrator (Kubernetes, ECS, or similar) when scaling, zero-downtime rollout, or multi-host needs arrive — the same "adopt the simple thing now, revisit when it bites" posture taken for the test database in [`000008`](000008-h2-test-database.md).

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
  - Compose-in-production is a named interim ceiling; a future ADR will revisit it (likely a real orchestrator) when scaling or multi-host needs arrive.
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
- [`000013-jacoco-coverage-gate.md`](000013-jacoco-coverage-gate.md) — the coverage gate whose pattern of deferring implementation-level details to the build change this ADR follows.
