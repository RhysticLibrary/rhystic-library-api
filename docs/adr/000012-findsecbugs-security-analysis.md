---
id: "000012"
name: findsecbugs-security-analysis
description: Add the FindSecBugs security rule pack as a SpotBugs plugin, enforced via `mvn verify`, failing on any security finding.
status: Proposed
date-proposed: "2026-05-29"
date-accepted: ""
date-invalidated: ""
supersedes: []
superseded-by: []
tags: [quality, security]
---

# ADR 000012: FindSecBugs for Security Static Analysis

| Field            | Value                                |
|------------------|--------------------------------------|
| Status           | Proposed                             |
| Date Proposed    | 2026-05-29                           |
| Date Accepted    | —                                    |
| Date Invalidated | —                                    |
| Authors          | Steven Timothy                       |
| Supersedes       | —                                    |
| Superseded By    | —                                    |
| Tags             | quality, security                    |

## Context and Problem Statement

[`000011`](000011-spotbugs-static-analysis.md) adopted SpotBugs to catch correctness bugs — null dereferences, resource leaks, broken `equals`/`hashCode` contracts — at the bytecode level. SpotBugs's stock detectors are not designed for security-specific patterns, however. Injection vulnerabilities, weak or broken cryptographic choices, insecure deserialization, path traversal, and similar anti-patterns require a dedicated rule pack to surface.

FindSecBugs is a SpotBugs **plugin** — a security rule pack that layers additional detectors on top of the existing SpotBugs execution. It is not a standalone tool or separate analysis engine; it extends the configuration already established in `000011` at negligible additional cost.

The project is greenfield (Java and Spring Boot, [`000003`](000003-java-spring-boot-application-framework.md); Maven, [`000004`](000004-maven-build-tool.md)), making this the cheapest moment to adopt a zero-violation security baseline: no existing codebase to retrofit, no accumulated suppressions to inherit. Adopting it now means every future line of first-party code is written against the gate.

FindSecBugs also complements the project's no-secrets-in-VCS security posture established in [`000002`](000002-secrets-in-version-control.md). That ADR guards against secrets entering the repository; FindSecBugs guards against insecure coding patterns in the application logic itself — the two operate at different layers and reinforce each other.

## Decision Drivers

- **Detect security-specific anti-patterns in first-party code.** SpotBugs's stock detectors leave a meaningful class of security findings unexamined; those gaps need to be closed.
- **Reuse the existing SpotBugs execution.** FindSecBugs is a plugin to the execution already adopted in `000011` — no new analysis engine, no new Maven plugin, no second `verify`-phase tool to configure and maintain.
- **Extend the project's established security posture.** [`000002`](000002-secrets-in-version-control.md) set a clear security stance at the repository level; automated code-level security checks reinforce that stance in the application layer.
- **Single source of truth via `mvn verify`.** Keeping the security gate inside the existing Maven lifecycle ensures local and CI enforcement are identical with no additional invocation.

## Considered Options

- **FindSecBugs (SpotBugs plugin)** — a security rule pack that runs inside the existing SpotBugs execution; detects injection, weak cryptography, insecure deserialization, path traversal, and similar patterns in first-party code.
- **OWASP Dependency-Check** — scans third-party dependencies against known CVE databases; a different scope (vulnerable dependencies) rather than first-party code analysis.
- **Snyk / Semgrep** — capable tools, but Snyk is SaaS-backed (external service dependency, account required) and Semgrep is a separate analysis engine and ecosystem outside the established Maven/SpotBugs workflow.
- **Do nothing** — rely solely on the existing correctness gate from `000011` and developer judgment for security patterns.

## Decision Outcome

Add **FindSecBugs** as a plugin to the SpotBugs execution established in [`000011`](000011-spotbugs-static-analysis.md). It runs at full strength within that same `verify`-bound execution, adding its security detectors alongside SpotBugs's existing correctness detectors. The build fails on any security finding.

FindSecBugs is the natural fit because it extends the tool and configuration already in place rather than introducing a second analysis engine. The other options either address a different scope (OWASP Dependency-Check covers dependency vulnerabilities, not first-party code) or introduce a new engine and ecosystem dependency (Snyk, Semgrep) that is not justified when the SpotBugs plugin path is available.

Scope is first-party code analysis only. Vulnerable-dependency scanning — e.g., OWASP Dependency-Check or a comparable tool — is a separate, undecided concern and is explicitly out of scope for this ADR. Suppressions are permitted but must be explicit and justified at the suppression site, consistent with the suppression policy established in `000011`.

## Consequences

- **Positive**
  - Adds security static analysis — injection, weak cryptography, insecure deserialization, path traversal, and related patterns — with no new analysis engine; it rides the existing SpotBugs gate from `000011`.
  - Reinforces the security stance established in [`000002`](000002-secrets-in-version-control.md) with automated, code-level checks that run on every `mvn verify`.
  - Local and CI enforcement are identical — both run `mvn verify` — consistent with the single-source-of-truth principle carried through from `000011`.
  - Zero-violation security baseline is established from the first commit on greenfield code; there is no backlog to clear.
- **Negative**
  - Security detectors raise false positives that require justified suppressions rather than silent dismissal; the suppression overhead is higher than for pure correctness detectors.
  - Does **not** cover dependency vulnerabilities — that gap is acknowledged and deferred to a separate future decision.
  - Shares SpotBugs's post-compile timing: analysis runs after `compile`, which is later in the cycle than a source-level or compile-time checker.

## Pros and Cons of the Options

### FindSecBugs (SpotBugs plugin)

- Pros: runs inside the existing SpotBugs execution with no new engine or Maven plugin; broad security detector coverage (injection, crypto, deserialization, traversal); zero additional `verify`-phase configuration beyond declaring the plugin dependency.
- Cons: security detectors produce more false positives than correctness detectors, requiring a managed suppression workflow; does not cover third-party dependency vulnerabilities.

### OWASP Dependency-Check

- Pros: detects known CVEs in third-party dependencies — a real and distinct risk surface; Maven plugin available.
- Cons: addresses a different scope entirely (vulnerable dependencies, not first-party code security patterns); not a substitute for FindSecBugs and not the gap this ADR is closing.

### Snyk / Semgrep

- Pros: powerful tools with broad rule sets; Semgrep supports custom rules; Snyk covers both code and dependency scanning.
- Cons: Snyk is SaaS-backed, adding an external service dependency and account requirement to the security path; Semgrep is a separate analysis engine and ecosystem outside the established Maven/SpotBugs workflow; neither reuses the existing SpotBugs execution.

### Do nothing

- Pros: no additional suppression overhead; no change to build configuration.
- Cons: security-specific anti-patterns in first-party code go undetected until runtime or review; the greenfield window for a zero-cost strict baseline is lost.

## Links

- [`000002-secrets-in-version-control.md`](000002-secrets-in-version-control.md) — the no-secrets security posture this ADR extends at the code-analysis layer.
- [`000003-java-spring-boot-application-framework.md`](000003-java-spring-boot-application-framework.md) — language and framework this analysis gate operates on.
- [`000004-maven-build-tool.md`](000004-maven-build-tool.md) — build tool through which the gate is enforced.
- [`000011-spotbugs-static-analysis.md`](000011-spotbugs-static-analysis.md) — the SpotBugs execution this ADR extends with the FindSecBugs rule pack.
