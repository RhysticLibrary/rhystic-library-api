package com.rhysticlibrary.boot;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.http.HttpClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

/** Smoke tests asserting the framework-provided infrastructure endpoints respond. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InfraEndpointsSmokeTest {

  @LocalServerPort private int port;

  private RestClient restClient;

  @BeforeEach
  void setUp() {
    HttpClient httpClient =
        HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build();
    restClient =
        RestClient.builder()
            .requestFactory(new JdkClientHttpRequestFactory(httpClient))
            .baseUrl("http://localhost:" + port)
            .build();
  }

  /** The Actuator health endpoint reports the application is UP. */
  @Test
  void healthEndpointReportsUp() {
    ResponseEntity<String> response =
        restClient.get().uri("/actuator/health").retrieve().toEntity(String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    assertThat(response.getBody()).contains("\"status\":\"UP\"");
  }

  /** The Actuator liveness probe group is exposed. */
  @Test
  void livenessProbeIsExposed() {
    ResponseEntity<String> response =
        restClient.get().uri("/actuator/health/liveness").retrieve().toEntity(String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }

  /** The Actuator readiness probe group is exposed. */
  @Test
  void readinessProbeIsExposed() {
    ResponseEntity<String> response =
        restClient.get().uri("/actuator/health/readiness").retrieve().toEntity(String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }

  /** The OpenAPI 3 spec is served as JSON. */
  @Test
  void apiDocsEndpointReturnsOpenApiJson() {
    ResponseEntity<String> response =
        restClient.get().uri("/v3/api-docs").retrieve().toEntity(String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    assertThat(response.getBody()).contains("\"openapi\"");
  }

  /** The Swagger UI entry point responds successfully (RestClient follows the redirect). */
  @Test
  void swaggerUiEndpointResponds() {
    ResponseEntity<String> response =
        restClient.get().uri("/swagger-ui.html").retrieve().toEntity(String.class);

    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
  }
}
