---
id: "000010"
name: checkstyle-style-enforcement
description: Adopt Checkstyle with the stock google_checks.xml, enforced via `mvn verify`, accepting overlap with Spotless.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [quality]
---

# ADR 000010: Checkstyle for Style Enforcement

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Accepted                             |
| Date Proposed    | 2026-05-29                           |
| Date Accepted    | 2026-05-29                           |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | quality                              |

## Context and Problem Statement

`rhystic-library-api` is a greenfield project whose quality bar is being recorded as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). [`000009`](000009-spotless-code-formatting.md) established Spotless with google-java-format as the project's code formatter, eliminating layout and whitespace concerns. Formatting, however, addresses only visual arrangement — it says nothing about naming conventions, Javadoc presence, or structural style rules (class and method organisation, import grouping policy, etc.). Those concerns require a separate tool.

The enforcement substrate is Maven ([`000004`](000004-maven-build-tool.md)) compiling Java ([`000003`](000003-java-spring-boot-application-framework.md)). Any style-checking tool must integrate naturally into the Maven lifecycle and agree with CI without per-machine setup.

The tool *version* is **out of scope**: it is delegated to dependency tooling, mirroring the version-agnostic stance taken in `000004`. Routine version upgrades do not require a new ADR.

## Decision Drivers

- **Non-format style coverage.** Naming conventions, Javadoc presence, and structural rules are outside Spotless's scope; a dedicated style checker is needed to enforce them.
- **Zero bespoke ruleset to maintain.** A stock, widely-used configuration eliminates the ongoing cost of authoring and defending custom rules.
- **Single source of truth.** `mvn verify` is the canonical gate — local and CI results must agree without requiring IDE plugins or per-developer settings.
- **Ecosystem familiarity.** Checkstyle is the most established Java style checker in the Maven ecosystem; the team's familiarity with Java extends naturally to it.

## Considered Options

- **`maven-checkstyle-plugin` + stock `google_checks.xml`** — the Maven Checkstyle plugin running the bundled, unmodified Google ruleset; configured (via a POM execution) to run in the `verify` phase.
- **PMD** — a static-analysis tool with style and structural rules; broader in scope than Checkstyle (also catches potential bugs and dead code) but heavier and less focused on style conventions.
- **Rely on Spotless alone** — accept that Spotless handles all style concerns; no additional tool.
- **Error Prone** — a compiler plugin that catches API-misuse and style bugs at compile time; complementary to Checkstyle but not a replacement for naming and Javadoc rules.
- **Do nothing** — accept that non-format style is unenforceable; resolve violations in code review.

## Decision Outcome

Adopt **`maven-checkstyle-plugin`** running the bundled, unmodified **`google_checks.xml`** ruleset, with severity set to `error`, configured via a POM execution to run in the Maven `verify` phase. Any violation fails the build.

Run Checkstyle alongside Spotless ([`000009`](000009-spotless-code-formatting.md)), **accepting the known overlap** between google-java-format and `google_checks.xml`: both tools share a common upstream style guide (the Google Java Style Guide) and are therefore generally aligned, though not identical in every rule. Occasional friction — for example, around Javadoc formatting or import-order rules — is handled by case-by-case suppression rather than by forking or modifying the ruleset.

Every driver points to this option. PMD's broader scope is appealing but misaligned with the immediate need: this decision is about style rules, not bug-finding, and PMD would add noise and configuration overhead before the project has any application code. Spotless alone leaves naming, Javadoc, and structural conventions entirely unchecked. Error Prone is a useful future complement but does not address the naming and documentation coverage gap. Checkstyle with the stock Google config gives maximum coverage at minimum maintenance cost.

## Consequences

- **Positive**
  - Naming conventions, Javadoc presence, and structural style rules are enforced from the first commit.
  - The stock `google_checks.xml` requires no authoring or ongoing maintenance of custom rules.
  - `mvn verify` is the same gate locally and in CI; no per-developer IDE configuration is required.
  - The Google ruleset and google-java-format share a common upstream style guide and are therefore generally aligned, so the overlap with Spotless rarely produces conflict in practice.
- **Negative**
  - Overlap with Spotless can occasionally produce conflicting expectations that require a justified suppression annotation; each suppression is a small local debt.
  - Adds a build step to `mvn verify`, increasing its wall-clock time slightly.
  - `google_checks.xml` is opinionated and not every rule may suit every future case; the remedy is targeted suppression, not forking the ruleset.

## Pros and Cons of the Options

### `maven-checkstyle-plugin` + stock `google_checks.xml`

- Pros: enforces naming, Javadoc, and structural rules Spotless does not cover; stock config is zero-maintenance; first-class Maven lifecycle integration; widely used and well-documented in the Java/Maven ecosystem; generally aligned with google-java-format through a shared upstream style guide.
- Cons: overlap with Spotless requires occasional suppression; adds a build step; opinionated ruleset may not suit every future need (mitigated by suppression).

### PMD

- Pros: broad rule set covering style, structural issues, and potential bugs; Maven plugin available; actively maintained.
- Cons: heavier and less focused than Checkstyle for pure style enforcement; adds meaningful configuration overhead; more overlap with future static-analysis tooling than with Checkstyle.

### Rely on Spotless alone

- Pros: no additional tool or configuration; no overlap to manage.
- Cons: naming conventions, Javadoc presence, and structural style rules are entirely unchecked; violations accumulate silently until code review.

### Error Prone

- Pros: catches API-misuse and style bugs at compile time; integrates into the Maven compiler plugin; powerful for a complementary future addition.
- Cons: does not address naming conventions or Javadoc rules; compiler-plugin integration adds complexity; not a substitute for a dedicated style checker.

### Do nothing

- Pros: no setup cost.
- Cons: non-format style issues accumulate unchecked; naming and documentation inconsistencies are caught only by code review, which is a slow and unreliable gate.

## Links

- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework this style checker targets.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build tool whose lifecycle phases enforce style checks.
- [`000009-spotless-code-formatting.md`](000009-spotless-code-formatting.md) — formatting decision; basis for the overlap discussion between google-java-format and `google_checks.xml`.
