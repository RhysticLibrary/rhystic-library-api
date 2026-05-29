# Design: Code-Quality Tooling ADRs

**Date:** 2026-05-29
**Status:** Approved (pending implementation)

## Goal

Record, as five ADRs, the decision to adopt a code-quality toolchain for
`rhystic-library-api` and the exact enforcement contract each tool carries.
The tools are **Spotless** (formatting), **Checkstyle** (style), **SpotBugs**
(bug static analysis), **FindSecBugs** (security static analysis), and
**JaCoCo** (test-coverage gate).

Consistent with the project's practice of recording foundational stack choices
before application code lands (see `000001`–`000008`), these ADRs codify the
quality bar now — before there is Java source to retrofit — so the gates are in
place the moment the first class is written.

This design covers the ADRs only. Wiring the actual Maven plugins into a
`pom.xml` is a downstream implementation concern that these ADRs govern but do
not themselves perform.

## Scope

In scope:

- Five new ADRs, authored as **Proposed** for review:
  - `000009` — Spotless + google-java-format (formatting)
  - `000010` — Checkstyle + stock `google_checks.xml` (style)
  - `000011` — SpotBugs (bug static analysis)
  - `000012` — FindSecBugs (security static analysis; SpotBugs plugin)
  - `000013` — JaCoCo 90% coverage gate
- One new ADR tag, `quality`, added to `docs/adr/_tags.md`.
- The `security` tag (already present) additionally applied to `000012`.

Out of scope:

- The `pom.xml` itself and the concrete plugin configuration blocks. These ADRs
  state *what* is enforced and *where*; the implementing build change wires it.
  There is no `pom.xml` in the repo yet.
- Tool versions. Delegated to dependency tooling and routine upgrades, mirroring
  the version-agnostic stance of `000003` (Java/Spring Boot) and `000004`
  (Maven). A version bump does not require a new ADR.
- Pre-commit hook changes. The Maven `verify` binding is the source of truth;
  pre-commit stays scoped to fast/format checks and is not modified by these
  ADRs.
- A custom Checkstyle ruleset or curated SpotBugs filter file. Start from stock
  configuration; introduce project-specific tuning only when a concrete false
  positive or false negative justifies it.

## Decision Drivers

- **Greenfield leverage.** With no legacy code, a zero-violation baseline is
  free to adopt and cheapest to maintain. Every gate starts clean.
- **Single source of truth.** Contributors, IDEs, and CI must all agree on
  pass/fail. Binding gates to the Maven `verify` lifecycle makes `mvn verify`
  authoritative everywhere.
- **Team familiarity and ecosystem fit.** The chosen tools are the conventional
  Maven/Spring quality stack with abundant documentation and first-class plugin
  support — the same familiarity argument that anchored `000003` and `000004`.
- **Defense across concerns.** Formatting, style, bug patterns, security bug
  patterns, and coverage are distinct failure modes; each warrants its own gate
  and its own recorded decision.

## Cross-Cutting Decisions

These apply to all five ADRs and are stated once here; each ADR restates the
part relevant to it.

### Enforcement: Maven `verify` + CI

Each tool is a Maven plugin bound to the `verify` lifecycle phase, configured to
fail the build on violation. `mvn verify` therefore fails identically on a
developer machine and in CI; CI re-runs `verify` as the unbypassable gate. This
is the single source of truth. Every ADR references `000004` (Maven, the
enforcement substrate) and `000003` (Java/Spring Boot, the language/framework
the tools analyze).

### Posture: zero-violation baseline

On greenfield code the gates start strict:

- **Checkstyle** — severity `error`, fail on any violation.
- **SpotBugs** — `effort=Max`, `threshold=Low` (report everything), fail on any
  bug instance.
- **FindSecBugs** — full security rule pack, fail on any finding.
- **Spotless** — `spotless:check` fails on any unformatted file; `spotless:apply`
  is the local auto-fix.
- **JaCoCo** — see `000013`.

Suppressions are permitted but must be explicit and justified at the suppression
site (annotation or filter entry with a reason), never a blanket relaxation of a
gate.

### Reference-direction constraint

An ADR may reference only **earlier** ADRs by id, never a later one (an immutable
ADR cannot point at something that did not yet exist). This shapes the
cross-links below: the Spotless/Checkstyle overlap is discussed in `000010`
(Checkstyle) pointing back to `000009` (Spotless), not the reverse; and `000012`
(FindSecBugs) references `000011` (SpotBugs) as its dependency.

## The Five ADRs

### 000009 — Spotless (google-java-format)

**Decision.** Adopt Spotless with the `google-java-format` (GOOGLE style) engine
as the project's code formatter. `spotless:check` is bound to `verify` and fails
on any unformatted file; `spotless:apply` is the canonical local auto-fix.

**References (earlier only):** `000003`, `000004`. Does **not** link to
Checkstyle (`000010` is later); it may describe its formatting scope but not
cross-reference the overlap by id.

**Considered options:** `fmt-maven-plugin` (spotify) — narrower, formatter-only;
IDE/`.editorconfig`-only — not enforceable in CI; Checkstyle-only formatting
checks — reports but does not auto-fix; do nothing.

### 000010 — Checkstyle (stock `google_checks.xml`)

**Decision.** Adopt the `maven-checkstyle-plugin` running the bundled, unmodified
`google_checks.xml`, severity `error`, bound to `verify`, failing on any
violation. Run alongside Spotless, **accepting the known overlap** between
google-java-format and `google_checks.xml`; the two are designed to be
compatible, and occasional friction (Javadoc, import order) is suppressed
case-by-case rather than by forking the ruleset.

**References (earlier only):** `000003`, `000004`, and **`000009`** — the ADR
that owns formatting and the basis for the overlap discussion.

**Considered options:** PMD — overlapping but different rule philosophy; rely on
Spotless only — drops naming/Javadoc/structural style rules Spotless does not
cover; Error Prone — compile-time, heavier integration; do nothing.

### 000011 — SpotBugs

**Decision.** Adopt the `spotbugs-maven-plugin` at `effort=Max`,
`threshold=Low`, bound to `verify`, failing on any reported bug instance.
SpotBugs is the maintained successor to the abandoned FindBugs.

**References (earlier only):** `000003`, `000004`.

**Considered options:** PMD — source-level, complementary but not a substitute
for bytecode bug detection; Error Prone — compile-time analysis, larger build
integration; do nothing.

### 000012 — FindSecBugs

**Decision.** Add the FindSecBugs security rule pack as a SpotBugs plugin (it is
not a standalone tool), running at full strength within the same `verify`-bound
SpotBugs execution and failing on any security finding. Tagged `quality` **and**
`security`.

**References (earlier only):** `000002` (secrets posture / security stance),
`000003`, `000004`, and **`000011`** — the SpotBugs ADR it depends on and
extends.

**Considered options:** OWASP Dependency-Check — different scope (vulnerable
*dependencies*, not first-party code); Snyk/Semgrep — SaaS or separate ecosystem
for code-level security; do nothing.

### 000013 — JaCoCo (90% coverage gate)

**Decision.** Adopt the `jacoco-maven-plugin` with the `check` goal bound to
`verify`, enforcing **90% LINE and 90% BRANCH coverage as a project-wide
aggregate**. Exclusions cover generated and untestable boilerplate: the Spring
`@SpringBootApplication` main class, plain DTO/config classes, and generated
artifacts. The build fails when either counter falls below 90%.

**References (earlier only):** `000003`, `000004`.

**Considered options:** Cobertura — effectively unmaintained; no coverage gate —
no regression protection; a lower threshold — weaker bar without a greenfield
justification; per-class rule — rejected in favor of the project-wide aggregate.

## Consequences

**Positive**

- A complete, recorded quality bar exists before the first class is written;
  every contribution clears it from commit one.
- `mvn verify` is the single authority — IDE, CLI, and CI cannot disagree.
- Each tool's decision is independently reviewable and independently
  supersedable, matching the one-decision-per-ADR precedent.
- Security static analysis (FindSecBugs) is explicitly tied to the existing
  security posture (`000002`).

**Negative**

- Five gates add build time and a steeper initial contribution friction;
  greenfield timing keeps the remediation cost near zero, but the friction is
  real.
- Stock-config overlap between Spotless and Checkstyle will occasionally require
  a justified suppression rather than a clean pass.
- A strict 90% line+branch aggregate can pressure contributors toward
  low-value tests for hard-to-reach branches; the exclusion list is the relief
  valve and must be curated honestly.
- These ADRs presuppose a `pom.xml` that does not yet exist; the implementing
  build change is a separate, dependent piece of work.

## Implementation Notes

**Use the existing ADR tooling, not hand-editing.** The `creating-an-adr` skill
and the helper scripts under `tools/adr/` are the supported path; they enforce
frontmatter shape, alphabetical tag ordering, and merge-gate compliance, and
read only frontmatter so they cost far fewer tokens than reading whole files.

- Add the `quality` tag once, first:
  `python tools/adr/add_tag.py quality "Decisions about code quality enforcement: formatting, style, static analysis, and test-coverage gates."`
- Scaffold each ADR with `python tools/adr/new_adr.py <slug>` — do not copy
  `_template.md` by hand. The script assigns the next id; author the five in
  order so ids land `000009`–`000013`. Provisional slugs:
  `spotless-code-formatting`, `checkstyle-style-enforcement`,
  `spotbugs-static-analysis`, `findsecbugs-security-analysis`,
  `jacoco-coverage-gate`.
- Leave each ADR at status `Proposed` with `date-accepted` empty for review.
  Do **not** flip to `Accepted` in this work.
- Run `python tools/adr/validate.py` before opening the PR.

Concrete artifacts the implementing PR will touch:

- `docs/adr/000009-spotless-code-formatting.md`
- `docs/adr/000010-checkstyle-style-enforcement.md`
- `docs/adr/000011-spotbugs-static-analysis.md`
- `docs/adr/000012-findsecbugs-security-analysis.md`
- `docs/adr/000013-jacoco-coverage-gate.md`
- `docs/adr/_tags.md` — `quality` tag added via `add_tag.py`.

(Exact ids are whatever `new_adr.py` assigns at scaffold time; `000009`–`000013`
assuming no other ADR lands first.)

## Open Questions

- The precise JaCoCo exclusion list. The design names the categories (main
  class, DTOs/config, generated artifacts); the exact package/class globs are
  finalized when the `pom.xml` and package layout exist, and may be refined in
  the implementing build change without amending this ADR.
