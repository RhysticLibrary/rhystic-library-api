---
id: "000015"
name: multi-module-domain-structure
description: Structure the application as a domain-sliced multi-module Maven build — a non-building parent, a boot aggregator, and per-domain impl/types/client subtrees with a strict dependency graph — to enforce isolation now and enable cheap extraction to microservices later.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000015: Multi-Module Maven Structure Sliced by Domain

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

```text
rhystic-library-api/                 parent, packaging = pom (dependency + plugin management only)
├── boot/                            Spring Boot entrypoint; aggregates and runs the impls
├── users/                           per-domain aggregator pom (builds nothing)
│   ├── users-impl/                  controllers · services · repositories · entities
│   ├── users-types/                 request/response DTOs — no JPA
│   └── users-client/                HTTP client (interface + impl) → users-types
├── cards/                           per-domain aggregator pom (builds nothing)
│   ├── cards-impl/                  controllers · services · repositories · entities
│   ├── cards-types/                 request/response DTOs — no JPA
│   └── cards-client/                HTTP client (interface + impl) → cards-types
└── organizations/                   per-domain aggregator pom (builds nothing)
    ├── organizations-impl/          controllers · services · repositories · entities
    ├── organizations-types/         request/response DTOs — no JPA
    └── organizations-client/        HTTP client (interface + impl) → organizations-types
```

**Dependency rules.** Allowed: `boot` → every `<domain>-impl`; `<domain>-impl` → its own `<domain>-types`; `<domain>-impl` → another domain's `<other>-client` (transitively pulling `<other>-types`); `<domain>-client` → its own `<domain>-types`. Forbidden: `<domain>-impl` → another `<domain>-impl` (no implementation ever sees another's entities, services, or repositories); anything → `boot`; `<domain>-types` → anything domain-specific. So `organizations-impl` needing user data depends on `users-client` → `users-types`, and **never** on `users-impl`.

**Cross-domain calls go over HTTP.** A `<domain>-client` is self-contained — its only dependency is its own `-types`, so it never needs the target domain's implementation. The sole difference between "monolith" and "extracted" is the base URL the client points at, configured in `boot`. Inside the single `boot` process this makes a cross-domain call a real **loopback HTTP request** (serialize, traverse the web stack, hit the other controller in the same JVM, with internal auth applying). This overhead is **accepted deliberately**. It is the price of strict isolation — an in-process direct call is impossible without breaking the core invariant. It also makes every cross-domain call remote-shaped, so extraction is a configuration change rather than a rewrite. And the same domain-specific APIs are what the future frontend API consumes, so building them now is not speculative.

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
