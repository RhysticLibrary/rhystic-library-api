---
id: "000005"
name: mysql-relational-database
description: Use MySQL as the relational database for the API; the MySQL version itself is delegated to dependency and hosting tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000005: MySQL as Relational Database

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

`rhystic-library-api` is a greenfield project whose foundational stack choices are being recorded as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000003`](000003-java-spring-boot-application-framework.md) chose Java and Spring Boot, and [`000004`](000004-maven-build-tool.md) chose Maven. The next foundational layer is persistence, and its first concern is where the API's data lives: the database engine that holds it in production.

Per ADR 000001's "one decision per ADR" rule, this ADR records the **relational store only**. The closely related concerns — schema migrations and the data-access layer — are independent choices recorded in their own ADRs, as is the test-database strategy.

The specific MySQL version is **out of scope**: it is delegated to hosting and dependency tooling (Dependabot is already wired up), mirroring the version-agnostic stance of 000003 and 000004. Routine upgrades do not require a new ADR.

## Decision Drivers

- **Team familiarity.** The team is most productive with MySQL — the same anchoring argument that drove the language, framework, and build-tool choices in 000003 and 000004.
- **Ecosystem maturity.** MySQL is a mature, ubiquitous RDBMS with first-class Spring Boot and JPA support, broad hosting options, and abundant tooling and documentation.

## Considered Options

- **MySQL** — the team's strongest database skill; mature, ubiquitous, and well-supported across the Spring ecosystem and hosting providers.
- **PostgreSQL** — a richer feature set (advanced types, stronger SQL-standard coverage), but less team familiarity for no offsetting need at this stage.
- **MariaDB** — a MySQL-compatible fork; viable, but offers no advantage over MySQL given the team already knows MySQL.

## Decision Outcome

Use **MySQL** as the relational database.

The two drivers point the same way as the rest of the stack: MySQL is both where the team is most productive *and* a deep, ubiquitous ecosystem with first-class Spring support. PostgreSQL's richer feature set is real but does not yet justify the familiarity cost; MariaDB adds nothing over MySQL for a team that already knows MySQL. This keeps the database choice resting on the same team-familiarity and ecosystem-fit reasoning already established for the language, framework, and build tool.

## Consequences

- **Positive**
  - The team is productive immediately; no ramp-up on the database engine.
  - Mature, ubiquitous engine with broad hosting, tooling, examples, and answers.
  - First-class Spring Boot and JPA support — the path of least resistance through the stack's tooling.
- **Negative**
  - MySQL's feature set is narrower than PostgreSQL's; advanced data types or SQL features may need workarounds later.
  - The choice couples the project to MySQL dialect specifics in schema and queries, which has downstream implications for testing fidelity (recorded in the test-database ADR).

## Pros and Cons of the Options

### MySQL

- Pros: highest team familiarity; mature and ubiquitous; first-class Spring/JPA support; broad hosting ecosystem.
- Cons: narrower feature set than PostgreSQL.

### PostgreSQL

- Pros: richer feature set; strong SQL-standard coverage; also well supported by Spring.
- Cons: less team familiarity for no offsetting need at this stage.

### MariaDB

- Pros: MySQL-compatible; drop-in for much of the same tooling.
- Cons: no advantage over MySQL given existing team familiarity; smaller mindshare than MySQL itself.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework decision this builds on.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build-tool decision this builds on.
