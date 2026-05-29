---
id: "000005"
name: persistence-stack-mysql-flyway-jpa
description: Use MySQL as the relational store, Flyway for schema migrations, and Spring Data JPA with Hibernate for data access; versions are delegated to dependency tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000005: Persistence Stack — MySQL, Flyway, and Spring Data JPA

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

`rhystic-library-api` is a greenfield project whose foundational stack choices are being recorded as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000003`](000003-java-spring-boot-application-framework.md) chose Java and Spring Boot, and [`000004`](000004-maven-build-tool.md) chose Maven. The next foundational layer is persistence: where the API's data lives, how its schema evolves, and how application code reads and writes it.

These are three related but separable concerns, and this ADR records all three because they are adopted together as one cohesive layer:

- **Relational store** — the database engine that holds the data in production.
- **Schema migrations** — how schema changes are versioned and applied.
- **Data access** — how application code maps to and queries that store.

Two concerns are deliberately **out of scope**:

- **Test databases.** How tests obtain a database is a separable decision recorded in a future ADR. This ADR covers the *production* persistence stack only.
- **Versions.** The specific MySQL, Flyway, Hibernate, and Spring Data versions are delegated to build configuration and dependency tooling (Dependabot is already wired up), mirroring the version-agnostic stance of 000003 and 000004. Routine upgrades do not require a new ADR.

## Decision Drivers

- **Team familiarity.** The team is most productive with MySQL, Flyway, and JPA/Hibernate — the same anchoring argument that drove the language, framework, and build-tool choices in 000003 and 000004.
- **Ecosystem maturity.** Each piece is mature, ubiquitous, and well-documented, with a large hosting and tooling ecosystem to draw on.
- **Spring ecosystem fit.** Flyway and Spring Data JPA/Hibernate are the default, best-supported persistence path in Spring Boot — auto-configuration, starters, and the bulk of Spring documentation assume them.
- **Safe schema evolution.** Versioned, declarative migrations from day one, rather than letting the ORM mutate production schema implicitly.

## Considered Options

### Relational store

- **MySQL** — the team's strongest database skill; a mature, ubiquitous RDBMS with first-class Spring Boot, JPA, and Flyway support and broad hosting options.
- **PostgreSQL** — a richer feature set (advanced types, stronger SQL standard coverage), but less team familiarity for no offsetting need at this stage.
- **MariaDB** — a MySQL-compatible fork; viable, but offers no advantage over MySQL given the team already knows MySQL.

### Schema migrations

- **Flyway** — SQL-first, simple, and Spring Boot's default migration tool with auto-configuration out of the box.
- **Liquibase** — more powerful and database-agnostic via its XML/YAML/JSON changelog abstraction, but heavier and a layer removed from plain SQL.
- **Hibernate `ddl-auto` (schema generation)** — convenient in development, but unsafe and opaque for production schema management; rejected as the production mechanism.
- **No migration tool** — hand-applied SQL; unversioned, error-prone, and not viable for a project expected to grow.

### Data access

- **Spring Data JPA + Hibernate** — the default Spring Data persistence path; repository abstraction and a familiar ORM the team already uses.
- **jOOQ** — type-safe SQL with excellent control, but a different model the team is less familiar with and additional build-time code generation.
- **MyBatis** — explicit SQL mapping with less "magic", but more boilerplate and weaker integration with the Spring Data idioms the project will lean on.
- **Plain `JdbcTemplate`** — maximum control and minimal abstraction, but pushes mapping and query boilerplate onto every consumer.

## Decision Outcome

Adopt **MySQL** as the relational store, **Flyway** for schema migrations, and **Spring Data JPA with Hibernate** for data access.

All three point the same way as the rest of the stack: each is where the team is most productive *and* the best-supported default in the Spring ecosystem. MySQL wins on familiarity and a deep, ubiquitous ecosystem; PostgreSQL's richer features do not yet justify the familiarity cost. Flyway keeps migrations as versioned, reviewable SQL — the simplest safe option, and Spring Boot's default — while Hibernate `ddl-auto` is explicitly kept out of the production schema path. Spring Data JPA/Hibernate gives a productive repository abstraction the team knows, and is the path of least resistance through Spring's tooling and documentation.

Choosing this stack keeps the whole persistence layer resting on the same team-familiarity and ecosystem-fit reasoning already established for the language, framework, and build tool.

## Consequences

- **Positive**
  - The team is productive immediately; no ramp-up on the persistence layer.
  - Versioned, reviewable schema migrations from day one, decoupled from application deploys.
  - The repository abstraction removes most CRUD boilerplate and integrates cleanly with Spring.
  - Mature, ubiquitous components with abundant hosting, tooling, examples, and answers.
- **Negative**
  - JPA/Hibernate is a leaky abstraction: lazy-loading pitfalls, N+1 query problems, and surprising flush/caching behavior require care and ORM literacy.
  - MySQL's feature set is narrower than PostgreSQL's; advanced data types or SQL features may need workarounds later.
  - Hibernate `ddl-auto` must stay disabled for any real environment — Flyway is the single source of truth for schema — and that discipline must be enforced in configuration and review.

## Pros and Cons of the Options

### MySQL

- Pros: highest team familiarity; mature and ubiquitous; first-class Spring/JPA/Flyway support; broad hosting ecosystem.
- Cons: narrower feature set than PostgreSQL.

### PostgreSQL

- Pros: richer feature set; strong SQL-standard coverage; also well supported by Spring.
- Cons: less team familiarity for no offsetting need at this stage.

### Flyway

- Pros: SQL-first and simple; Spring Boot's default with auto-configuration; migrations read as plain, reviewable SQL.
- Cons: less database-abstraction than Liquibase if multi-database portability were ever needed.

### Liquibase

- Pros: powerful, database-agnostic changelog abstraction.
- Cons: heavier; changelog formats sit a layer removed from plain SQL.

### Spring Data JPA + Hibernate

- Pros: Spring's default persistence path; productive repository abstraction; high team familiarity.
- Cons: leaky abstraction; lazy-loading and N+1 footguns; implicit behavior that can surprise.

### jOOQ / MyBatis / JdbcTemplate

- Pros: more explicit SQL and finer control.
- Cons: less team familiarity (jOOQ), more boilerplate (MyBatis, JdbcTemplate), and weaker fit with Spring Data idioms.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework decision this persistence stack builds on.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build-tool decision this persistence stack builds on.
