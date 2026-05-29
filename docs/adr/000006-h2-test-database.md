---
id: "000006"
name: h2-test-database
description: Use the H2 in-memory database in MySQL-compatibility mode as the test database now, accepting MySQL divergence as a known trade-off to revisit later.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000006: H2 In-Memory Database for Tests

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

[`000005`](000005-persistence-stack-mysql-flyway-jpa.md) chose MySQL, Flyway, and Spring Data JPA/Hibernate as the production persistence stack and explicitly deferred the test-database strategy to a separate decision. This ADR makes that decision: what database the automated test suite runs against.

Production runs MySQL, so the central tension is fidelity versus speed and simplicity. The closer the test database is to production MySQL, the more confidence the suite gives — but the more infrastructure it requires. The key risk to name honestly: **H2, even in its MySQL-compatibility mode, is not MySQL.** It diverges in SQL dialect, built-in functions, and DDL semantics, so Flyway migrations written for MySQL and MySQL-specific query behavior are not fully exercised against the real engine in tests.

## Decision Drivers

- **Speed.** An in-memory database keeps the test suite fast and tight, encouraging frequent runs.
- **Zero external dependency.** No Docker daemon or running database required to execute tests locally or in CI.
- **Simplicity now.** While the schema and query surface are small, the divergence risk is correspondingly small, and the simplest option is the right one to start with.
- **Honest trade-off.** Whatever is chosen, the divergence risk and the conditions that would trigger revisiting it should be recorded explicitly.

## Considered Options

- **H2 (MySQL-compatibility mode)** — in-memory, fast, zero external dependency, trivial setup. Diverges from real MySQL in dialect, functions, and DDL.
- **Testcontainers (real MySQL)** — runs the production engine in a container for full fidelity, but adds Docker as a test-time dependency and a second test profile to wire and maintain.
- **Embedded MariaDB** — closer to MySQL than H2, but heavier than the H2 path and a less common, less idiomatic choice in the Spring ecosystem.

## Decision Outcome

Adopt **H2 in MySQL-compatibility mode** as the test database for now.

While the schema and query surface are small, speed and zero-infrastructure simplicity outweigh the fidelity gap, and H2 is the lightest path to a fast, runnable test suite. The divergence from real MySQL is accepted as a **known, recorded trade-off** rather than an oversight.

This is explicitly an interim choice, not a permanent endorsement. Running the suite against real MySQL via **Testcontainers** is the expected next step and a likely future ADR, to be taken up when divergence starts causing missed bugs — for example, once Flyway migrations or application queries lean on MySQL-specific features that H2 cannot faithfully reproduce.

## Consequences

- **Positive**
  - Fast, in-memory test runs with no Docker or external database dependency.
  - Low setup cost and easy onboarding — tests just run.
  - Appropriate to the current small schema and query surface.
- **Negative**
  - Tests can pass against H2 while real MySQL would fail (or vice versa); the suite does not guarantee MySQL behavior.
  - MySQL-specific SQL and Flyway migrations may need compatibility care to also run on H2, or an H2-incompatible migration may force the revisit sooner than planned.
  - H2 is a known interim choice; the team carries an implicit commitment to revisit fidelity (likely Testcontainers) as the project grows.

## Pros and Cons of the Options

### H2 (MySQL-compatibility mode)

- Pros: fast, in-memory, zero external dependency; trivial setup; well-trodden in the Spring ecosystem.
- Cons: not real MySQL — diverges in dialect, functions, and DDL, so it cannot fully validate MySQL behavior or migrations.

### Testcontainers (real MySQL)

- Pros: full fidelity against the production engine; exercises real migrations and MySQL-specific behavior.
- Cons: adds Docker as a test-time dependency; slower; requires a second test profile and wiring to maintain.

### Embedded MariaDB

- Pros: closer to MySQL than H2 while still embeddable.
- Cons: heavier than H2; less common and less idiomatic in the Spring ecosystem; still not MySQL itself.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000005-persistence-stack-mysql-flyway-jpa.md`](000005-persistence-stack-mysql-flyway-jpa.md) — production persistence stack that deferred this test-database decision.
