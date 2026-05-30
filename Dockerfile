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
