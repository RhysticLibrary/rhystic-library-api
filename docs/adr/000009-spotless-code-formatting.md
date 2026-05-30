---
id: "000009"
name: spotless-code-formatting
description: Adopt Spotless with google-java-format as the project's code formatter, enforced via `mvn verify`.
status: Proposed
date-proposed: "2026-05-29"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [quality]
---

# ADR 000009: Spotless for Code Formatting

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

`rhystic-library-api` is a greenfield project whose quality bar is being recorded as ADRs before application code lands (see [`000001`](000001-adr-process-and-structure.md)). Without an automatically-applied, consistently-enforced formatter, style debates accumulate over time and formatting changes pollute diffs with noise that obscures meaningful changes. Establishing a formatter now — before the first production file is committed — means the project never accumulates a formatting debt.

The enforcement substrate is Maven ([`000004`](000004-maven-build-tool.md)) compiling Java ([`000003`](000003-java-spring-boot-application-framework.md)). The formatter must integrate naturally into the Maven lifecycle and produce output that all contributors and CI agree on without per-machine configuration.

The tool *version* is **out of scope**: it is delegated to dependency tooling, mirroring the version-agnostic stance taken in `000004`. Routine version upgrades do not require a new ADR.

## Decision Drivers

- **Zero diff noise.** Every commit should be free of incidental whitespace or import-order churn; formatting must be fully deterministic.
- **Auto-fixable.** Contributors should be able to fix formatting violations with a single command so compliance costs nothing beyond running it.
- **Single source of truth.** `mvn verify` is the canonical gate — local and CI results must agree without requiring IDE plugins or per-developer settings.
- **Ecosystem familiarity.** The team knows Java and Maven; the formatter and its Maven plugin should be well-established in that ecosystem.

## Considered Options

- **Spotless + google-java-format (GOOGLE style)** — a Maven plugin that delegates to Google's deterministic Java formatter; `spotless:check` is configured (via a POM execution) to run in the Maven `verify` phase and `spotless:apply` auto-fixes.
- **`fmt-maven-plugin` (Spotify)** — Spotify's thin Maven wrapper around google-java-format; simpler configuration but narrower in scope (a single-language wrapper) compared to Spotless, which is a broader, actively-developed multi-language formatting framework.
- **IDE / `.editorconfig`-only** — rely on each developer's IDE to apply consistent formatting; no build-time enforcement.
- **Do nothing** — accept inconsistent formatting and resolve style disagreements in code review.

## Decision Outcome

Adopt **Spotless** with the **google-java-format engine (GOOGLE style)**.

Bind `spotless:check` to the Maven `verify` lifecycle phase so that `mvn verify` fails locally and in CI if any file is unformatted. `spotless:apply` is the canonical local auto-fix command. Zero unformatted files are tolerated at merge time.

Spotless is the right choice on every driver: it produces fully deterministic output (zero diff noise), ships a first-class `apply` goal (auto-fixable), integrates into `mvn verify` by configuration (single source of truth), and is the most widely-used Java formatting plugin in the Maven ecosystem (familiarity). The google-java-format engine is opinionated and intentionally non-configurable, which eliminates the meta-debate about formatter settings entirely.

## Consequences

- **Positive**
  - Uniform formatting from the first commit; no formatting debt ever accrues.
  - `spotless:apply` means contributors spend no manual effort on compliance.
  - `mvn verify` is the same gate locally and in CI; no per-developer IDE setup is required.
  - google-java-format is non-configurable by design, so there is nothing to debate or drift.
- **Negative**
  - Spotless may overlap in scope with any style or static-analysis tooling the project adopts; in rare edge cases the tools may disagree, resolved by reformatting (`spotless:apply`) or a narrow Spotless exclusion rather than by an inline suppression.
  - Adds a build step to `mvn verify`, increasing its wall-clock time slightly.

## Pros and Cons of the Options

### Spotless + google-java-format (GOOGLE style)

- Pros: deterministic and non-configurable (no settings drift); first-class Maven lifecycle integration; `apply` goal makes auto-fix trivial; actively maintained; widely used in the Java/Maven ecosystem.
- Cons: google-java-format's GOOGLE style is opinionated — contributors cannot tune it, which is mostly a feature but can feel rigid.

### `fmt-maven-plugin` (Spotify)

- Pros: simpler POM configuration; also wraps google-java-format so output is identical.
- Cons: less actively maintained than Spotless; narrower feature set; fewer adopters, meaning less community support.

### IDE / `.editorconfig`-only

- Pros: zero build overhead; no new plugin dependency.
- Cons: enforcement is entirely voluntary; different IDEs produce different output; CI cannot catch violations; diff noise accumulates immediately.

### Do nothing

- Pros: no setup cost.
- Cons: style debates consume review time; inconsistent formatting pollutes diffs and makes history harder to read; the problem only grows as the codebase grows.

## Links

- [`000001-adr-process-and-structure.md`](000001-adr-process-and-structure.md) — ADR process and structure.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework this formatter targets.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build tool whose lifecycle phases enforce formatting.
