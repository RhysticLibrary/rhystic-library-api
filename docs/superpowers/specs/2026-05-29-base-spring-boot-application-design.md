# Design: Base Spring Boot Application (boot module + infra endpoints)

**Date:** 2026-05-29
**Status:** Approved (brainstorming) — pending implementation plan
**Target artifact:** First application code in the repo — a Maven parent pom + `boot`
module that builds, runs, and exposes three framework-provided endpoints, plus Docker
Compose packaging.

## Summary

Stand up the first runnable slice of `rhystic-library-api`: a non-building Maven **parent
pom** and a single **`boot`** Spring Boot module (ADR
[`000015`](../../adr/000015-multi-module-domain-structure.md)). The application exposes three
infrastructure endpoints, all provided by the framework — no domain code:

- `GET /actuator/health` — Spring Boot Actuator aggregate health, with liveness/readiness
  probe groups enabled.
- `GET /v3/api-docs` — OpenAPI 3 spec (JSON) via springdoc-openapi.
- `GET /swagger-ui.html` — interactive Swagger UI via springdoc-openapi.

All five code-quality gates (ADRs [`000009`](../../adr/000009-spotless-code-formatting.md)–
[`000013`](../../adr/000013-jacoco-coverage-gate.md)) are wired into the parent and bound to
`verify`, so `./mvnw verify` is the single gate locally and in CI. The application is
containerized per ADR [`000014`](../../adr/000014-docker-compose-containerization.md) with a
multi-stage Dockerfile and the base + override Compose layering.

Persistence (MySQL/Flyway/JPA/H2) and domain modules (with the cross-domain Enforcer guard)
are **deliberately deferred** to the first data-bearing domain.

## Context

The foundational stack is fixed across prior ADRs:

- Java/Spring Boot — [`000003`](../../adr/000003-java-spring-boot-application-framework.md)
- Maven — [`000004`](../../adr/000004-maven-build-tool.md)
- MySQL — [`000005`](../../adr/000005-mysql-relational-database.md) (deferred)
- Flyway — [`000006`](../../adr/000006-flyway-schema-migrations.md) (deferred)
- Spring Data JPA / Hibernate — [`000007`](../../adr/000007-spring-data-jpa-hibernate-data-access.md) (deferred)
- H2 for tests — [`000008`](../../adr/000008-h2-test-database.md) (deferred)
- Spotless / Checkstyle / SpotBugs / FindSecBugs / JaCoCo —
  [`000009`](../../adr/000009-spotless-code-formatting.md)–[`000013`](../../adr/000013-jacoco-coverage-gate.md)
- Docker + Compose — [`000014`](../../adr/000014-docker-compose-containerization.md)
- Multi-module domain structure — [`000015`](../../adr/000015-multi-module-domain-structure.md)

Today the repo contains only ADR tooling (Python) and docs — **zero Java**. This is the
first application code to land. The only endpoints in scope are infrastructure endpoints,
which are entirely framework-provided, so no controllers, services, entities, or domains are
needed yet.

## Decisions (from brainstorming)

| Question | Decision |
|----------|----------|
| Module layout | **Parent + `boot` only.** No domain subtrees; no Enforcer banned-dependencies guard yet (nothing to guard). |
| Code-quality gates | **All five now**, in the parent, bound to `verify`. |
| Persistence | **Deferred** — lands with the first data-bearing domain. |
| Java + Spring Boot | **Java 25 LTS + Spring Boot 4.0.** Versions delegated to tooling/Dependabot thereafter. |
| OpenAPI/Swagger | **springdoc-openapi 3.0.x** (the line supporting Boot 4). |
| Health probes | **Enabled** — liveness/readiness groups exposed. |
| Tests | **Context-loads test + endpoint smoke test.** |
| Docker | **Full ADR 000014 layering now** — Dockerfile + `compose.yml` + `compose.override.yml` (local MySQL) + `compose.prod.yml` + `.env.example`. |

## Architecture

### Module layout

```text
rhystic-library-api/              parent pom — packaging=pom, builds nothing
├── pom.xml                       extends spring-boot-starter-parent (4.0);
│                                 dependencyManagement + pluginManagement + 5 quality gates
├── mvnw, mvnw.cmd, .mvn/wrapper/ Maven Wrapper (ADR 000004) → ./mvnw verify with no local Maven
├── boot/                         the only runnable artifact (ADR 000015 boot aggregator)
│   ├── pom.xml                   parent = rhystic-library-api
│   └── src/
│       ├── main/java/com/rhysticlibrary/boot/RhysticLibraryApplication.java
│       ├── main/resources/application.yml
│       └── test/java/com/rhysticlibrary/boot/
│           ├── RhysticLibraryApplicationTest.java     context-loads
│           └── InfraEndpointsSmokeTest.java           the three endpoints respond
├── Dockerfile                    multi-stage: Maven build stage → slim JRE runtime stage
├── compose.yml                   base — app service only
├── compose.override.yml          local — adds MySQL service + dev conveniences (auto-loaded)
├── compose.prod.yml              prod — app only against external MySQL, no dev conveniences
└── .env.example                  documents env var NAMES only (ADR 000002), no real values
```

- **Coordinates** (ADR 000015): groupId `com.rhysticlibrary`; artifactIds match module names
  (`rhystic-library-api`, `boot`).
- The parent **extends `spring-boot-starter-parent`** (Boot 4.0) to inherit its dependency
  and plugin management, then layers the five quality-gate plugins into its own
  `pluginManagement`/`build` so every child (today just `boot`) inherits them.
- **No domain modules** and **no Maven Enforcer cross-domain rule** yet — ADR 000015 defers
  the exact guard config, and there are no domains to isolate. A note is left for when the
  first `<domain>-impl` lands.

### boot module

- **Dependencies:** `spring-boot-starter-web`, `spring-boot-starter-actuator`,
  `springdoc-openapi-starter-webmvc-ui` (3.0.x), `spring-boot-starter-test` (test scope).
- **No datasource starter** on the classpath → Spring Boot does not auto-configure a DB.
- `RhysticLibraryApplication` — a standard `@SpringBootApplication` main class. No
  controllers; all three endpoints are framework-provided.
- `application.yml`:
  - `management.endpoint.health.probes.enabled: true` → exposes
    `/actuator/health/liveness` and `/actuator/health/readiness` alongside the aggregate
    `/actuator/health`.
  - springdoc defaults serve `/v3/api-docs` and `/swagger-ui.html` with no extra config.

### Endpoints (all framework-provided)

| Endpoint | Source | Notes |
|----------|--------|-------|
| `GET /actuator/health` | Actuator | Aggregate `{"status":"UP"}`; liveness/readiness groups enabled. |
| `GET /v3/api-docs` | springdoc | OpenAPI 3 JSON. |
| `GET /swagger-ui.html` | springdoc | Redirects to the Swagger UI bundle. |

## Testing

`spring-boot-starter-test` bundles JUnit 5 + Mockito + AssertJ — no extra test
dependencies. **AssertJ** is the assertion style throughout; **Mockito** is used where
mocking is needed (none required for these framework endpoints, but available).

- **`RhysticLibraryApplicationTest`** — `@SpringBootTest` `contextLoads()`. Proves the full
  context (web + actuator + springdoc) wires up.
- **`InfraEndpointsSmokeTest`** — `@SpringBootTest(webEnvironment = RANDOM_PORT)` +
  `TestRestTemplate`. Asserts `/actuator/health` returns `UP`, and `/v3/api-docs` and
  `/swagger-ui.html` return HTTP 200. This is the only test that actually exercises the
  three endpoints and gives the JaCoCo gate meaningful covered paths.

The `@SpringBootApplication` main class is excluded from JaCoCo per ADR 000013's named
exclusions.

## Code-quality gates (parent, bound to `verify`)

| Gate | ADR | Configuration |
|------|-----|---------------|
| Spotless | 000009 | google-java-format GOOGLE; `spotless:check` on `verify`; `spotless:apply` to fix. |
| Checkstyle | 000010 | stock `google_checks.xml`, severity=error; fail on violation. |
| SpotBugs + FindSecBugs | 000011, 000012 | `effort=Max`, `threshold=Low`, FindSecBugs plugin in the same execution; fail on any finding. |
| JaCoCo | 000013 | 90% line + branch, project-wide aggregate; exclude the main class. |

`./mvnw verify` runs compile → test → all four gates, locally and in CI.

## Docker / Compose (ADR 000014)

- **`Dockerfile`** — multi-stage: a Maven build stage compiles the `boot` jar; a runtime
  stage copies it onto a slim JRE base image.
- **`compose.yml`** — base; defines the `app` service. Configuration injected from the
  environment, never baked into the image.
- **`compose.override.yml`** — auto-loaded locally; adds a **MySQL** service + dev
  conveniences (port exposure, named volume). `docker compose up` brings up the full stack.
  *Note:* the app does not yet connect to MySQL (persistence deferred); the service runs but
  is unused until persistence lands. Full ADR 000014 structure is in place now by decision.
- **`compose.prod.yml`** — app only against an external/managed MySQL via env vars; no MySQL
  service, no dev conveniences.
- **`.env.example`** — documents variable *names* only (ADR 000002); real values live in a
  git-ignored `.env`.

## CI + Dependabot

- Add a `java-build` job to `.github/workflows/ci.yml`: `setup-java` (Temurin 25) +
  `./mvnw -B verify`.
- Add a `maven` ecosystem entry to `.github/dependabot.yml` so Java dependency and plugin
  versions get bumped automatically (honoring the version-delegation stance of the stack
  ADRs).

## Explicitly deferred (YAGNI)

- **Persistence** — MySQL/Flyway/Spring Data JPA/H2 land with the first data-bearing domain.
- **Domain modules + Enforcer cross-domain guard** — land with the first `<domain>-impl`.
- The app's actual **connection to MySQL** — wired alongside persistence; the Compose MySQL
  service is present but unused until then.

## Risks / watch-items

- **springdoc 3.0.x on Boot 4.0** — supported and works out-of-the-box, but springdoc 3.0.0
  is known to return HTTP 400 on both `/swagger-ui.html` and `/v3/api-docs` **when Spring
  Boot 4's native API versioning is enabled**. We do not use API versioning, so we are
  unaffected; pin a known-good 3.0.x patch and keep the smoke test as the guard.
- **JaCoCo 90% with almost no code** — with the main class excluded, the gate must have
  enough instrumented, covered code to be meaningful; the endpoint smoke test supplies it.
