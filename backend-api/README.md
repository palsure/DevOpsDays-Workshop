# Backend API

Java/Spring Boot REST API that ingests QoE metrics from all player clients, runs validation rules, and serves a pipeline acceptance gate.

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Java 17, Spring Boot 3.2 |
| Database | PostgreSQL 15 (Flyway migrations) |
| Docs | Springdoc OpenAPI / Swagger UI |
| Testing | JUnit 5, Mockito, REST Assured, Testcontainers |
| Reports | Allure |
| Build | Gradle 8 |

## Prerequisites

- Java 17+
- Docker & Docker Compose (for PostgreSQL and E2E tests)

## Setup

### 1. Start PostgreSQL

```bash
docker compose up postgres -d
```

### 2. Run the API locally

```bash
cd backend-api
./gradlew bootRun
```

The API starts on **http://localhost:8080**.

### 3. Swagger UI

Open **http://localhost:8080/swagger-ui/index.html** to browse and try all endpoints interactively.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/metrics` | Ingest a QoE metric payload |
| `GET` | `/api/v1/metrics/{videoId}` | Query metrics for a video |
| `GET` | `/api/v1/platforms` | List all supported platforms (optional `?category=`) |
| `POST` | `/api/v1/validations` | Create a validation rule |
| `POST` | `/api/v1/validations/{id}/run` | Run a validation |
| `GET` | `/api/v1/validations/{id}/results` | Get validation results |
| `POST` | `/api/v1/pipeline/runs` | Start a pipeline acceptance run |
| `POST` | `/api/v1/pipeline/runs/{id}/platforms` | Record a platform result |
| `GET` | `/api/v1/pipeline/runs/{id}` | Get pipeline run result |
| `GET` | `/actuator/health` | Health check |

## Running Tests

### Unit tests (fast — no Docker required)

```bash
./gradlew unitTest
```

### E2E / API tests (requires Docker for Testcontainers)

```bash
./gradlew e2eTest
```

### All tests

```bash
./gradlew test
```

### Generate Allure report

```bash
./gradlew allureReport
# Opens at build/reports/allure-report/allureReport/index.html
```

### View Gradle HTML test report

```bash
open build/reports/tests/unitTest/index.html
open build/reports/tests/e2eTest/index.html
```

## Build Docker image

```bash
cd backend-api
docker build -t qoe-backend .
```

The Dockerfile runs `unitTest` during the build (fast) — E2E tests run separately in CI after the stack is up.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SPRING_DATASOURCE_URL` | `jdbc:postgresql://localhost:5432/qoe_db` | PostgreSQL JDBC URL |
| `SPRING_DATASOURCE_USERNAME` | `qoe_user` | DB username |
| `SPRING_DATASOURCE_PASSWORD` | `qoe_password` | DB password |
| `NEWRELIC_ENABLED` | `false` | Enable New Relic agent |
| `NEWRELIC_LICENSE_KEY` | — | New Relic license key |

## Project Structure

```
backend-api/
├── src/main/java/com/devopsdays/qoe/api/
│   ├── config/          # Spring config (CORS, OpenAPI, Web MVC)
│   ├── controllers/     # REST controllers
│   ├── models/          # JPA entities + Platform enum
│   ├── repositories/    # Spring Data JPA repositories
│   ├── services/        # Business logic
│   └── pipeline/        # Pipeline acceptance gate
├── src/main/resources/
│   ├── application.yml  # App configuration
│   └── db/migration/    # Flyway SQL migrations
├── src/test/java/
│   ├── unit/            # @Tag("unit") — JUnit 5 + Mockito
│   └── e2e/             # @Tag("e2e") — REST Assured + Testcontainers
├── Dockerfile
└── build.gradle
```
