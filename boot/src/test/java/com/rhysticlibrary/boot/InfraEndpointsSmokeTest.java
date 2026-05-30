package com.rhysticlibrary.boot;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.http.HttpClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.test.web.servlet.client.RestTestClient;

/** Smoke tests asserting the framework-provided infrastructure endpoints respond. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InfraEndpointsSmokeTest {

  @LocalServerPort private int port;

  private RestTestClient client;

  @BeforeEach
  void setUp() {
    HttpClient httpClient =
        HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build();
    client =
        RestTestClient.bindToServer(new JdkClientHttpRequestFactory(httpClient))
            .baseUrl("http://localhost:" + port)
            .build();
  }

  /** The Actuator health endpoint reports the application is UP. */
  @Test
  void healthEndpointReportsUp() {
    String body =
        client
            .get()
            .uri("/actuator/health")
            .exchange()
            .expectStatus()
            .is2xxSuccessful()
            .expectBody(String.class)
            .returnResult()
            .getResponseBody();

    assertThat(body).contains("\"status\":\"UP\"");
  }

  /** The Actuator liveness probe group is exposed. */
  @Test
  void livenessProbeIsExposed() {
    client.get().uri("/actuator/health/liveness").exchange().expectStatus().is2xxSuccessful();
  }

  /** The Actuator readiness probe group is exposed. */
  @Test
  void readinessProbeIsExposed() {
    client.get().uri("/actuator/health/readiness").exchange().expectStatus().is2xxSuccessful();
  }

  /** The OpenAPI 3 spec is served as JSON. */
  @Test
  void apiDocsEndpointReturnsOpenApiJson() {
    String body =
        client
            .get()
            .uri("/v3/api-docs")
            .exchange()
            .expectStatus()
            .is2xxSuccessful()
            .expectBody(String.class)
            .returnResult()
            .getResponseBody();

    assertThat(body).contains("\"openapi\"");
  }

  /** The Swagger UI entry point responds successfully (redirect followed via JDK HttpClient). */
  @Test
  void swaggerUiEndpointResponds() {
    client.get().uri("/swagger-ui.html").exchange().expectStatus().is2xxSuccessful();
  }
}
