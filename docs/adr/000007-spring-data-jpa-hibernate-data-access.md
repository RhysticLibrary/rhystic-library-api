---
id: "000007"
name: spring-data-jpa-hibernate-data-access
description: Use Spring Data JPA with Hibernate as the data-access layer; versions are delegated to dependency tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000007: Spring Data JPA with Hibernate for Data Access

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

`rhystic-library-api` records its foundational stack choices as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000005`](000005-mysql-relational-database.md) chose MySQL as the relational database and [`000006`](000006-flyway-schema-migrations.md) chose Flyway for migrations. The remaining persistence concern is the data-access layer: how application code maps to and queries the store. This is an independent decision from the engine and the migration tool, recorded here per ADR 000001's "one decision per ADR" rule.

The specific Spring Data and Hibernate versions are **out of scope**, delegated to dependency tooling, mirroring the version-agnostic stance of the prior stack ADRs.

## Decision Drivers

- **Team familiarity.** The team is most productive with JPA and Hibernate — the same anchoring argument as the rest of the stack.
- **Spring ecosystem fit.** Spring Data JPA is the default, best-supported data-access path in Spring Boot, with auto-configuration and a repository abstraction that removes most CRUD boilerplate.

## Considered Options

- **Spring Data JPA + Hibernate** — the default Spring Data persistence path; repository abstraction and a familiar ORM the team already uses.
- **jOOQ** — type-safe SQL with excellent control, but a different model the team is less familiar with and additional build-time code generation.
- **MyBatis** — explicit SQL mapping with less "magic", but more boilerplate and weaker integration with the Spring Data idioms the project will lean on.
- **Plain `JdbcTemplate`** — maximum control and minimal abstraction, but pushes mapping and query boilerplate onto every consumer.

## Decision Outcome

Use **Spring Data JPA with Hibernate** as the data-access layer.

The drivers point the same way: JPA/Hibernate is where the team is most productive *and* Spring's default persistence path, so it is the path of least resistance through the framework's tooling and documentation. Its repository abstraction removes most CRUD boilerplate. The alternatives trade that productivity for finer SQL control (jOOQ, MyBatis, JdbcTemplate) that the project does not yet need, at the cost of familiarity or boilerplate.

## Consequences

- **Positive**
  - The team is productive immediately; the repository abstraction removes most CRUD boilerplate.
  - Default, best-supported Spring data-access path — auto-configuration and abundant examples.
  - Integrates cleanly with the rest of the Spring stack.
- **Negative**
  - JPA/Hibernate is a leaky abstraction: lazy-loading pitfalls, N+1 query problems, and surprising flush/caching behavior require care and ORM literacy.
  - Hibernate's schema-generation features must stay disabled — Flyway owns the schema (see [`000006`](000006-flyway-schema-migrations.md)).

## Pros and Cons of the Options

### Spring Data JPA + Hibernate

- Pros: Spring's default persistence path; productive repository abstraction; high team familiarity.
- Cons: leaky abstraction; lazy-loading and N+1 footguns; implicit behavior that can surprise.

### jOOQ

- Pros: type-safe SQL with fine control; transparent generated queries.
- Cons: less team familiarity; additional build-time code generation.

### MyBatis

- Pros: explicit SQL mapping; less implicit behavior.
- Cons: more boilerplate; weaker fit with Spring Data idioms.

### Plain `JdbcTemplate`

- Pros: maximum control; minimal abstraction.
- Cons: pushes mapping and query boilerplate onto every consumer.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000005-mysql-relational-database.md`](000005-mysql-relational-database.md) — the database this layer reads and writes.
- [`000006-flyway-schema-migrations.md`](000006-flyway-schema-migrations.md) — schema ownership; Hibernate schema generation stays off.
