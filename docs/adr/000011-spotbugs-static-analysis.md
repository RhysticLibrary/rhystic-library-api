---
id: "000011"
name: spotbugs-static-analysis
description: Adopt SpotBugs at max effort and low threshold, enforced via `mvn verify`, failing on any reported bug.
status: Accepted
date-proposed: "2026-05-29"
date-accepted: "2026-05-29"
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [quality]
---

# ADR 000011: SpotBugs for Bug Static Analysis

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

`rhystic-library-api` has adopted formatting and style gates ([Checkstyle](000010-checkstyle-style-enforcement.md), [Spotless / google-java-format](000009-spotless-code-formatting.md)) to keep the codebase consistent, but those tools operate on source text — they do not catch latent bug patterns that only become visible in compiled bytecode. Null dereferences, resource leaks, broken `equals`/`hashCode` contracts, and similar defects require bytecode-level static analysis to surface before they reach runtime.

The project is greenfield (see [`000003`](000003-java-spring-boot-application-framework.md) and [`000004`](000004-maven-build-tool.md)), which makes this the cheapest moment to adopt a zero-violation baseline: there is no existing codebase to retrofit and no accumulated suppressions to inherit. Establishing the gate now means every future line of code is written against it.

The build substrate is Maven ([`000004`](000004-maven-build-tool.md)) and the application language is Java ([`000003`](000003-java-spring-boot-application-framework.md)).

## Decision Drivers

- **Catch bug patterns before they reach runtime.** Bytecode analysis finds a class of defects that source-level style gates cannot see.
- **Use actively maintained tooling.** SpotBugs is the actively maintained successor to the abandoned FindBugs project; it receives regular updates and has broad plugin ecosystem support.
- **A strict baseline is cheapest on greenfield code.** Adopting `effort=Max` / `threshold=Low` now costs nothing retroactively; the same decision on a mature codebase would require addressing a backlog of findings.
- **Single source of truth via `mvn verify`.** Running the gate through Maven's standard lifecycle keeps local and CI enforcement identical and avoids a separate tool invocation.

## Considered Options

- **`spotbugs-maven-plugin`** — bytecode analysis; actively maintained; native Maven integration; configurable effort and threshold; rich plugin ecosystem.
- **PMD** — source-level analysis; catches style and structural issues; does not substitute for bytecode bug detection.
- **Error Prone** — compile-time checker integrated into `javac`; catches certain bug patterns at compilation but requires heavier build integration and a different configuration model.
- **Do nothing** — rely solely on the existing format/style gates and developer judgment.

## Decision Outcome

Adopt the **`spotbugs-maven-plugin`**, configured via a POM execution to run in the Maven `verify` phase at `effort=Max` and `threshold=Low` (report everything), failing the build on any reported bug instance.

SpotBugs is the maintained successor to the abandoned FindBugs, which makes it the natural choice for JVM bytecode analysis. Running at `effort=Max` causes SpotBugs to apply its most thorough analysis algorithms; `threshold=Low` ensures no finding is silently dropped by a confidence filter. Together, these settings surface the maximum number of issues while the codebase is small enough that each finding can be assessed individually.

Suppressions are permitted but must be explicit and justified at the suppression site — via annotation or filter entry, with a stated reason — never a blanket relaxation of the gate. This preserves the value of the gate while acknowledging that some findings will be intentional design choices or acceptable trade-offs.

SpotBugs also supports a plugin ecosystem that allows additional detectors to be layered in as separate dependencies, providing a path to extend coverage without changing the core gate configuration.

## Consequences

- **Positive**
  - Catches a class of defects (the same kinds noted in Context) that the format and style gates miss entirely.
  - `effort=Max` / `threshold=Low` (where `Low` is the minimum confidence level a finding must reach to be reported, so the lowest setting reports the most findings) surfaces the most issues while the codebase is small, making the cost of adoption lowest now.
  - Local and CI enforcement are identical: both run `mvn verify`.
  - Zero-violation baseline is established from the first commit; there is no backlog to clear.
- **Negative**
  - `effort=Max` / `threshold=Low` raises more false positives than a lenient configuration; each requires a justified suppression rather than silent dismissal.
  - Adds build time: SpotBugs analyzes compiled bytecode, so it runs after compilation and slows the `verify` phase.
  - Because analysis is bytecode-level, the tool runs after `compile` — it cannot catch problems as early in the cycle as a source-level or compile-time checker.

## Pros and Cons of the Options

### `spotbugs-maven-plugin`

- Pros: bytecode analysis catches defects invisible to source-level tools; actively maintained; native Maven integration; configurable effort and threshold; extensible plugin ecosystem.
- Cons: runs after compilation, so slower feedback than compile-time checkers; higher false-positive rate at strict settings requires managed suppressions.

### PMD

- Pros: source-level analysis with broad rule sets covering style, design, and some bug-prone patterns; fast feedback before compilation.
- Cons: operates on source text, not bytecode — complementary to SpotBugs but not a substitute for detecting bytecode-level bug patterns.

### Error Prone

- Pros: compile-time checker integrated into `javac`; finds certain bug patterns at the earliest possible stage; zero additional build phase.
- Cons: heavier build integration (requires compiler flag wiring); different configuration model; operates at compile time on source/AST rather than on bytecode, so its detector coverage is complementary to — not a superset or subset of — SpotBugs's.

### Do nothing

- Pros: no additional build time; no suppression overhead.
- Cons: an entire class of detectable defects goes unexamined until runtime; the greenfield window for a zero-cost strict baseline is lost.

## Links

- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework this analysis gate operates on.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build tool through which the gate is enforced.
