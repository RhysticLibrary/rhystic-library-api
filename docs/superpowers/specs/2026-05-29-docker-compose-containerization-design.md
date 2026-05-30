# Design: Containerize the Application with Docker and Docker Compose

**Date:** 2026-05-29
**Status:** Approved (brainstorming) — pending ADR authoring
**Target artifact:** A single new ADR (next id: `000014`) under `docs/adr/`, tagged `architecture`.

## Summary

Record the decision to containerize `rhystic-library-api` with a Docker image and
orchestrate it with Docker Compose. The image is built by a multi-stage Dockerfile;
Compose runs the app and its runtime dependency (MySQL) locally for developers and,
in an interim single-host form, in production. CI is explicitly out of scope: the test
suite runs on in-memory H2 ([`000008`](../../adr/000008-h2-test-database.md)) and needs
no container runtime today.

This is a brainstorming spec, not the ADR itself. The ADR is authored separately via the
`creating-an-adr` skill and must conform to [`000001`](../../adr/000001-adr-process-and-structure.md).

## Context

The foundational stack is fixed across prior ADRs:

- Java/Spring Boot — [`000003`](../../adr/000003-java-spring-boot-application-framework.md)
- Maven — [`000004`](../../adr/000004-maven-build-tool.md)
- MySQL — [`000005`](../../adr/000005-mysql-relational-database.md)
- Flyway — [`000006`](../../adr/000006-flyway-schema-migrations.md)
- Spring Data JPA / Hibernate — [`000007`](../../adr/000007-spring-data-jpa-hibernate-data-access.md)
- H2 for tests — [`000008`](../../adr/000008-h2-test-database.md)

What is missing is a uniform, reproducible way to **run** the service and its MySQL
dependency without "works on my machine" drift — for developers now, and for production
later. Tests are out of this decision's path: they run on in-memory H2, so the automated
suite needs no container runtime.

## Decision

### Image

- Package the application as a **Docker image** built by a **multi-stage Dockerfile**:
  a build stage compiles the jar with the Maven toolchain; a runtime stage copies the jar
  into a slim JRE base image.

### Orchestration — Compose, base + override layering

- `compose.yaml` — base; defines the **app** service.
- `compose.override.yaml` — auto-loaded by `docker compose` locally; adds a **throwaway
  MySQL** service plus developer conveniences (port exposure, a named volume). A developer
  runs `docker compose up` and gets the full stack.
- `compose.prod.yaml` — composed on top for production
  (`docker compose -f compose.yaml -f compose.prod.yaml ...`); runs the **app only** and
  points it at an **external/managed MySQL** via environment variables. No MySQL service,
  no dev conveniences.

Rationale for layering over alternatives:

- **Single profile-gated file** — denser; prod and dev concerns tangle in one file; easy to
  start the dev DB in prod by mistake.
- **Standalone file per environment** — duplicates the app service and drifts over time
  (copy-paste rot).
- **Base + override (chosen)** — idiomatic Compose convention; local "just works"; the prod
  delta is small, explicit, and reviewable.

### Configuration and secrets

Environment-specific values come from the environment, never baked into the image. Honoring
[`000002`](../../adr/000002-secrets-in-version-control.md): configuration is injected via env
vars sourced from a **git-ignored `.env`**, with a committed **`.env.example`** documenting
variable *names* only — never real values.

### Production stance (interim, honest)

Compose is the **initial production runtime** on a single host: app-container-only, MySQL
external/managed. A future ADR will reconsider a real orchestrator (Kubernetes / ECS) when
scaling, zero-downtime rollout, or multi-host needs arrive. This mirrors the "interim choice,
revisit when it bites" posture of the H2 ADR ([`000008`](../../adr/000008-h2-test-database.md)).

### CI scope (explicitly deferred)

CI keeps running the H2 suite directly, with no Compose stack. The door is left open to add a
Compose-based smoke test or a Testcontainers-style fidelity pass later if divergence or
deployment confidence warrants it.

## Considered options

- **Docker + Docker Compose** — chosen.
- **Plain Dockerfile + run-instructions docs** — containerizes the app but leaves the DB and
  multi-service wiring to manual steps; reintroduces the drift this decision removes.
- **Kubernetes / Helm from day one** — premature for a greenfield single service; large
  operational surface with no current scaling need.
- **No containerization / run-on-host** — the "works on my machine" drift problem itself.

## Consequences

- **Positive**
  - One `docker compose up` gives any developer the full stack.
  - Dev/prod parity on the application image.
  - Clean separation of configuration from the image; secrets stay out of version control.
  - Small, reviewable production delta via the override layer.
- **Negative**
  - Docker becomes a local-development prerequisite.
  - Multiple compose files to keep coherent.
  - Compose-in-production is a known interim ceiling, carrying an implicit commitment to
    revisit at scale.
  - Base-image / JRE choices need ongoing security patching.

## Deferred to the implementing PR (not ADR-amending)

Mirroring how [`000013`](../../adr/000013-jacoco-coverage-gate.md) deferred its exclusion
globs, these are settled when the build and files exist and may be refined without amending
the ADR:

- Exact base images and JRE version.
- Healthcheck definitions.
- Final compose file names and service names.

## ADR metadata (for authoring)

- **id:** `000014` (confirm at authoring time; `000013` is the current latest)
- **tag:** `architecture` (no `_tags.md` change)
- **status:** Proposed → Accepted on merge
- **links:** [`000002`](../../adr/000002-secrets-in-version-control.md),
  [`000003`](../../adr/000003-java-spring-boot-application-framework.md),
  [`000004`](../../adr/000004-maven-build-tool.md),
  [`000005`](../../adr/000005-mysql-relational-database.md),
  [`000008`](../../adr/000008-h2-test-database.md)

## Implementation notes

**Use the existing ADR tooling, not hand-editing.** The `creating-an-adr` skill and the
helper scripts under `tools/adr/` are the supported path; they enforce frontmatter shape,
tag validity, and merge-gate compliance, and read only frontmatter so they cost far fewer
tokens than reading whole files.

- No tag change is needed — `architecture` already exists in `docs/adr/_tags.md`.
- Scaffold with `python tools/adr/new_adr.py <slug>` — do not copy `_template.md` by hand.
  The script assigns the next id (expected `000014`). Provisional slug:
  `docker-compose-containerization`.
- Leave the ADR at status `Proposed` with `date-accepted` empty for review. Do **not** flip
  to `Accepted` in this work.
- Reference only earlier ADRs by id (the immutability/reference-direction rule from
  `000001`): `000002`, `000003`, `000004`, `000005`, `000008` are all earlier and safe to
  link.
- Run `python tools/adr/validate.py` before opening the PR.

Concrete artifact the implementing PR will touch:

- `docs/adr/000014-docker-compose-containerization.md` (exact id is whatever `new_adr.py`
  assigns at scaffold time; `000014` assuming no other ADR lands first).
