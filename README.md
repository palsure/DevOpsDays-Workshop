# Cross Platform Streaming Video QoE Validation in CI/CD Pipelines

## Workshop Overview

This workshop demonstrates how to implement cross-platform Quality of Experience (QoE) validation for streaming video in CI/CD pipelines. The workshop includes complete, working examples for web, iOS, and Android platforms, integrated with automated testing and monitoring.

## Workshop Duration

3-4 hours (Half-day workshop)

## Target Audience

Advanced practitioners with experience in:
- Video streaming technologies
- CI/CD pipelines
- Cross-platform development
- Quality assurance and testing

## Learning Outcomes

- Understand QoE metrics relevant to video streaming
- Implement cross-platform QoE validation
- Integrate quality checks into CI/CD pipelines
- Use open-source tools for media validation
- Handle platform-specific challenges
- Set up automated quality gates
- Monitor QoE metrics using New Relic

## Modules

| Module | Description | README |
|---|---|---|
| [`backend-api/`](backend-api/README.md) | Java/Spring Boot REST API | Setup, endpoints, test commands |
| [`web-player/`](web-player/README.md) | React/TypeScript HLS player | Setup, E2E tests, Allure reports |
| [`ios-player/`](ios-player/README.md) | Swift Package library + SwiftUI demo app | Library usage, Xcode build, Firebase deploy |
| [`android-player/`](android-player/README.md) | Kotlin/ExoPlayer Android app | Android Studio setup, APK build |
| [`qoe-automation-tests/`](qoe-automation-tests/README.md) | Java/TestNG automation suite | API, web, mobile, validation tests |
| [`ops/`](ops/README.md) | Infrastructure, monitoring, shared schema | nginx, FFmpeg, New Relic, JSON schema |

## Project Structure

```
├── backend-api/                 # Java/Spring Boot backend API
├── web-player/                  # React/TypeScript web player
├── ios-player/                  # Swift/Xcode iOS player (library + app)
├── android-player/              # Kotlin/Gradle Android app
├── qoe-automation-tests/        # Java/TestNG test automation
├── ops/                         # Ops utilities
│   ├── infrastructure/          # nginx, FFmpeg, network simulation scripts
│   ├── monitoring/              # New Relic alerts, dashboards, NRQL queries
│   └── shared/schema/           # Shared QoE metrics schema + TypeScript types
├── test-videos/                 # Sample HLS test streams
└── .github/workflows/           # GitHub Actions CI/CD workflows
```

## Reference Repositories

This workshop is based on production implementations from:

- **cbs-android**: Android app using Kotlin, ExoPlayer, Gradle
- **cbs-ios**: iOS app using Swift, AVPlayer, Xcode
- **api-web-monorepo**: Java/Spring Boot backend API
- **quality-engineering-test**: Test automation framework

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Java 17+ (for backend)
- Node.js 18+ (for web player)
- Xcode 15+ (for iOS, macOS only)
- Android Studio (for Android)
- New Relic account (for monitoring)

### Running the Demo

1. **Start all services**:
   ```bash
   docker compose up -d
   ```

2. **Access services**:
   - Backend API: http://localhost:8080
   - Web Player: http://localhost:3000
   - New Relic Dashboard: (configured in ops/monitoring/)

3. **Run tests**:
   ```bash
   # Backend API — unit only (before deploy) or E2E (needs Docker), or both
   cd backend-api && ./gradlew unitTest
   cd backend-api && ./gradlew e2eTest   # after stack / with Docker
   cd backend-api && ./gradlew test      # unit + e2e

   # Test automation framework
   cd qoe-automation-tests && mvn test
   ```

## Components

### 1. Multi-Platform Video Players

- **Web Player**: React/TypeScript with HLS.js
- **iOS Player**: Swift with AVPlayer
- **Android Player**: Kotlin with ExoPlayer

All players collect and report QoE metrics to the backend API.

### 2. Backend API

Java/Spring Boot REST API that:
- Receives QoE metrics from all platforms
- Stores metrics in PostgreSQL
- Provides query endpoints for metrics and trends
- Manages video catalog and manifests

### 3. Test Automation Framework

Java/TestNG framework for:
- Automated QoE validation tests
- Cross-platform test execution
- Quality gate enforcement
- Test reporting

### 4. CI/CD Pipelines

Module-isolated GitHub Actions workflows for:
- Path-filtered triggers — only the affected module's pipeline runs on each commit
- Per-module stages: Unit Tests → E2E Tests → Automation E2E
- Threaded Slack notifications with test counts, pass rate, and report links
- Aggregate acceptance gate (`build-acceptance-release.yml`) triggered manually
- PR quality gate (`qoe-pr-e2e.yml`) — Playwright gates on every pull request

| Workflow | Trigger | Module |
|---|---|---|
| `qoe-api-tests.yml` | push to `backend-api/**` | Backend API |
| `qoe-web-tests.yml` | push to `web-player/**` | Web Player |
| `qoe-android-tests.yml` | push to `android-player/**` | Android Player |
| `qoe-ios-tests.yml` | push to `ios-player/**` | iOS Player |
| `qoe-validation.yml` | pull request | All modules (lightweight) |
| `qoe-pr-e2e.yml` | pull request | Web + API (E2E gate) |
| `build-acceptance-release.yml` | manual | All modules (acceptance + release) |

### 5. Monitoring

New Relic integration for:
- Real-time QoE metrics visualization
- Custom dashboards
- Automated alerts
- Performance monitoring

## Workshop Sessions

1. **Foundation & Architecture** (45 min)
2. **Hands-on Project Setup** (60 min)
3. **CI/CD Integration** (60 min)
4. **Advanced Scenarios & Best Practices** (45 min)

See [`presentations/workshop-guide.md`](presentations/workshop-guide.md) for detailed instructions.

## Contributing

This is a workshop demonstration project. For questions or issues, please refer to the workshop guide.

## License

This project is for educational purposes as part of the DevOpsDays Raleigh 2026 workshop.
