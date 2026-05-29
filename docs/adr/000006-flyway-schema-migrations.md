---
id: "000006"
name: flyway-schema-migrations
description: Use Flyway for versioned, SQL-first schema migrations; the Flyway version itself is delegated to dependency tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000006: Flyway for Schema Migrations

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

`rhystic-library-api` records its foundational stack choices as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000005`](000005-mysql-relational-database.md) chose MySQL as the relational database. The schema in that database needs to evolve over the life of the project, and how those changes are versioned and applied is an independent decision from the database engine itself — recorded here per ADR 000001's "one decision per ADR" rule.

The specific Flyway version is **out of scope**, delegated to dependency tooling, mirroring the version-agnostic stance of the prior stack ADRs.

## Decision Drivers

- **Safe, versioned schema evolution.** Schema changes should be explicit, ordered, reviewable, and decoupled from application deploys — not applied implicitly by the ORM.
- **Spring ecosystem fit.** Flyway is Spring Boot's default migration tool, with auto-configuration out of the box.
- **Team familiarity and simplicity.** The team knows Flyway, and its SQL-first model keeps migrations as plain, reviewable SQL.

## Considered Options

- **Flyway** — SQL-first, simple, and Spring Boot's default migration tool with auto-configuration.
- **Liquibase** — more powerful and database-agnostic via its XML/YAML/JSON changelog abstraction, but heavier and a layer removed from plain SQL.
- **Hibernate `ddl-auto` (schema generation)** — convenient in development, but unsafe and opaque for production schema management; rejected as the production mechanism.
- **No migration tool** — hand-applied SQL; unversioned, error-prone, and not viable for a project expected to grow.

## Decision Outcome

Use **Flyway** for schema migrations.

The drivers point the same way: Flyway keeps migrations as versioned, reviewable SQL — the simplest safe option — and is Spring Boot's default, so it is the path of least resistance through the framework's tooling. Hibernate `ddl-auto` is explicitly rejected for production schema management; Flyway is the single source of truth for the schema. Liquibase's database-agnostic abstraction is real but unneeded given a single, known database engine.

## Consequences

- **Positive**
  - Versioned, reviewable schema migrations from day one, decoupled from application deploys.
  - Spring Boot auto-configures Flyway; minimal setup.
  - SQL-first migrations are transparent and easy to reason about in review.
- **Negative**
  - Hibernate `ddl-auto` must stay disabled for any real environment, and that discipline must be enforced in configuration and review.
  - SQL-first migrations are written against the MySQL dialect, which has implications for test-database fidelity (recorded in the test-database ADR).
  - Less database-abstraction than Liquibase, should multi-database portability ever be needed — though that is not anticipated.

## Pros and Cons of the Options

### Flyway

- Pros: SQL-first and simple; Spring Boot's default with auto-configuration; migrations read as plain, reviewable SQL.
- Cons: less database-abstraction than Liquibase if multi-database portability were ever needed.

### Liquibase

- Pros: powerful, database-agnostic changelog abstraction.
- Cons: heavier; changelog formats sit a layer removed from plain SQL.

### Hibernate `ddl-auto`

- Pros: zero-effort schema generation in development.
- Cons: unsafe and opaque for production; no version history or review surface.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000005-mysql-relational-database.md`](000005-mysql-relational-database.md) — the database these migrations target.
