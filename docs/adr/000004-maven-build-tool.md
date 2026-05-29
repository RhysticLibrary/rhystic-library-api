---
id: "000004"
name: maven-build-tool
description: Use Maven as the build tool; the Maven version itself is delegated to the wrapper and dependency tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000004: Maven as Build Tool

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

`rhystic-library-api` is a greenfield project whose foundational stack choices are being recorded as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000003`](000003-java-spring-boot-application-framework.md) chose Java and Spring Boot as the language and framework, and explicitly deferred the build tool to a separate decision. This ADR makes that decision.

The build tool governs how the project is compiled, tested, packaged, and how its dependencies are declared and resolved — the day-to-day surface every contributor and the CI pipeline interact with.

The Maven version itself is **out of scope**: it is delegated to the Maven Wrapper and dependency tooling, mirroring the version-agnostic stance taken in 000003. Routine upgrades do not require a new ADR.

## Decision Drivers

- **Team familiarity.** The team knows Maven best — the same familiarity argument that anchored the Java/Spring Boot choice in 000003.
- **Declarative simplicity.** Maven's POM is declarative and predictable; there is less room for bespoke, drifting build logic than with a programmable build script.
- **Spring ecosystem fit.** First-class Spring Boot support — `start.spring.io`, the Spring Boot Maven plugin, and the bulk of Spring documentation and examples default to Maven.
- **Convention and stability.** Mature, stable, and ubiquitous, with a standard lifecycle and directory layout that minimizes surprise for new contributors and tooling.

## Considered Options

- **Maven** — the team's strongest build-tool skill; declarative POM; best-supported path in the Spring ecosystem.
- **Gradle** — faster incremental builds and a flexible Kotlin/Groovy DSL, but more moving parts and a steeper learning curve, with build logic expressed as code that can drift over time.

## Decision Outcome

Use **Maven** as the build tool.

All four drivers point the same way. Gradle's advantages — incremental-build speed and DSL flexibility — are real but matter most for large or unusually complex builds; they do not outweigh familiarity and declarative predictability for a single Spring Boot service. Maven is also the path of least resistance through the Spring tooling and documentation the project will lean on.

Choosing Maven keeps the build consistent with the team-familiarity reasoning already established for the language and framework, so the whole stack rests on the same justification.

## Consequences

- **Positive**
  - The team is productive immediately; no build-tool ramp-up.
  - Declarative POMs make builds predictable and easy to reason about across contributors.
  - Best-supported path in the Spring ecosystem — generators, plugins, and docs assume it.
  - Ubiquitous CI and IDE support; abundant examples and answers.
- **Negative**
  - Builds are slower and less aggressively cached than Gradle's at larger scales.
  - XML POMs are verbose compared to a concise DSL.
  - Less flexible for complex, custom build logic, should the project ever need it — though that need is not anticipated.

## Pros and Cons of the Options

### Maven

- Pros: highest team familiarity; declarative and predictable; first-class Spring support; ubiquitous tooling.
- Cons: slower builds at scale; verbose XML; limited flexibility for bespoke build logic.

### Gradle

- Pros: fast incremental builds with strong caching; flexible, expressive Kotlin/Groovy DSL; also well supported by Spring.
- Cons: less team familiarity; steeper learning curve; programmable build logic is more prone to drift and surprise.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework decision this build-tool choice complements.
