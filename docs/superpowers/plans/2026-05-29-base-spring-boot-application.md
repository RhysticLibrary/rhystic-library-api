# Base Spring Boot Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the first runnable slice of `rhystic-library-api` — a Maven parent pom + a single `boot` Spring Boot module exposing `/actuator/health`, `/v3/api-docs`, and `/swagger-ui.html` — with all five code-quality gates and full Docker Compose packaging.

**Architecture:** A non-building parent pom (packaging `pom`, extends `spring-boot-starter-parent`) owns dependency/plugin management and the five quality gates bound to `verify`. A `boot` module is the only runnable artifact; all three endpoints are framework-provided (Spring Boot Actuator + springdoc-openapi), so there are no controllers, services, entities, or domains. Persistence and domain modules are deferred.

**Tech Stack:** Java 25, Spring Boot 4.0, Maven (wrapper), springdoc-openapi 3.0.x, JUnit 5 + AssertJ + Mockito (via `spring-boot-starter-test`), Spotless/Checkstyle/SpotBugs+FindSecBugs/JaCoCo, Docker + Docker Compose.

**Spec:** [`docs/superpowers/specs/2026-05-29-base-spring-boot-application-design.md`](../specs/2026-05-29-base-spring-boot-application-design.md)

---

## Prerequisites

- **JDK 25** must be installed and active for local builds (the spec targets Java 25; the machine currently has JDK 21). Install via e.g. `brew install --cask temurin@25` or SDKMAN (`sdk install java 25-tem`), then ensure `java -version` reports 25 (or point `JAVA_HOME` at it). CI and Docker pin Temurin 25 independently.
- **Maven 3.9+** available once to bootstrap the wrapper (confirmed present).
- **Docker** for the Docker tasks (confirmed present).

## Conventions

- Test classes use the singular `...Test` suffix (e.g., `RhysticLibraryApplicationTest`).
- All assertions use **AssertJ** (`org.assertj.core.api.Assertions.assertThat`).
- Run the build with the wrapper: `./mvnw`.
- Commit after each task. Branch is `base-spring-boot-application` (already created).

## File Structure

```text
rhystic-library-api/
├── pom.xml                                  NEW  parent pom + quality gates
├── mvnw, mvnw.cmd, .mvn/wrapper/...         NEW  Maven Wrapper
├── boot/
│   ├── pom.xml                              NEW  boot module
│   └── src/
│       ├── main/java/com/rhysticlibrary/boot/
│       │   ├── RhysticLibraryApplication.java   NEW  @SpringBootApplication
│       │   └── package-info.java                NEW  package Javadoc
│       ├── main/resources/application.yml       NEW  health probes config
│       └── test/java/com/rhysticlibrary/boot/
│           ├── RhysticLibraryApplicationTest.java   NEW  context-loads
│           └── InfraEndpointsSmokeTest.java         NEW  3 endpoints respond
├── Dockerfile                               NEW  multi-stage build
├── compose.yml                              NEW  base: app service
├── compose.override.yml                     NEW  local: + MySQL + dev conveniences
├── compose.prod.yml                         NEW  prod: app-only, external MySQL
├── .env.example                             NEW  env var names (no real values)
├── .github/workflows/ci.yml                 MODIFY  add java-build job
└── .github/dependabot.yml                   MODIFY  add maven ecosystem
```

> **Plugin/dependency versions** below are concrete starting pins for the Spring Boot 4.0 / Java 25 era; Dependabot bumps them thereafter. If a pinned version fails to resolve, use the latest available patch of that same major/minor line and note it in the commit.

---

### Task 1: Parent pom + Maven Wrapper

**Files:**
- Create: `pom.xml`
- Create: `mvnw`, `mvnw.cmd`, `.mvn/wrapper/maven-wrapper.properties` (generated)

- [ ] **Step 1: Create the parent pom**

Create `pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.0.0</version>
    <relativePath/>
  </parent>

  <groupId>com.rhysticlibrary</groupId>
  <artifactId>rhystic-library-api</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <packaging>pom</packaging>
  <name>rhystic-library-api</name>
  <description>Parent build for the Rhystic Library API.</description>

  <properties>
    <java.version>25</java.version>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <springdoc.version>3.0.3</springdoc.version>
    <spotless.version>2.43.0</spotless.version>
    <maven-checkstyle-plugin.version>3.6.0</maven-checkstyle-plugin.version>
    <checkstyle.version>10.21.0</checkstyle.version>
    <spotbugs-maven-plugin.version>4.8.6.6</spotbugs-maven-plugin.version>
    <findsecbugs.version>1.13.0</findsecbugs.version>
  </properties>

  <!-- boot module is added in Task 2 -->
  <modules>
  </modules>

  <build>
    <!-- Quality-gate plugins are added in Tasks 4-7. -->
    <plugins>
    </plugins>
  </build>
</project>
```

- [ ] **Step 2: Generate the Maven Wrapper**

Run: `mvn -N wrapper:wrapper`
Expected: creates `mvnw`, `mvnw.cmd`, and `.mvn/wrapper/maven-wrapper.properties`. (`.mvn/wrapper/maven-wrapper.jar` is gitignored — modern wrapper downloads it on first run.)

- [ ] **Step 3: Verify the wrapper runs**

Run: `./mvnw -v`
Expected: prints Apache Maven version and the active Java version. (If Java < 25, install JDK 25 per Prerequisites before later tasks.)

- [ ] **Step 4: Commit**

```bash
git add pom.xml mvnw mvnw.cmd .mvn/wrapper/maven-wrapper.properties
git commit -m "Add Maven parent pom and wrapper"
```

---

### Task 2: boot module — application + context-loads test

**Files:**
- Modify: `pom.xml` (add `<module>boot</module>`)
- Create: `boot/pom.xml`
- Create: `boot/src/main/java/com/rhysticlibrary/boot/RhysticLibraryApplication.java`
- Create: `boot/src/main/java/com/rhysticlibrary/boot/package-info.java`
- Create: `boot/src/main/resources/application.yml`
- Test: `boot/src/test/java/com/rhysticlibrary/boot/RhysticLibraryApplicationTest.java`

- [ ] **Step 1: Write the failing context-loads test**

Create `boot/src/test/java/com/rhysticlibrary/boot/RhysticLibraryApplicationTest.java`:

```java
package com.rhysticlibrary.boot;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

/** Verifies the Spring application context loads. */
@SpringBootTest
class RhysticLibraryApplicationTest {

  /** The application context should start without error. */
  @Test
  void contextLoads() {}
}
```

- [ ] **Step 2: Register the module and run the test to verify it fails**

Add the module to the parent `pom.xml` — replace:

```xml
  <modules>
  </modules>
```

with:

```xml
  <modules>
    <module>boot</module>
  </modules>
```

Run: `./mvnw -pl boot test`
Expected: FAIL — `boot/pom.xml` and the application class do not exist yet (build/compile error).

- [ ] **Step 3: Create the boot module pom**

Create `boot/pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>com.rhysticlibrary</groupId>
    <artifactId>rhystic-library-api</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <relativePath>../pom.xml</relativePath>
  </parent>

  <artifactId>boot</artifactId>
  <name>boot</name>
  <description>Spring Boot entry point that assembles and runs the application.</description>

  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springdoc</groupId>
      <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
      <version>${springdoc.version}</version>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
```

- [ ] **Step 4: Create the application class and package-info**

Create `boot/src/main/java/com/rhysticlibrary/boot/RhysticLibraryApplication.java`:

```java
package com.rhysticlibrary.boot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point that boots the Rhystic Library API. */
@SpringBootApplication
public class RhysticLibraryApplication {

  /**
   * Starts the Spring application context.
   *
   * @param args command-line arguments
   */
  public static void main(String[] args) {
    SpringApplication.run(RhysticLibraryApplication.class, args);
  }
}
```

Create `boot/src/main/java/com/rhysticlibrary/boot/package-info.java`:

```java
/** Application bootstrap package for the Rhystic Library API. */
package com.rhysticlibrary.boot;
```

- [ ] **Step 5: Create minimal application config**

Create `boot/src/main/resources/application.yml`:

```yaml
spring:
  application:
    name: rhystic-library-api
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `./mvnw -pl boot test`
Expected: PASS — `RhysticLibraryApplicationTest.contextLoads` runs green; the context wires up Actuator and springdoc.

- [ ] **Step 7: Commit**

```bash
git add pom.xml boot/pom.xml boot/src
git commit -m "Add boot module with context-loads test"
```

---

### Task 3: Endpoint smoke test + health probes

**Files:**
- Modify: `boot/src/main/resources/application.yml`
- Test: `boot/src/test/java/com/rhysticlibrary/boot/InfraEndpointsSmokeTest.java`

- [ ] **Step 1: Write the failing smoke test**

Create `boot/src/test/java/com/rhysticlibrary/boot/InfraEndpointsSmokeTest.java`:

```java
package com.rhysticlibrary.boot;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.ResponseEntity;

/** Smoke tests asserting the framework-provided infrastructure endpoints respond. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InfraEndpointsSmokeTest {

  @Autowired private TestRestTemplate restTemplate;

  /** The Actuator health endpoint reports the application is UP. */
  @Test
  void healthEndpointReportsUp() {
    ResponseEntity<String> response =
        restTemplate.getForEntity("/actuator/health", String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    assertThat(response.getBody()).contains("\"status\":\"UP\"");
  }

  /** The Actuator liveness probe group is exposed. */
  @Test
  void livenessProbeIsExposed() {
    ResponseEntity<String> response =
        restTemplate.getForEntity("/actuator/health/liveness", String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }

  /** The Actuator readiness probe group is exposed. */
  @Test
  void readinessProbeIsExposed() {
    ResponseEntity<String> response =
        restTemplate.getForEntity("/actuator/health/readiness", String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }

  /** The OpenAPI 3 spec is served as JSON. */
  @Test
  void apiDocsEndpointReturnsOpenApiJson() {
    ResponseEntity<String> response =
        restTemplate.getForEntity("/v3/api-docs", String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    assertThat(response.getBody()).contains("\"openapi\"");
  }

  /** The Swagger UI entry point responds successfully (TestRestTemplate follows the redirect). */
  @Test
  void swaggerUiEndpointResponds() {
    ResponseEntity<String> response =
        restTemplate.getForEntity("/swagger-ui.html", String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }
}
```

- [ ] **Step 2: Run to verify the probe tests fail**

Run: `./mvnw -pl boot test -Dtest=InfraEndpointsSmokeTest`
Expected: `livenessProbeIsExposed` and `readinessProbeIsExposed` FAIL with 404 — probe groups are not enabled yet. (`healthEndpointReportsUp`, `apiDocsEndpointReturnsOpenApiJson`, and `swaggerUiEndpointResponds` should already pass.)

- [ ] **Step 3: Enable the liveness/readiness probe groups**

Replace the contents of `boot/src/main/resources/application.yml` with:

```yaml
spring:
  application:
    name: rhystic-library-api

management:
  endpoint:
    health:
      probes:
        enabled: true
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `./mvnw -pl boot test -Dtest=InfraEndpointsSmokeTest`
Expected: PASS — all five smoke tests green.

- [ ] **Step 5: Commit**

```bash
git add boot/src/main/resources/application.yml boot/src/test/java/com/rhysticlibrary/boot/InfraEndpointsSmokeTest.java
git commit -m "Add infra endpoint smoke test and enable health probes"
```

---

### Task 4: Spotless code formatting gate (ADR 000009)

**Files:**
- Modify: `pom.xml` (add Spotless plugin)

- [ ] **Step 1: Add the Spotless plugin to the parent build**

In `pom.xml`, replace:

```xml
  <build>
    <!-- Quality-gate plugins are added in Tasks 4-7. -->
    <plugins>
    </plugins>
  </build>
```

with:

```xml
  <build>
    <plugins>
      <plugin>
        <groupId>com.diffplug.spotless</groupId>
        <artifactId>spotless-maven-plugin</artifactId>
        <version>${spotless.version}</version>
        <configuration>
          <java>
            <googleJavaFormat/>
          </java>
        </configuration>
        <executions>
          <execution>
            <id>spotless-check</id>
            <phase>verify</phase>
            <goals>
              <goal>check</goal>
            </goals>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
```

- [ ] **Step 2: Auto-format all sources**

Run: `./mvnw spotless:apply`
Expected: BUILD SUCCESS; any unformatted Java is rewritten to google-java-format style.

- [ ] **Step 3: Verify the gate passes**

Run: `./mvnw verify`
Expected: BUILD SUCCESS — `spotless:check` finds zero unformatted files; all tests still pass.

- [ ] **Step 4: Commit**

```bash
git add pom.xml boot/src
git commit -m "Add Spotless google-java-format gate"
```

---

### Task 5: Checkstyle style gate (ADR 000010)

**Files:**
- Modify: `pom.xml` (add Checkstyle plugin)

- [ ] **Step 1: Add the Checkstyle plugin**

In `pom.xml`, inside `<build><plugins>`, add after the Spotless plugin:

```xml
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-checkstyle-plugin</artifactId>
        <version>${maven-checkstyle-plugin.version}</version>
        <dependencies>
          <dependency>
            <groupId>com.puppycrawl.tools</groupId>
            <artifactId>checkstyle</artifactId>
            <version>${checkstyle.version}</version>
          </dependency>
        </dependencies>
        <configuration>
          <configLocation>google_checks.xml</configLocation>
          <consoleOutput>true</consoleOutput>
          <failOnViolation>true</failOnViolation>
          <violationSeverity>warning</violationSeverity>
          <includeTestSourceDirectory>false</includeTestSourceDirectory>
        </configuration>
        <executions>
          <execution>
            <id>checkstyle-check</id>
            <phase>verify</phase>
            <goals>
              <goal>check</goal>
            </goals>
          </execution>
        </executions>
      </plugin>
```

> `google_checks.xml` ships inside the `checkstyle` jar. `violationSeverity=warning` makes any google_checks finding fail the build (it emits at `warning`). Test sources are excluded (`includeTestSourceDirectory=false`), so only `src/main/java` is checked — the application class and `package-info.java`, both written with Javadoc above.

- [ ] **Step 2: Verify the gate passes**

Run: `./mvnw verify`
Expected: BUILD SUCCESS. If Checkstyle reports a violation, the console names the exact `file:line` and rule; fix it minimally (most commonly: add/adjust a Javadoc summary sentence ending in a period). Per ADR 000010, unavoidable friction is handled by a case-by-case suppression, never by modifying `google_checks.xml`.

- [ ] **Step 3: Commit**

```bash
git add pom.xml
git commit -m "Add Checkstyle google_checks gate"
```

---

### Task 6: SpotBugs + FindSecBugs static analysis gate (ADRs 000011, 000012)

**Files:**
- Modify: `pom.xml` (add SpotBugs plugin with FindSecBugs)

- [ ] **Step 1: Add the SpotBugs plugin**

In `pom.xml`, inside `<build><plugins>`, add after the Checkstyle plugin:

```xml
      <plugin>
        <groupId>com.github.spotbugs</groupId>
        <artifactId>spotbugs-maven-plugin</artifactId>
        <version>${spotbugs-maven-plugin.version}</version>
        <configuration>
          <effort>Max</effort>
          <threshold>Low</threshold>
          <plugins>
            <plugin>
              <groupId>com.h3xstream.findsecbugs</groupId>
              <artifactId>findsecbugs-plugin</artifactId>
              <version>${findsecbugs.version}</version>
            </plugin>
          </plugins>
        </configuration>
        <executions>
          <execution>
            <id>spotbugs-check</id>
            <phase>verify</phase>
            <goals>
              <goal>check</goal>
            </goals>
          </execution>
        </executions>
      </plugin>
```

> SpotBugs analyzes compiled `target/classes` (main code only, not tests). FindSecBugs runs as a detector plugin inside the same execution, inheriting `effort=Max`/`threshold=Low`.

- [ ] **Step 2: Verify the gate passes**

Run: `./mvnw verify`
Expected: BUILD SUCCESS — no bug instances on the single `@SpringBootApplication` main class. If a finding appears, fix it; if it is an intentional design choice, suppress it explicitly and justified at the site (a `@SuppressFBWarnings` annotation or a `spotbugs-exclude.xml` filter), per ADRs 000011/000012 — never relax the gate globally.

- [ ] **Step 3: Commit**

```bash
git add pom.xml
git commit -m "Add SpotBugs and FindSecBugs static-analysis gate"
```

---

### Task 7: JaCoCo coverage gate (ADR 000013)

**Files:**
- Modify: `pom.xml` (add JaCoCo plugin)

- [ ] **Step 1: Add the JaCoCo plugin**

In `pom.xml`, inside `<build><plugins>`, add after the SpotBugs plugin (the `jacoco-maven-plugin` version is managed by `spring-boot-starter-parent`):

```xml
      <plugin>
        <groupId>org.jacoco</groupId>
        <artifactId>jacoco-maven-plugin</artifactId>
        <executions>
          <execution>
            <id>jacoco-prepare-agent</id>
            <goals>
              <goal>prepare-agent</goal>
            </goals>
          </execution>
          <execution>
            <id>jacoco-check</id>
            <phase>verify</phase>
            <goals>
              <goal>check</goal>
            </goals>
            <configuration>
              <excludes>
                <exclude>com/rhysticlibrary/boot/RhysticLibraryApplication.class</exclude>
                <exclude>com/rhysticlibrary/boot/package-info.class</exclude>
              </excludes>
              <rules>
                <rule>
                  <element>BUNDLE</element>
                  <limits>
                    <limit>
                      <counter>LINE</counter>
                      <value>COVEREDRATIO</value>
                      <minimum>0.90</minimum>
                    </limit>
                    <limit>
                      <counter>BRANCH</counter>
                      <value>COVEREDRATIO</value>
                      <minimum>0.90</minimum>
                    </limit>
                  </limits>
                </rule>
              </rules>
            </configuration>
          </execution>
        </executions>
      </plugin>
```

> The `@SpringBootApplication` main class and `package-info` are excluded per ADR 000013's named exclusions. With no other application classes yet, the bundle has no instrumented lines, so the 90% line/branch rule is satisfied vacuously. The gate becomes meaningful when the first real class lands.

- [ ] **Step 2: Verify the full gate passes**

Run: `./mvnw verify`
Expected: BUILD SUCCESS — Spotless, Checkstyle, SpotBugs+FindSecBugs, and JaCoCo all pass; all tests green. `./mvnw verify` is now the single gate.

- [ ] **Step 3: Commit**

```bash
git add pom.xml
git commit -m "Add JaCoCo 90% coverage gate"
```

---

### Task 8: Multi-stage Dockerfile (ADR 000014)

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create the Dockerfile**

Create `Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1

# ---- Build stage: compile the executable jar with the Maven toolchain ----
FROM eclipse-temurin:25-jdk AS build
WORKDIR /workspace

COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
COPY boot/pom.xml boot/pom.xml
COPY boot/src boot/src

# Tests run in CI, not in the image build.
RUN ./mvnw -B -pl boot -am clean package -DskipTests

# ---- Runtime stage: slim JRE with just the jar ----
FROM eclipse-temurin:25-jre AS runtime
WORKDIR /app
RUN useradd --system --uid 1001 spring
USER spring
COPY --from=build /workspace/boot/target/boot-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

> `package` (not `verify`) is used so the image build skips the quality gates and tests — those run in CI via `./mvnw verify`. The `boot-*.jar` glob matches the repackaged executable jar but not `boot-*.jar.original`.

- [ ] **Step 2: Build the image**

Run: `docker build -t rhystic-library-api:latest .`
Expected: BUILD SUCCESS; image `rhystic-library-api:latest` is created.

- [ ] **Step 3: Smoke-test the container**

Run:
```bash
docker run --rm -d -p 8080:8080 --name rla-smoke rhystic-library-api:latest
sleep 15
curl -fsS http://localhost:8080/actuator/health
docker stop rla-smoke
```
Expected: `curl` prints `{"status":"UP",...}` and exits 0.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "Add multi-stage Dockerfile"
```

---

### Task 9: Docker Compose layering + .env.example (ADR 000014)

**Files:**
- Create: `compose.yml`, `compose.override.yml`, `compose.prod.yml`, `.env.example`

- [ ] **Step 1: Create the base compose file**

Create `compose.yml`:

```yaml
name: rhystic-library-api

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: rhystic-library-api:latest
    ports:
      - "${APP_PORT:-8080}:8080"
    restart: unless-stopped
```

- [ ] **Step 2: Create the local override (adds MySQL + dev conveniences)**

Create `compose.override.yml`:

```yaml
services:
  app:
    environment:
      SPRING_PROFILES_ACTIVE: local
    depends_on:
      mysql:
        condition: service_healthy

  # Local throwaway MySQL. NOTE: the app does not connect to it yet
  # (persistence is deferred); the full ADR 000014 layering is in place
  # so it is wired the day persistence lands.
  mysql:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: "${MYSQL_DATABASE:-rhystic_library}"
      MYSQL_USER: "${MYSQL_USER:-rhystic}"
      MYSQL_PASSWORD: "${MYSQL_PASSWORD:?set MYSQL_PASSWORD in .env}"
      MYSQL_ROOT_PASSWORD: "${MYSQL_ROOT_PASSWORD:?set MYSQL_ROOT_PASSWORD in .env}"
    ports:
      - "${MYSQL_PORT:-3306}:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mysql-data:
```

> Passwords use the `${VAR:?msg}` required form, so no secret value is committed (honoring ADR 000002) and `docker compose up` fails fast if `.env` is missing them.

- [ ] **Step 3: Create the production override (app only, external MySQL)**

Create `compose.prod.yml`:

```yaml
services:
  app:
    # Run a pre-built, published image rather than building locally.
    build: !reset null
    image: "${APP_IMAGE:?set APP_IMAGE to the published image reference}"
    environment:
      SPRING_PROFILES_ACTIVE: prod
      # Forward-looking: consumed once persistence lands. External/managed MySQL.
      SPRING_DATASOURCE_URL: "${SPRING_DATASOURCE_URL:-}"
      SPRING_DATASOURCE_USERNAME: "${SPRING_DATASOURCE_USERNAME:-}"
      SPRING_DATASOURCE_PASSWORD: "${SPRING_DATASOURCE_PASSWORD:-}"
    restart: always
```

> `build: !reset null` (Docker Compose ≥ 2.24) removes the base `build` so production runs the published image only, never the local dev MySQL.

- [ ] **Step 4: Create the env template**

Create `.env.example`:

```bash
# Copy to .env and fill in values. Real secrets must never be committed (ADR 000002).

# Application
APP_PORT=8080

# Local MySQL (compose.override.yml). The app does not connect to it yet.
MYSQL_PORT=3306
MYSQL_DATABASE=rhystic_library
MYSQL_USER=rhystic
MYSQL_PASSWORD=
MYSQL_ROOT_PASSWORD=

# Production (compose.prod.yml)
APP_IMAGE=
SPRING_DATASOURCE_URL=
SPRING_DATASOURCE_USERNAME=
SPRING_DATASOURCE_PASSWORD=
```

- [ ] **Step 5: Validate the local and prod compose configurations**

Run:
```bash
MYSQL_PASSWORD=x MYSQL_ROOT_PASSWORD=x docker compose config >/dev/null && echo "local OK"
APP_IMAGE=rhystic-library-api:latest docker compose -f compose.yml -f compose.prod.yml config >/dev/null && echo "prod OK"
```
Expected: prints `local OK` then `prod OK` — both layered configurations parse, and the prod app service has no `build` and no `mysql` service.

- [ ] **Step 6: Commit**

```bash
git add compose.yml compose.override.yml compose.prod.yml .env.example
git commit -m "Add Docker Compose base/override/prod layering"
```

---

### Task 10: CI job + Dependabot Maven ecosystem

**Files:**
- Modify: `.github/workflows/ci.yml` (add `java-build` job)
- Modify: `.github/dependabot.yml` (add `maven` ecosystem)

- [ ] **Step 1: Add the Java build job to CI**

In `.github/workflows/ci.yml`, add this job under `jobs:` (e.g., after the `gitleaks` job, matching the existing two-space indentation):

```yaml
  java-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "25"
          cache: maven
      - name: Build and verify
        run: ./mvnw -B verify
```

- [ ] **Step 2: Add the Maven ecosystem to Dependabot**

In `.github/dependabot.yml`, add under `updates:` (after the existing entries):

```yaml
  - package-ecosystem: maven
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(deps)"
```

- [ ] **Step 3: Validate the workflow YAML locally**

Run: `./mvnw -B verify`
Expected: BUILD SUCCESS locally (the same command CI runs). The CI job itself is exercised on push/PR.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml .github/dependabot.yml
git commit -m "Add Java CI job and Maven Dependabot updates"
```

---

## Final verification

- [ ] Run the complete gate from a clean state:

Run: `./mvnw clean verify`
Expected: BUILD SUCCESS — compiles, all tests pass (`RhysticLibraryApplicationTest` + 5 `InfraEndpointsSmokeTest` cases), and Spotless, Checkstyle, SpotBugs+FindSecBugs, and JaCoCo all pass.

- [ ] Confirm the three endpoints manually (optional):

Run:
```bash
./mvnw -pl boot spring-boot:run &
sleep 20
curl -fsS http://localhost:8080/actuator/health
curl -fsS http://localhost:8080/v3/api-docs | head -c 80
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/swagger-ui.html
kill %1
```
Expected: health prints `{"status":"UP"...}`, api-docs prints OpenAPI JSON starting `{"openapi":"3...`, and swagger-ui returns `200`.

## Notes for the implementer

- **JDK 25 is required locally** — if `./mvnw verify` fails with an "invalid target release: 25" or class-version error, the active JDK is too old; install and activate JDK 25 (see Prerequisites).
- **springdoc 3.0.x watch-item:** if both `/v3/api-docs` and `/swagger-ui.html` return HTTP 400, check that Spring Boot 4 API versioning has not been enabled (known springdoc 3.0.0 interaction) — it is not in this plan, so this should not occur.
- **Deferred (do NOT add here):** persistence (MySQL/Flyway/JPA/H2), domain modules, the Maven Enforcer cross-domain banned-dependencies guard, and the app's actual MySQL connection. These land with the first data-bearing domain.
