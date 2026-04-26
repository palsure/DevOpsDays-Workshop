package com.devopsdays.qoe.api.e2e;

import com.devopsdays.qoe.api.models.Platform;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Story;
import io.qameta.allure.junit5.AllureJunit5;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.Map;
import java.util.UUID;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.closeTo;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.instanceOf;
import static org.hamcrest.Matchers.notNullValue;

@Tag("e2e")
@Epic("QoE API")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ExtendWith(AllureJunit5.class)
@Testcontainers(disabledWithoutDocker = true)
@ActiveProfiles("test")
class QoEApiE2EIT {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:15-alpine")
            .withDatabaseName("qoe_db")
            .withUsername("qoe_user")
            .withPassword("qoe_password");

    @LocalServerPort
    int port;

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @BeforeEach
    void configureRestAssured() {
        RestAssured.reset();
        RestAssured.baseURI = "http://localhost";
        RestAssured.port = port;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
        RestAssured.filters(new AllureRestAssured());
    }

    // ── Infrastructure ────────────────────────────────────────────────────────

    @Test
    @Feature("Actuator")
    @Story("Health")
    void healthEndpointReturnsUp() {
        given()
                .when().get("/actuator/health")
                .then()
                .statusCode(200)
                .body("status", equalTo("UP"));
    }

    @Test
    @Feature("OpenAPI")
    @Story("Discovery")
    void openApiDocsAvailable() {
        given()
                .when().get("/v3/api-docs")
                .then()
                .statusCode(200)
                .contentType(containsString("json"))
                .body("openapi", notNullValue())
                .body("paths", notNullValue());
    }

    // ── Platform catalogue ────────────────────────────────────────────────────

    @Test
    @Feature("Platforms")
    @Story("Full list")
    void listPlatformsReturnsAllPlatforms() {
        given()
                .accept(ContentType.JSON)
                .when().get("/api/v1/platforms")
                .then()
                .statusCode(200)
                .body("$", hasSize(Platform.values().length));
    }

    @ParameterizedTest(name = "platform list filtered by category {0}")
    @EnumSource(Platform.Category.class)
    @Feature("Platforms")
    @Story("Filter by category")
    void listPlatformsByCategoryReturnsNonEmpty(Platform.Category category) {
        given()
                .accept(ContentType.JSON)
                .queryParam("category", category.name())
                .when().get("/api/v1/platforms")
                .then()
                .statusCode(200)
                .body("$", hasSize(greaterThanOrEqualTo(1)));
    }

    // ── Videos ────────────────────────────────────────────────────────────────

    @Test
    @Feature("Videos")
    @Story("Catalog")
    void listVideosReturnsJsonArray() {
        given()
                .accept(ContentType.JSON)
                .when().get("/api/v1/videos")
                .then()
                .statusCode(200)
                .contentType(ContentType.JSON)
                .body("$", instanceOf(Iterable.class));
    }

    // ── Metrics ingest — all platforms ────────────────────────────────────────

    /**
     * Parameterized over every supported platform: each sends a metric,
     * reads it back by session, and checks the summary endpoint responds 200.
     */
    @ParameterizedTest(name = "metrics ingest + query for platform {0}")
    @EnumSource(Platform.class)
    @Feature("Metrics")
    @Story("Multi-platform ingest and query")
    void ingestAndQueryMetricForEachPlatform(Platform platform) {
        String sessionId = "e2e-" + platform.getKey() + "-" + UUID.randomUUID();

        given()
                .contentType(ContentType.JSON)
                .body(metricPayload(platform.getKey(), "demo-1", sessionId))
                .when().post("/api/v1/metrics")
                .then()
                .statusCode(201)
                .body("sessionId", equalTo(sessionId))
                .body("platform", equalTo(platform.getKey()));

        given()
                .queryParam("sessionId", sessionId)
                .when().get("/api/v1/metrics")
                .then()
                .statusCode(200)
                .body("$", hasSize(greaterThanOrEqualTo(1)));

        given()
                .queryParam("platform", platform.getKey())
                .queryParam("videoId", "demo-1")
                .when().get("/api/v1/metrics/summary")
                .then()
                .statusCode(200);
    }

    @Test
    @Feature("Metrics")
    @Story("Unknown platform rejected")
    void ingestMetricUnknownPlatformReturns400() {
        given()
                .contentType(ContentType.JSON)
                .body(metricPayload("tvos", "demo-1", "bad-session"))
                .when().post("/api/v1/metrics")
                .then()
                .statusCode(400)
                .body("error", containsString("Unknown platform"));
    }

    // ── Validation — selected platforms ──────────────────────────────────────

    @ParameterizedTest(name = "validation run for platform {0}")
    @EnumSource(value = Platform.class, names = {
            "WEB", "IPHONE", "ANDROID_PHONE", "APPLE_TV", "ANDROID_TV", "FIRE_TV", "ROKU"
    })
    @Feature("Validation")
    @Story("Multi-platform validation run")
    void validationRunForPlatform(Platform platform) {
        String sessionId = "val-" + platform.getKey() + "-" + UUID.randomUUID();

        given().contentType(ContentType.JSON)
                .body(metricPayload(platform.getKey(), "demo-2", sessionId))
                .when().post("/api/v1/metrics")
                .then().statusCode(201);

        given().contentType(ContentType.JSON)
                .body(Map.of("ruleId", "startup-" + platform.getKey(), "type", "startupTime", "threshold", 5000))
                .when().post("/api/v1/validation/rules")
                .then().statusCode(201);

        given().contentType(ContentType.JSON)
                .body(Map.of("videoId", "demo-2", "platform", platform.getKey(), "sessionId", sessionId))
                .when().post("/api/v1/validation/run")
                .then()
                .statusCode(201)
                .body("sessionId", equalTo(sessionId));
    }

    // ── Pipeline acceptance — all pipeline-facing platforms ───────────────────

    @ParameterizedTest(name = "pipeline gate for platform {0}")
    @EnumSource(value = Platform.class, names = {
            "WEB", "IPHONE", "IPAD", "ANDROID_PHONE", "ANDROID_TABLET",
            "APPLE_TV", "ANDROID_TV", "FIRE_TV", "SAMSUNG_TV", "LG_TV",
            "ROKU", "CHROMECAST", "XBOX", "PLAYSTATION",
            "DESKTOP_MACOS", "DESKTOP_WINDOWS", "DESKTOP_LINUX",
            "API", "AUTOMATION"
    })
    @Feature("Pipeline acceptance")
    @Story("Single platform gate")
    void pipelineRunPerPlatform(Platform platform) {
        String runId = given()
                .contentType(ContentType.JSON)
                .body(Map.of("githubRunId", "e2e-" + platform.getKey()))
                .when().post("/api/v1/pipeline-runs")
                .then()
                .statusCode(201)
                .body("status", equalTo("PENDING"))
                .extract().path("runId");

        given()
                .pathParam("runId", runId)
                .contentType(ContentType.JSON)
                .body(Map.of(
                        "platform", platform.getKey(),
                        "passed", 90, "failed", 10, "skipped", 0, "total", 100
                ))
                .when().post("/api/v1/pipeline-runs/{runId}/platforms")
                .then()
                .statusCode(200)
                .body("platform", equalTo(platform.getKey()));

        given()
                .pathParam("runId", runId)
                .when().post("/api/v1/pipeline-runs/{runId}/finalize")
                .then()
                .statusCode(200)
                .body("status", equalTo("RELEASED"))
                .body("overallPassRate", closeTo(0.9, 0.001));
    }

    @Test
    @Feature("Pipeline acceptance")
    @Story("Multi-platform aggregate gate")
    void pipelineMultiPlatformAggregateMeetsGate() {
        String runId = given()
                .contentType(ContentType.JSON)
                .body(Map.of("githubRunId", "e2e-multi"))
                .when().post("/api/v1/pipeline-runs")
                .then().statusCode(201).extract().path("runId");

        for (Platform p : new Platform[]{
                Platform.WEB, Platform.IPHONE, Platform.ANDROID_PHONE,
                Platform.APPLE_TV, Platform.ANDROID_TV
        }) {
            given()
                    .pathParam("runId", runId)
                    .contentType(ContentType.JSON)
                    .body(Map.of(
                            "platform", p.getKey(),
                            "passed", 85, "failed", 15, "skipped", 0, "total", 100
                    ))
                    .when().post("/api/v1/pipeline-runs/{runId}/platforms")
                    .then().statusCode(200);
        }

        given()
                .pathParam("runId", runId)
                .when().post("/api/v1/pipeline-runs/{runId}/finalize")
                .then()
                .statusCode(200)
                .body("status", equalTo("RELEASED"))
                .body("platforms", hasSize(5));
    }

    @Test
    @Feature("Pipeline acceptance")
    @Story("Unknown platform rejected")
    void pipelinePlatformUnknownReturns400() {
        String runId = given()
                .contentType(ContentType.JSON)
                .body(Map.of("githubRunId", "e2e-bad"))
                .when().post("/api/v1/pipeline-runs")
                .then().statusCode(201).extract().path("runId");

        given()
                .pathParam("runId", runId)
                .contentType(ContentType.JSON)
                .body(Map.of(
                        "platform", "tvos",
                        "passed", 5, "failed", 0, "skipped", 0, "total", 5
                ))
                .when().post("/api/v1/pipeline-runs/{runId}/platforms")
                .then()
                .statusCode(400)
                .body("error", containsString("Unknown platform"));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static Map<String, Object> metricPayload(String platform, String videoId, String sessionId) {
        return Map.of(
                "platform", platform,
                "videoId", videoId,
                "sessionId", sessionId,
                "timestamp", "2024-06-01T10:00:00Z",
                "metrics", Map.of(
                        "playbackState", "playing",
                        "currentTime", 30.0,
                        "duration", 300.0,
                        "startupTime", 600,
                        "totalBufferingTime", 0.5,
                        "errorCount", 0
                )
        );
    }
}
