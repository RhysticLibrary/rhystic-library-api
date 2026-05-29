# Code-Quality Tooling ADRs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author five ADRs (Proposed) recording the adoption and enforcement contract of Spotless, Checkstyle, SpotBugs, FindSecBugs, and JaCoCo.

**Architecture:** Each tool gets its own immutable ADR following `docs/adr/_template.md`, authored via the project's `tools/adr/` scripts (never hand-copied). A new `quality` tag is introduced first so all five validate. ADRs land as `Proposed` for human review; status is NOT flipped to `Accepted` in this work. Reference-direction rule: an ADR may cite only earlier ids.

**Tech Stack:** Markdown ADRs; Python helper scripts under `tools/adr/` (`add_tag.py`, `new_adr.py`, `validate.py`, `list_adrs.py`) run inside the repo's `.venv`.

**Spec:** `docs/superpowers/specs/2026-05-29-code-quality-adrs-design.md`

---

## Conventions for every task

- Activate the venv once per shell session: `source .venv/bin/activate`.
- "Verify" in this plan means running the ADR validator — it is the same check
  the CI `adr-validate` job runs. There is no application test suite involved.
- Author content directly into the scaffolded file with the editor; do not
  leave any `TODO`/`{{...}}` template tokens behind — `validate.py` and
  markdownlint will flag them.
- Each ADR's frontmatter stays `status: Proposed` with `date-accepted: ""`.
- Commit after each ADR so review is per-file.

---

### Task 1: Add the `quality` tag

**Files:**
- Modify: `docs/adr/_tags.md`

- [ ] **Step 1: Add the tag via the script (not by hand)**

```bash
source .venv/bin/activate
python tools/adr/add_tag.py quality "Decisions about code quality enforcement: formatting, style, static analysis, and test-coverage gates."
```

- [ ] **Step 2: Verify the tag landed alphabetically (between `process` and `security`)**

Run: `python tools/adr/list_tags.py`
Expected: output includes `quality` listed between `process` and `security`.

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS (no unknown-tag or ordering errors).

- [ ] **Step 4: Commit**

```bash
git add docs/adr/_tags.md
git commit -m "Add 'quality' ADR tag"
```

---

### Task 2: ADR 000009 — Spotless (google-java-format)

**Files:**
- Create: `docs/adr/000009-spotless-code-formatting.md`

- [ ] **Step 1: Scaffold**

```bash
source .venv/bin/activate
python tools/adr/new_adr.py spotless-code-formatting
```
Expected: creates `docs/adr/000009-spotless-code-formatting.md` with id `000009`, today's `date-proposed`, status `Proposed`.

- [ ] **Step 2: Author the content**

Fill the scaffold to match `_template.md`. Required substance:

- **Frontmatter:** `description` = one sentence ("Adopt Spotless with google-java-format as the project's code formatter, enforced via `mvn verify`."); `tags: [quality]`; `status: Proposed`; `date-accepted: ""`.
- **Title:** `# ADR 000009: Spotless for Code Formatting`
- **Status table:** Status `Proposed`, Date Accepted `—`, Authors `Steven Timothy`, Tags `quality`.
- **Context and Problem Statement:** greenfield project recording its quality bar before code lands (cite `000001`); a consistent, automatically-applied format eliminates style debate and diff noise; enforcement substrate is Maven (`000004`) analyzing Java (`000003`). Tool version is out of scope (delegated to dependency tooling, per `000004`).
- **Decision Drivers:** zero-diff-noise formatting; auto-fixable so it costs contributors nothing; single source of truth via `mvn verify`; ecosystem familiarity.
- **Considered Options:** Spotless + google-java-format (GOOGLE style); `fmt-maven-plugin` (Spotify); IDE/`.editorconfig`-only; do nothing.
- **Decision Outcome:** Adopt Spotless with the `google-java-format` engine (GOOGLE style). Bind `spotless:check` to the `verify` lifecycle so it fails `mvn verify` locally and in CI; `spotless:apply` is the canonical local auto-fix. Zero unformatted files tolerated.
- **Consequences:** Positive — uniform formatting from commit one, auto-fix means near-zero friction, CI and local agree. Negative — overlaps partially with the style checker adopted separately (occasional suppression), adds a build step.
- **Pros and Cons of the Options:** cover Spotless vs `fmt-maven-plugin` vs IDE-only.
- **Links:** `000003`, `000004`. **Do NOT link Checkstyle** — `000010` is a later id; the reference-direction rule forbids it.

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS. No `{{...}}` tokens, no `TODO`, tag known, frontmatter well-formed.

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000009-spotless-code-formatting.md
git commit -m "Add ADR 000009: Spotless for code formatting"
```

---

### Task 3: ADR 000010 — Checkstyle (stock `google_checks.xml`)

**Files:**
- Create: `docs/adr/000010-checkstyle-style-enforcement.md`

- [ ] **Step 1: Scaffold**

```bash
source .venv/bin/activate
python tools/adr/new_adr.py checkstyle-style-enforcement
```
Expected: creates `docs/adr/000010-checkstyle-style-enforcement.md` with id `000010`.

- [ ] **Step 2: Author the content**

- **Frontmatter:** `description` = "Adopt Checkstyle with the stock google_checks.xml, enforced via `mvn verify`, accepting overlap with Spotless."; `tags: [quality]`; `status: Proposed`; `date-accepted: ""`.
- **Title:** `# ADR 000010: Checkstyle for Style Enforcement`
- **Status table:** as for 000009, Tags `quality`.
- **Context and Problem Statement:** formatting (`000009`) covers layout but not naming, Javadoc presence, and structural style rules; Checkstyle enforces those. Substrate Maven (`000004`), language Java (`000003`).
- **Decision Drivers:** enforce non-format style (naming, Javadoc, structure); stock Google config = no bespoke ruleset to maintain; single source of truth via `mvn verify`; familiarity.
- **Considered Options:** `maven-checkstyle-plugin` + stock `google_checks.xml`; PMD; rely on Spotless only; Error Prone; do nothing.
- **Decision Outcome:** Adopt `maven-checkstyle-plugin` running the bundled, unmodified `google_checks.xml`, severity `error`, bound to `verify`, fail on any violation. Run alongside Spotless (`000009`), **accepting the known overlap** between google-java-format and `google_checks.xml`; they are designed to be compatible, and occasional friction (Javadoc, import order) is suppressed case-by-case rather than by forking the ruleset.
- **Consequences:** Positive — catches style classes Spotless does not; stock config is zero-maintenance; CI/local agree. Negative — overlap with Spotless can produce occasional conflicting expectations needing a justified suppression; adds a build step.
- **Pros and Cons of the Options:** Checkstyle vs PMD vs Spotless-only.
- **Links:** `000003`, `000004`, **`000009`** (formatting decision and the basis for the overlap discussion — earlier id, allowed).

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000010-checkstyle-style-enforcement.md
git commit -m "Add ADR 000010: Checkstyle for style enforcement"
```

---

### Task 4: ADR 000011 — SpotBugs

**Files:**
- Create: `docs/adr/000011-spotbugs-static-analysis.md`

- [ ] **Step 1: Scaffold**

```bash
source .venv/bin/activate
python tools/adr/new_adr.py spotbugs-static-analysis
```
Expected: creates `docs/adr/000011-spotbugs-static-analysis.md` with id `000011`.

- [ ] **Step 2: Author the content**

- **Frontmatter:** `description` = "Adopt SpotBugs at max effort / low threshold, enforced via `mvn verify`, failing on any bug instance."; `tags: [quality]`; `status: Proposed`; `date-accepted: ""`.
- **Title:** `# ADR 000011: SpotBugs for Bug Static Analysis`
- **Status table:** as above, Tags `quality`.
- **Context and Problem Statement:** formatting and style gates do not catch latent bug patterns (null derefs, resource leaks, bad equals/hashCode). Bytecode static analysis does. Greenfield = zero-baseline is free. Substrate Maven (`000004`), language Java (`000003`).
- **Decision Drivers:** catch bug patterns before runtime; maintained tooling (SpotBugs is the FindBugs successor); strict greenfield baseline; single source of truth via `mvn verify`.
- **Considered Options:** `spotbugs-maven-plugin`; PMD; Error Prone; do nothing.
- **Decision Outcome:** Adopt `spotbugs-maven-plugin` at `effort=Max`, `threshold=Low` (report everything), bound to `verify`, fail on any reported bug instance. Note SpotBugs is the maintained successor to the abandoned FindBugs. Suppressions must be explicit and justified at the site.
- **Consequences:** Positive — catches a bug class the other gates miss; max effort surfaces the most issues while the codebase is small. Negative — max-effort/low-threshold raises false positives needing justified suppressions; adds build time.
- **Pros and Cons of the Options:** SpotBugs vs PMD vs Error Prone.
- **Links:** `000003`, `000004`.

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000011-spotbugs-static-analysis.md
git commit -m "Add ADR 000011: SpotBugs for bug static analysis"
```

---

### Task 5: ADR 000012 — FindSecBugs

**Files:**
- Create: `docs/adr/000012-findsecbugs-security-analysis.md`

- [ ] **Step 1: Scaffold**

```bash
source .venv/bin/activate
python tools/adr/new_adr.py findsecbugs-security-analysis
```
Expected: creates `docs/adr/000012-findsecbugs-security-analysis.md` with id `000012`.

- [ ] **Step 2: Author the content**

- **Frontmatter:** `description` = "Add the FindSecBugs security rule pack as a SpotBugs plugin, enforced via `mvn verify`, failing on any security finding."; `tags: [quality, security]`; `status: Proposed`; `date-accepted: ""`.
- **Title:** `# ADR 000012: FindSecBugs for Security Static Analysis`
- **Status table:** as above, Tags `quality, security`.
- **Context and Problem Statement:** SpotBugs (`000011`) finds correctness bugs but its stock rules are weak on security-specific patterns (injection, weak crypto, insecure deserialization). FindSecBugs is a SpotBugs plugin that adds those rules; it is not a standalone tool. Complements the no-secrets security posture (`000002`). Substrate Maven (`000004`), language Java (`000003`).
- **Decision Drivers:** detect security-specific anti-patterns in first-party code; reuse the SpotBugs execution already adopted (`000011`) — no new engine; extend the project's existing security posture (`000002`); single source of truth via `mvn verify`.
- **Considered Options:** FindSecBugs (SpotBugs plugin); OWASP Dependency-Check; Snyk/Semgrep; do nothing.
- **Decision Outcome:** Add the FindSecBugs security rule pack as a plugin to the SpotBugs execution from `000011`, running at full strength within the same `verify`-bound run, failing on any security finding. Note this is scoped to first-party code analysis; vulnerable-dependency scanning (e.g. OWASP Dependency-Check) is a separate concern not decided here.
- **Consequences:** Positive — security static analysis with no new engine, riding the SpotBugs gate; ties into the `000002` security stance. Negative — security rules raise false positives needing justified suppressions; does not cover dependency vulnerabilities (separate future decision).
- **Pros and Cons of the Options:** FindSecBugs vs OWASP Dependency-Check (different scope) vs Snyk/Semgrep (SaaS/separate ecosystem).
- **Links:** `000002` (security posture), `000003`, `000004`, **`000011`** (the SpotBugs ADR it depends on and extends — earlier id, allowed).

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS (both `quality` and `security` are known tags).

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000012-findsecbugs-security-analysis.md
git commit -m "Add ADR 000012: FindSecBugs for security static analysis"
```

---

### Task 6: ADR 000013 — JaCoCo coverage gate

**Files:**
- Create: `docs/adr/000013-jacoco-coverage-gate.md`

- [ ] **Step 1: Scaffold**

```bash
source .venv/bin/activate
python tools/adr/new_adr.py jacoco-coverage-gate
```
Expected: creates `docs/adr/000013-jacoco-coverage-gate.md` with id `000013`.

- [ ] **Step 2: Author the content**

- **Frontmatter:** `description` = "Adopt JaCoCo enforcing 90% line and branch coverage project-wide via `mvn verify`."; `tags: [quality]`; `status: Proposed`; `date-accepted: ""`.
- **Title:** `# ADR 000013: JaCoCo 90% Coverage Gate`
- **Status table:** as above, Tags `quality`.
- **Context and Problem Statement:** style and static-analysis gates do not measure whether code is exercised by tests. A coverage gate prevents untested code from merging. Greenfield = the bar is cheap to hold from day one. Substrate Maven (`000004`), language Java (`000003`).
- **Decision Drivers:** prevent untested code merging; line + branch together (branch catches untested conditionals line coverage hides); a single project-wide number is simple to reason about; single source of truth via `mvn verify`.
- **Considered Options:** `jacoco-maven-plugin` `check` goal at 90% line + branch project-wide; lower threshold; per-class threshold; no coverage gate; Cobertura.
- **Decision Outcome:** Adopt `jacoco-maven-plugin` with the `check` goal bound to `verify`, enforcing **90% LINE and 90% BRANCH coverage as a project-wide aggregate**. Build fails when either counter is below 90%. Exclusions cover generated/untestable boilerplate: the Spring `@SpringBootApplication` main class, plain DTO/config classes, and generated artifacts. The exact exclusion globs are finalized when the `pom.xml` and package layout exist and may be refined in the build change without amending this ADR.
- **Consequences:** Positive — enforces a tested codebase from the start; branch coverage catches untested conditionals; one number is easy to reason about. Negative — a strict aggregate can pressure low-value tests for hard-to-reach branches (the exclusion list is the relief valve and must be curated honestly); adds build time; the aggregate can mask a single weak class (accepted trade-off vs per-class strictness).
- **Pros and Cons of the Options:** project-wide aggregate vs per-class vs no gate; JaCoCo vs Cobertura (unmaintained).
- **Links:** `000003`, `000004`.

- [ ] **Step 3: Validate**

Run: `python tools/adr/validate.py`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/adr/000013-jacoco-coverage-gate.md
git commit -m "Add ADR 000013: JaCoCo 90% coverage gate"
```

---

### Task 7: Final full-set validation

**Files:** none (verification only)

- [ ] **Step 1: List ADRs and confirm the five new ids and statuses**

Run: `python tools/adr/list_adrs.py`
Expected: `000009`–`000013` present, all status `Proposed`, with the slugs above.

- [ ] **Step 2: Run the validator over the whole set**

Run: `python tools/adr/validate.py`
Expected: PASS — no unknown tags, no template tokens, frontmatter well-formed, no forbidden later-id references.

- [ ] **Step 3: Confirm reference direction by inspection**

Check the `Links` section of each new ADR cites only **lower** ids:
- 000009 → 000003, 000004 only
- 000010 → 000003, 000004, 000009
- 000011 → 000003, 000004
- 000012 → 000002, 000003, 000004, 000011
- 000013 → 000003, 000004

Expected: no ADR references an id greater than its own.

---

## Notes for the implementer

- These ADRs deliberately stop at `Proposed`. Do NOT run the merge gate or flip
  any status to `Accepted` — the human reviewer does that after reading them.
- If `new_adr.py` assigns an id other than the expected one (because another ADR
  merged first), keep authoring in sequence and adjust the cross-reference ids
  accordingly, preserving the reference-direction rule (cite only earlier ids).
- Match the prose density and section style of the existing accepted ADRs
  (`000004`–`000008`) — full sentences, concrete justification, no filler.
