---
id: "000013"
name: jacoco-coverage-gate
description: Adopt JaCoCo enforcing 90% line and branch coverage project-wide via `mvn verify`.
status: Proposed
date-proposed: "2026-05-29"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [quality]
---

# ADR 000013: JaCoCo 90% Coverage Gate

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | 2026-05-29                           |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | quality                              |

## Context and Problem Statement

`rhystic-library-api` already has formatting, style, and static-analysis gates in CI, but none of those gates measure whether code is actually exercised by tests. A coverage gate closes that gap: it prevents untested code from merging by failing the build when coverage falls below the configured threshold.

The project is greenfield. Holding a high coverage bar from day one is cheap — every new class is written with tests in mind from the start. Retrofitting coverage onto an untested codebase later is expensive: tests written after the fact tend to be shallow, and the cultural shift is harder. The right time to set the bar is before the first application class lands.

The substrate is Maven ([`000004`](000004-maven-build-tool.md)) running Java and Spring Boot ([`000003`](000003-java-spring-boot-application-framework.md)). Any coverage tooling must integrate naturally into the Maven lifecycle so that a single `mvn verify` command covers compilation, tests, and all quality gates — locally and in CI — without extra steps.

## Decision Drivers

- **Prevent untested code from merging.** The gate must make untested code a build failure, not a warning.
- **Measure line AND branch coverage together.** Branch coverage catches untested conditionals that line coverage hides — a line with an `if` can be "covered" by line even when the false branch is never taken. Requiring both counters gives a meaningful signal.
- **Simplicity of administration.** A single project-wide aggregate number is easy to reason about and easy to communicate to contributors. Per-class thresholds multiply the configuration surface and create constant friction as the class landscape changes.
- **Single source of truth via `mvn verify`.** Local runs and CI must agree on pass/fail with no extra tooling or scripts.

## Considered Options

- **`jacoco-maven-plugin` `check` goal at 90% line + branch, project-wide aggregate** — the chosen option.
- **A lower threshold** — e.g., 70–80%; easier to hit initially but sets a weaker bar that silently degrades over time.
- **A per-class threshold** — strictest possible; enforces that no individual class is undertested, but creates friction on legitimately hard-to-test classes (e.g., framework entry points, generated code) and requires a per-class exclusion list that grows with the codebase.
- **No coverage gate** — no build-time enforcement; coverage would be advisory at best.
- **Cobertura** — an older Maven coverage plugin; effectively unmaintained and superseded by JaCoCo across the Java ecosystem.

## Decision Outcome

Adopt the `jacoco-maven-plugin` with its `check` goal — which has no default lifecycle binding and must be attached to `verify` via an explicit POM `<execution>` block — enforcing **90% LINE and 90% BRANCH coverage as a project-wide aggregate**. The build fails when either counter falls below 90%.

JaCoCo is the de-facto standard for bytecode-instrumentation-based coverage on the JVM, is actively maintained, and integrates directly with the Maven lifecycle via its plugin — no extra wrapper scripts. Running in the `verify` phase means `mvn verify` is the one command that covers everything, consistent with how other quality gates in this project are wired.

90% is a widely-adopted high-coverage bar for services: 100% is impractical without either excluding every hard-to-test class or writing low-value tests purely to satisfy the counter, while thresholds in the 70–80% range leave room for whole untested conditional branches to pass undetected. The exclusion list is the relief valve for legitimately hard-to-test code — the Spring `@SpringBootApplication` main class, plain DTO/configuration classes, and generated artifacts. The exact exclusion globs are finalized when the `pom.xml` and package layout exist and may be refined in the implementing build change without amending this ADR.

The project-wide aggregate is chosen over a per-class rule because per-class creates friction on legitimately hard-to-test classes and requires a growing exclusion list; the aggregate is simpler to administer, and the exclusion list handles edge cases.

## Consequences

- **Positive**
  - Enforces a tested codebase from the first class; untested code is a build failure, not a suggestion.
  - Branch coverage catches untested conditional logic that line coverage alone would mask.
  - A single project-wide number is easy to administer and communicate.
  - Local and CI agree exactly via `mvn verify` — no environment-specific divergence.
- **Negative**
  - A strict aggregate can pressure contributors toward low-value tests written solely to satisfy the counter for hard-to-reach branches; the exclusion list must be curated honestly as the relief valve.
  - Adds build time (instrumentation and report generation), though the overhead is modest for a single Spring Boot service.
  - The aggregate can mask a single weak class hidden behind a strong overall number — an accepted trade-off versus the friction of per-class strictness.

## Pros and Cons of the Options

### `jacoco-maven-plugin` — 90% line + branch, project-wide aggregate

- Pros: actively maintained de-facto standard; native Maven lifecycle integration; both coverage counters enforced; project-wide aggregate is simple to administer; exclusions are the well-understood relief valve.
- Cons: aggregate can mask a single undertested class; exclusion list requires curation discipline.

### Lower threshold (e.g., 70–80%)

- Pros: easier to satisfy immediately; less pressure to write coverage-padding tests.
- Cons: sets a weaker standard that tends to drift further downward over time; does not instill test discipline from the start.

### Per-class threshold

- Pros: strictest possible guarantee; no class can hide behind others.
- Cons: high maintenance burden as the class landscape changes; creates constant friction on legitimately hard-to-test classes; requires a per-class exclusion list that grows with the codebase.

### No coverage gate

- Pros: zero friction; no build-time overhead.
- Cons: coverage is advisory at best; untested code merges silently; cultural drift toward a low-coverage codebase is hard to reverse.

### Cobertura

- Pros: was the original Maven coverage standard.
- Cons: effectively unmaintained; superseded by JaCoCo across the Java ecosystem; not the right choice for a new project.

## Links

- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework decision that establishes the JVM substrate this gate targets.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build tool decision that this coverage gate hooks into via the Maven `verify` phase.
