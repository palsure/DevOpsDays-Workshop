package com.devopsdays.qoe.api.e2e;

import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Story;
import io.qameta.allure.junit5.AllureJunit5;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.extension.ExtendWith;
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

import static java.util.Map.entry;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@Tag("e2e")
@Epic("Video Catalog API")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ExtendWith(AllureJunit5.class)
@Testcontainers(disabledWithoutDocker = true)
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("Video Catalog API — E2E")
class VideoApiE2EIT {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:15-alpine")
            .withDatabaseName("qoe_db")
            .withUsername("qoe_user")
            .withPassword("qoe_password");

    @LocalServerPort
    int port;

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url",      POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @BeforeEach
    void configureRestAssured() {
        RestAssured.reset();
        RestAssured.baseURI = "http://localhost";
        RestAssured.port    = port;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
        RestAssured.filters(new AllureRestAssured());
    }

    // ── helpers ───────────────────────────────────────────────────────────────

    private static Map<String, Object> videoPayload(String videoId) {
        return Map.ofEntries(
                entry("videoId",        videoId),
                entry("title",          "Test Video - " + videoId),
                entry("description",    "An E2E test video"),
                entry("thumbnailUrl",   "https://example.com/" + videoId + "/thumb.jpg"),
                entry("hlsManifestUrl", "https://example.com/" + videoId + ".m3u8"),
                entry("dashManifestUrl","https://example.com/" + videoId + ".mpd"),
                entry("duration",       596),
                entry("resolution",     "1920x1080"),
                entry("bitrate",        5000000),
                entry("category",       "movie"),
                entry("genre",          "animation")
        );
    }

    // ── GET /api/v1/videos ────────────────────────────────────────────────────

    @Test
    @Order(1)
    @Feature("List Videos")
    @Story("List all videos returns seeded catalog")
    @DisplayName("GET /videos returns 200 with seeded videos")
    void listVideos_returnsSeededCatalog() {
        given()
            .when().get("/api/v1/videos")
            .then()
            .statusCode(200)
            .contentType(ContentType.JSON)
            .body("$", hasSize(greaterThanOrEqualTo(1)));
    }

    @Test
    @Order(2)
    @Feature("List Videos")
    @Story("Filter by category returns matching videos only")
    @DisplayName("GET /videos?category=movie returns only movies")
    void listVideos_filterByCategory() {
        // First create a known movie
        String videoId = "e2e-cat-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .queryParam("category", "movie")
            .when().get("/api/v1/videos")
            .then()
            .statusCode(200)
            .body("$", hasSize(greaterThanOrEqualTo(1)))
            .body("[0].category", equalTo("movie"));
    }

    // ── GET /api/v1/videos/search ─────────────────────────────────────────────

    @Test
    @Order(3)
    @Feature("Search Videos")
    @Story("Search by title keyword returns matching videos")
    @DisplayName("GET /videos/search?q=bunny returns results containing 'bunny'")
    void searchVideos_byTitleKeyword() {
        // Create a known searchable video
        String videoId = "e2e-search-" + UUID.randomUUID().toString().substring(0, 8);
        Map<String, Object> payload = Map.of(
                "videoId", videoId,
                "title", "Bunny Tales Episode 1",
                "description", "A story about rabbits",
                "hlsManifestUrl", "https://example.com/bunny.m3u8",
                "duration", 300,
                "category", "show",
                "genre", "animation"
        );
        given()
            .contentType(ContentType.JSON)
            .body(payload)
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .queryParam("q", "Bunny")
            .when().get("/api/v1/videos/search")
            .then()
            .statusCode(200)
            .body("$", hasSize(greaterThanOrEqualTo(1)))
            .body("[0].title", containsString("Bunny"));
    }

    @Test
    @Order(4)
    @Feature("Search Videos")
    @Story("Search by description keyword works")
    @DisplayName("GET /videos/search?q=rabbits finds videos by description")
    void searchVideos_byDescriptionKeyword() {
        given()
            .queryParam("q", "rabbits")
            .when().get("/api/v1/videos/search")
            .then()
            .statusCode(200)
            .body("$", hasSize(greaterThanOrEqualTo(1)));
    }

    @Test
    @Order(5)
    @Feature("Search Videos")
    @Story("Empty search term returns all active videos")
    @DisplayName("GET /videos/search?q= (blank) returns all active videos")
    void searchVideos_blankQueryReturnsAll() {
        given()
            .queryParam("q", "")
            .when().get("/api/v1/videos/search")
            .then()
            .statusCode(200)
            .body("$", hasSize(greaterThanOrEqualTo(1)));
    }

    // ── GET /api/v1/videos/{id} ───────────────────────────────────────────────

    @Test
    @Order(6)
    @Feature("Get Video")
    @Story("Get existing video by ID returns full details")
    @DisplayName("GET /videos/{id} returns 200 with correct fields")
    void getVideo_returnsVideoDetails() {
        String videoId = "e2e-get-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .when().get("/api/v1/videos/" + videoId)
            .then()
            .statusCode(200)
            .body("videoId",    equalTo(videoId))
            .body("title",      containsString("Test Video"))
            .body("category",   equalTo("movie"))
            .body("genre",      equalTo("animation"))
            .body("duration",   equalTo(596))
            .body("bitrate",    equalTo(5000000))
            .body("active",     equalTo(true))
            .body("createdAt",  notNullValue());
    }

    @Test
    @Order(7)
    @Feature("Get Video")
    @Story("Get non-existent video returns 404")
    @DisplayName("GET /videos/{id} returns 404 for unknown id")
    void getVideo_notFound() {
        given()
            .when().get("/api/v1/videos/does-not-exist-xyz")
            .then()
            .statusCode(404);
    }

    // ── GET /api/v1/videos/{id}/manifest ─────────────────────────────────────

    @Test
    @Order(8)
    @Feature("Manifest")
    @Story("Get manifest returns HLS and DASH URLs")
    @DisplayName("GET /videos/{id}/manifest returns hls and dash URLs")
    void getManifest_returnsUrls() {
        String videoId = "e2e-manifest-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .when().get("/api/v1/videos/" + videoId + "/manifest")
            .then()
            .statusCode(200)
            .body("videoId", equalTo(videoId))
            .body("hls",     containsString(".m3u8"))
            .body("dash",    containsString(".mpd"));
    }

    @Test
    @Order(9)
    @Feature("Manifest")
    @Story("Get manifest for non-existent video returns 404")
    @DisplayName("GET /videos/{id}/manifest returns 404 for unknown id")
    void getManifest_notFound() {
        given()
            .when().get("/api/v1/videos/unknown-manifest/manifest")
            .then()
            .statusCode(404);
    }

    // ── POST /api/v1/videos ───────────────────────────────────────────────────

    @Test
    @Order(10)
    @Feature("Create Video")
    @Story("Create a new video returns 201 with persisted data")
    @DisplayName("POST /videos creates video and returns 201")
    void createVideo_success() {
        String videoId = "e2e-create-" + UUID.randomUUID().toString().substring(0, 8);

        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then()
            .statusCode(201)
            .body("videoId",  equalTo(videoId))
            .body("active",   equalTo(true))
            .body("category", equalTo("movie"))
            .body("genre",    equalTo("animation"));
    }

    @Test
    @Order(11)
    @Feature("Create Video")
    @Story("Duplicate videoId returns 400 Bad Request")
    @DisplayName("POST /videos with duplicate videoId returns 400")
    void createVideo_duplicateId_returns400() {
        String videoId = "e2e-dup-" + UUID.randomUUID().toString().substring(0, 8);

        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then()
            .statusCode(400)
            .body("error", containsString(videoId));
    }

    @Test
    @Order(12)
    @Feature("Create Video")
    @Story("Missing required fields returns 400 validation error")
    @DisplayName("POST /videos with missing videoId returns 400")
    void createVideo_missingRequiredField_returns400() {
        given()
            .contentType(ContentType.JSON)
            .body(Map.of("title", "No ID Video"))
            .when().post("/api/v1/videos")
            .then()
            .statusCode(400);
    }

    // ── PUT /api/v1/videos/{id} ───────────────────────────────────────────────

    @Test
    @Order(13)
    @Feature("Update Video")
    @Story("Update an existing video replaces all fields")
    @DisplayName("PUT /videos/{id} updates title, category and genre")
    void updateVideo_success() {
        String videoId = "e2e-upd-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        Map<String, Object> updated = Map.of(
                "videoId",        videoId,
                "title",          "Updated Title",
                "description",    "Updated description",
                "hlsManifestUrl", "https://example.com/updated.m3u8",
                "duration",       999,
                "category",       "documentary",
                "genre",          "nature"
        );

        given()
            .contentType(ContentType.JSON)
            .body(updated)
            .when().put("/api/v1/videos/" + videoId)
            .then()
            .statusCode(200)
            .body("title",    equalTo("Updated Title"))
            .body("category", equalTo("documentary"))
            .body("genre",    equalTo("nature"))
            .body("duration", equalTo(999));
    }

    @Test
    @Order(14)
    @Feature("Update Video")
    @Story("Update non-existent video returns 404")
    @DisplayName("PUT /videos/{id} returns 404 for unknown id")
    void updateVideo_notFound() {
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload("ghost-id"))
            .when().put("/api/v1/videos/ghost-id")
            .then()
            .statusCode(404)
            .body("error", containsString("ghost-id"));
    }

    // ── DELETE /api/v1/videos/{id} ────────────────────────────────────────────

    @Test
    @Order(15)
    @Feature("Delete Video")
    @Story("Delete video returns 204 and video no longer appears in listings")
    @DisplayName("DELETE /videos/{id} soft-deletes the video")
    void deleteVideo_success() {
        String videoId = "e2e-del-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        // Delete
        given()
            .when().delete("/api/v1/videos/" + videoId)
            .then()
            .statusCode(204);

        // Verify it's gone from GET by ID
        given()
            .when().get("/api/v1/videos/" + videoId)
            .then()
            .statusCode(404);
    }

    @Test
    @Order(16)
    @Feature("Delete Video")
    @Story("Deleted video no longer appears in list")
    @DisplayName("GET /videos does not return soft-deleted videos")
    void deleteVideo_disappearsFromList() {
        String videoId = "e2e-del-list-" + UUID.randomUUID().toString().substring(0, 8);
        given()
            .contentType(ContentType.JSON)
            .body(videoPayload(videoId))
            .when().post("/api/v1/videos")
            .then().statusCode(201);

        given()
            .when().delete("/api/v1/videos/" + videoId)
            .then().statusCode(204);

        // Should not appear in the full list
        given()
            .when().get("/api/v1/videos")
            .then()
            .statusCode(200)
            .body("videoId.flatten()", org.hamcrest.Matchers.not(
                    org.hamcrest.Matchers.hasItem(videoId)));
    }

    @Test
    @Order(17)
    @Feature("Delete Video")
    @Story("Delete non-existent video returns 404")
    @DisplayName("DELETE /videos/{id} returns 404 for unknown id")
    void deleteVideo_notFound() {
        given()
            .when().delete("/api/v1/videos/no-such-video")
            .then()
            .statusCode(404);
    }
}
