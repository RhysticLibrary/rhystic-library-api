---
id: "000003"
name: java-spring-boot-application-framework
description: Build the API on Java with the Spring Boot framework; version selection is delegated to build and dependency tooling.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [architecture]
---

# ADR 000003: Java and Spring Boot as Application Language and Framework

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

`rhystic-library-api` is a greenfield project. No application code has landed yet — by design, the foundational stack choices are being recorded as ADRs *before* the first line of application code, so the reasoning is captured as it is made rather than reconstructed later (see [`000001`](000001-adr-process-and-structure.md) and the project README).

The first such choice is the language and framework the API is built on. This decision anchors nearly everything downstream: the libraries available, the idioms contributors write in, the hiring and onboarding profile, and the production runtime.

This ADR covers **language and framework only**. Two related concerns are deliberately out of scope:

- **Build tool** — Maven vs. an alternative is a separable decision to be recorded in its own ADR.
- **Versions** — the specific Java release and Spring Boot line are delegated to build configuration and dependency tooling (Dependabot is already wired up). Routine upgrades within the stack do not require a new ADR.

## Decision Drivers

- **Team familiarity.** The team is most productive in Java and Spring. Choosing them minimizes ramp-up and gets a working API delivered fastest.
- **Ecosystem maturity.** Spring offers broad, well-maintained coverage of common needs (Spring Web, Data, Security, Actuator), an enormous third-party library ecosystem, and a long track record of long-term-support releases — a safe footing for a project expected to live and grow.

## Considered Options

- **Java + Spring Boot** — the team's strongest skill set; the most mature framework ecosystem available on the JVM.
- **Node.js / TypeScript** (e.g. NestJS or Express) — lighter runtime and a large package ecosystem, but a weaker fit for the team's strengths.
- **PHP** (e.g. Laravel or Symfony) — productive, batteries-included web frameworks, but outside the team's primary expertise.
- **Kotlin + Spring Boot** — the same framework with a more modern language; set aside because the team is less familiar with Kotlin and Java captures the same ecosystem benefits without the learning cost.
- **Scala** — expressive and powerful on the JVM, but the team is less familiar with it and its learning curve is steep.

## Decision Outcome

Build the API on **Java with the Spring Boot framework**.

The two drivers point the same way: Java + Spring Boot is both where the team is most productive *and* the most mature ecosystem on the table. The JVM-language alternatives (Kotlin, Scala) would have kept the Spring ecosystem but cost familiarity for no offsetting gain at this stage; the non-JVM alternatives (Node.js/TypeScript, PHP) trade away both the team's expertise and Spring's depth.

Version selection — the Java release line and the Spring Boot version — is intentionally left to build configuration and dependency tooling rather than fixed here, so the project can adopt patch and minor upgrades without an ADR churn cycle.

## Consequences

- **Positive**
  - The team is productive from day one; minimal ramp-up.
  - Mature, broad ecosystem (Spring Web/Data/Security/Actuator and the wider Java library landscape) covers common needs without bespoke plumbing.
  - Strong production story: observability, mature JVM tooling, and a well-understood deployment model.
  - Large hiring pool and abundant learning resources ease future onboarding.
- **Negative**
  - The JVM carries a heavier memory footprint and slower cold-start than lighter runtimes such as Node.js or Go — a consideration for serverless or rapid-scale scenarios.
  - Spring's convention-and-annotation "magic" has a real learning curve and can obscure behavior for contributors new to it.
  - The choice couples the project to the JVM ecosystem; moving off it later would be a substantial undertaking.

## Pros and Cons of the Options

### Java + Spring Boot

- Pros: highest team familiarity; the most mature framework ecosystem on the JVM; excellent production tooling and hiring pool.
- Cons: JVM footprint and startup cost; Spring's learning curve and implicit behavior.

### Node.js / TypeScript

- Pros: lightweight runtime; fast startup; huge npm ecosystem; JS/TS skills are common.
- Cons: weaker fit for the team's strengths; framework ecosystem less cohesive than Spring for backend concerns.

### PHP

- Pros: mature, productive web frameworks (Laravel, Symfony); fast to stand up CRUD APIs.
- Cons: outside the team's primary expertise; diverges from the team's tooling and idioms.

### Kotlin + Spring Boot

- Pros: same Spring ecosystem with a more modern, concise language; first-class Spring support.
- Cons: less team familiarity; adds a language-learning cost for no ecosystem gain over Java.

### Scala

- Pros: powerful, expressive JVM language; strong functional capabilities.
- Cons: least team familiarity of the options; steep learning curve; smaller backend-framework mindshare.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
