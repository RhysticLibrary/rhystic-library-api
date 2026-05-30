# Design: Multi-Module Maven Structure (Domain-Sliced Modulith)

**Date:** 2026-05-29
**Status:** Approved (brainstorming) — pending ADR authoring
**Target artifact:** A single new ADR (next id: `000015`) under `docs/adr/`, tagged `architecture`.

## Summary

Record the decision to structure `rhystic-library-api` as a **multi-module Maven build
sliced by domain**. A non-building parent (packaging pom) owns dependency and plugin
management. A `boot` module is the only thing that assembles and runs the application.
Each business domain (`users`, `cards`, `organizations`, …) is a self-contained subtree of
three leaf modules — implementation, wire DTOs, and an HTTP client — with a strict
dependency graph that forbids one domain's implementation from ever seeing another's.

The deliberate design goal is **cheap future extraction**: today everything ships in one
repo and runs in one `boot` process, but each domain is shaped so it can be lifted into its
own microservice (and its own repo) with minimal rework. Cross-domain calls already go over
HTTP, so they are remote-shaped from day one.

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

No application code exists yet — the foundational choices are being recorded before code
lands. What is undecided is how the source is **organized**: a single-module monolith, or a
multi-module build, and along which seams. This ADR settles that, and does so in a way that
serves a stated long-term direction: each domain eventually becoming its own microservice,
consumed both by sibling domains and by a separate frontend API (a different
application/repo).

## Decision

### Module topology

A domain-sliced multi-module Maven build:

```
rhystic-library-api/                 parent, packaging = pom
│                                     (dependencyManagement + pluginManagement only; builds nothing)
├── boot/                             Spring Boot entrypoint: main class, wiring, runs the web server
│
├── users/                           per-domain aggregator pom (builds nothing)
│   ├── users-impl/                   controllers · services · repositories · entities
│   ├── users-types/                  request/response DTOs — NO JPA, plain data
│   └── users-client/                 HTTP client (interface + impl) → depends on users-types
│
├── cards/
│   ├── cards-impl/   cards-types/   cards-client/
│
└── organizations/
    ├── organizations-impl/  organizations-types/  organizations-client/
```

- The **parent** is a packaging pom: it centralizes dependency management and plugin
  management and produces no deployable artifact.
- **`boot`** is the only aggregator that assembles a running application. It depends on every
  `<domain>-impl` so their controllers are hosted, and it owns runtime configuration
  (including the base URLs the clients point at).
- Each **`<domain>/`** directory is an aggregator pom that groups its three leaves and may
  carry per-domain shared config. It builds nothing itself.
- The three leaves per domain are the real artifacts (see naming below).

### Dependency rules

**Allowed edges:**

- `boot` → every `<domain>-impl` (it hosts their controllers)
- `<domain>-impl` → its own `<domain>-types` (controllers speak in those DTOs)
- `<domain>-impl` → **another** domain's `<other>-client` (its only window into another
  domain — transitively pulling `<other>-types`)
- `<domain>-client` → its own `<domain>-types`

**Forbidden edges (the invariants the layout exists to enforce):**

- ❌ `<domain>-impl` → `<other>-impl` — no implementation ever sees another's entities,
  services, or repositories
- ❌ anything → `boot`
- ❌ `<domain>-types` → anything domain-specific — DTO modules are leaves

So `organizations-impl` needing user data depends on `users-client` → `users-types`, and
**never** on `users-impl`.

### Cross-domain call mechanism

`<domain>-client` is a client **interface plus an HTTP implementation** (e.g. Spring's
`RestClient` / declarative HTTP interface). Its only dependency is its own `-types`, so it is
fully self-contained and never needs the target domain's implementation. The only thing that
differs between "monolith" and "extracted" is the **base URL** the client points at,
configured in `boot`.

**Accepted trade-off (intentional):** inside the single `boot` process, an
`organizations-impl` → `users-client` call is a real **loopback HTTP request** — it
serializes a DTO, traverses the web stack, and hits `users-impl`'s controller in the same
JVM, with internal auth applying. This overhead is accepted deliberately:

- It is the price of strict isolation. An in-process direct call is impossible without some
  module depending on another domain's impl, which breaks the core invariant.
- It makes every cross-domain call remote-shaped from day one, so extracting a domain into
  its own microservice is a configuration change (base URL), not a rewrite.
- The same domain-specific HTTP APIs are what the future separate frontend API will consume,
  so building them now is not speculative — they are needed regardless.

### Naming convention (consistency is the goal; the gate is open)

| Module | Role |
|---|---|
| `rhystic-library-api` | parent, packaging pom |
| `boot` | Spring Boot entrypoint; aggregates and runs the impls |
| `<domain>/` (plural noun, e.g. `users/`) | per-domain aggregator pom |
| `<domain>-impl` | controllers · services · repositories · entities |
| `<domain>-types` | DTOs exchanged over the API — no JPA, pure data |
| `<domain>-client` | HTTP client (interface + impl) → depends on `<domain>-types` |

Rationale for the suffixes chosen:

- **`-impl`** over `-app`/`-service`: today it is a library hosted by `boot`, not
  independently runnable, so `-app` would overpromise; `-service` collides with the Spring
  `@Service` layer. `-impl` honestly names "the implementation behind this domain."
- **`-types`** over `-models`/`-domain-models`: these are *not* the domain model (no entities
  live here) — they are plain wire data, so `-types` avoids confusion with the JPA entities
  in `-impl`.
- **Plural domain directories** (`users`, `cards`) to match how the domains are named.

Coordinate convention: groupId `com.rhysticlibrary`, artifactIds matching the module names,
so extraction is a clean lift of coordinates.

### Shared cross-cutting types (acknowledged, deferred)

Types belonging to no single domain (pagination wrappers, a standard error envelope, common
value objects) are anticipated. The ADR **sanctions a future `common-types` leaf module** any
`-types`/`-client`/`-impl` may depend on, but does **not** create it now — it is added the day
a genuinely shared type appears, without a new decision. This avoids seeding a junk-drawer
module on day one.

## Considered options

- **Domain-sliced multi-module modulith (chosen)** — strict per-domain isolation with
  HTTP-shaped cross-domain calls; one-move extraction per domain.
- **Single-module monolith** — simplest to start, but no enforced boundaries; extraction
  later means untangling a ball of mutual references — exactly the future cost being avoided.
- **Multi-module grouped by layer** (all DTOs together, all clients together) — makes the
  "no cross-domain dependency" rule visually obvious and eases per-layer config, but a
  domain's pieces scatter across three parents, so extraction means surgically pulling one
  child out of each group rather than lifting one subtree.
- **Direct module-to-module dependencies, acyclic only** — simpler than HTTP clients, but
  couples domains at compile time and makes extraction a rewrite, not a config change.

## Consequences

- **Positive**
  - Boundaries are enforced by the build graph, not convention — a forbidden dependency
    fails to compile.
  - Each domain extracts to its own microservice/repo as a near one-move lift; cross-domain
    calls are already remote-shaped.
  - The domain-specific HTTP APIs are reusable by the future separate frontend API.
  - The parent centralizes dependency and plugin management for uniformity across modules.
- **Negative**
  - More modules and poms to maintain than a single-module build; more Maven ceremony.
  - In-process cross-domain calls pay real HTTP serialization + round-trip overhead and
    require internal auth — accepted deliberately.
  - A domain needing another's data must define and version a DTO contract and client up
    front, rather than reaching into a shared object.
  - Risk of premature fragmentation if domains are sliced too finely; domain boundaries must
    be chosen with care.

## Deferred to the implementing PR (not ADR-amending)

These are settled when the build and code exist and may be refined without amending the ADR:

- The concrete initial domain set (beyond illustrative `users` / `cards` / `organizations`).
- The exact HTTP-client technology (declarative HTTP interface vs `RestClient` vs other) and
  internal-auth mechanism.
- Whether and when to introduce `common-types`.
- Per-module plugin/dependency specifics under the parent's management.

## ADR metadata (for authoring)

- **id:** `000015` (confirm at authoring time; `000014` is the current latest)
- **tag:** `architecture` (no `_tags.md` change)
- **status:** Proposed → Accepted on merge
- **links:** [`000003`](../../adr/000003-java-spring-boot-application-framework.md),
  [`000004`](../../adr/000004-maven-build-tool.md),
  [`000007`](../../adr/000007-spring-data-jpa-hibernate-data-access.md)

## Implementation notes

**Use the existing ADR tooling, not hand-editing.** The `creating-an-adr` skill and the
helper scripts under `tools/adr/` are the supported path; they enforce frontmatter shape, tag
validity, and merge-gate compliance, and read only frontmatter so they cost far fewer tokens
than reading whole files.

- No tag change is needed — `architecture` already exists in `docs/adr/_tags.md`.
- Scaffold with `python tools/adr/new_adr.py <slug>` — do not copy `_template.md` by hand.
  The script assigns the next id (expected `000015`). Provisional slug:
  `multi-module-domain-structure`.
- Leave the ADR at status `Proposed` with `date-accepted` empty for review. Do **not** flip to
  `Accepted` in this work.
- Reference only earlier ADRs by id (the immutability/reference-direction rule from
  `000001`): `000003`, `000004`, `000007` are all earlier and safe to link.
- Run `python tools/adr/validate.py` before opening the PR.

Concrete artifact the implementing PR will touch:

- `docs/adr/000015-multi-module-domain-structure.md` (exact id is whatever `new_adr.py`
  assigns at scaffold time; `000015` assuming no other ADR lands first).
