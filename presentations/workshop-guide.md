# Cross Platform Streaming Video QoE Validation in CI/CD Pipelines
## Workshop Guide

### Workshop Overview

This hands-on workshop demonstrates how to implement cross-platform Quality of Experience (QoE) validation for streaming video in CI/CD pipelines. You'll learn to collect, validate, and monitor QoE metrics across web, iOS, and Android platforms.

**Duration**: 3-4 hours  
**Level**: Advanced

---

## Prerequisites

Before starting, ensure you have:

- Docker and Docker Compose installed
- Java 17+ (for backend)
- Node.js 18+ (for web player)
- Xcode 15+ (for iOS, macOS only)
- Android Studio (for Android)
- New Relic account (optional, for monitoring)
- Git

---

## Session 1: Foundation & Architecture (45 minutes)

### 1.1 Introduction to QoE Metrics

**What is QoE?**
Quality of Experience (QoE) measures the overall satisfaction of a user with a service. For video streaming, key metrics include:

- **Startup Time**: Time from play request to first frame
- **Buffering Time**: Total time spent buffering during playback
- **Bitrate**: Current video bitrate and switches
- **Error Rate**: Number and type of playback errors
- **Frame Drops**: Frames dropped vs. rendered
- **Playback Quality**: Overall quality assessment (excellent/good/fair/poor)

### 1.2 Cross-Platform Challenges

Different platforms have different capabilities:

- **Web**: Browser-based, HLS.js, network conditions vary
- **iOS**: AVPlayer, native performance, consistent hardware
- **Android**: ExoPlayer, diverse hardware, fragmentation

### 1.3 Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Web Player │     │ iOS Player  │     │Android Player│
│  (HLS.js)   │     │ (AVPlayer)  │     │ (ExoPlayer) │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │  Backend API    │
                  │ (Spring Boot)   │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  │   (Database)    │
                  └─────────────────┘
```

### 1.4 CI/CD Integration Patterns

- **Module-isolated pipelines** — path-filtered triggers ensure only the affected module's workflow runs on each commit, giving fast, focused feedback
- **Three-stage pipeline** per module: Unit Tests → E2E Tests → Automation E2E (Maven/TestNG)
- **PR quality gate** — `qoe-pr-e2e.yml` runs the full Docker stack and enforces an 80% Playwright pass rate on every pull request
- **Threaded Slack notifications** — Build Started + per-stage replies with test counts, pass rate, and Allure report links
- **Manual acceptance gate** — `build-acceptance-release.yml` runs cross-module acceptance tests and creates a GitHub Release when ≥ 80% pass

---

## Session 2: Hands-on Project Setup (60 minutes)

### 2.1 Clone and Explore the Project

```bash
cd /path/to/DevOpsDays
ls -la
```

**Project Structure:**
```

├── backend-api/          # Java/Spring Boot API
├── web-player/           # React/TypeScript web player
├── ios-player/           # Swift iOS player (library + Xcode app)
├── android-player/       # Kotlin Android player
├── qoe-automation-tests/  # Test automation
└── ops/                   # infrastructure, monitoring, shared schema
```

### 2.2 Start the Backend Services

```bash
# Start PostgreSQL and Backend API
docker compose up -d postgres backend

# Wait for services to be healthy
docker compose ps

# Check backend health
curl http://localhost:8080/actuator/health
```

**Expected Output:**
```json
{"status":"UP"}
```

### 2.3 Explore the API

```bash
# List videos
curl http://localhost:8080/api/v1/videos

# Create a test video
curl -X POST http://localhost:8080/api/v1/videos \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "demo-1",
    "title": "Demo Video",
    "hlsManifestUrl": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
  }'
```

### 2.4 Start the Web Player

```bash
cd web-player
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

**Exercise**: Play a video and observe metrics being sent to the backend.

### 2.5 Verify Metrics Collection

```bash
# Query metrics
curl "http://localhost:8080/api/v1/metrics?platform=web"

# Get summary
curl "http://localhost:8080/api/v1/metrics/summary?platform=web"
```

---

## Session 3: CI/CD Integration (60 minutes)

### 3.1 Explore GitHub Actions Workflows

The project uses **module-isolated pipelines** — only the pipeline for the changed module runs on each commit:

| Workflow | Trigger | What runs |
|---|---|---|
| `qoe-api-tests.yml` | push → `backend-api/**` | Unit → E2E (matrix) → Automation E2E |
| `qoe-web-tests.yml` | push → `web-player/**` | Unit → Playwright E2E → Automation E2E |
| `qoe-android-tests.yml` | push → `android-player/**` | Unit/Lint → Build → Automation E2E |
| `qoe-ios-tests.yml` | push → `ios-player/**` | Swift test → Xcode build → Automation E2E |
| `qoe-validation.yml` | pull request | All modules (lightweight compile + unit) |
| `qoe-pr-e2e.yml` | pull request (web+api) | Full Docker stack + Playwright gate |
| `build-acceptance-release.yml` | manual | Cross-module acceptance + GitHub Release |

Each pipeline posts threaded Slack notifications:
- **Build Started** message with branch, commit, and build number
- **Unit test** thread reply — test count, pass rate, report link
- **E2E / Automation** thread reply — test count, pass rate, Allure link
- **Summary** message — overall build status, all stages, duration

```bash
# Browse workflow files
ls .github/workflows/
cat .github/workflows/qoe-api-tests.yml
```

### 3.2 Run Tests Locally

**Backend API Tests:**
```bash
cd backend-api
./gradlew unitTest   # before deploy / packaging
./gradlew e2eTest    # after stack is up (Docker + Testcontainers)
./gradlew test       # both
```

**Web Player Tests:**
```bash
cd web-player
npm test
```

### 3.3 Create a Validation Rule

```bash
curl -X POST http://localhost:8080/api/v1/validation/rules \
  -H "Content-Type: application/json" \
  -d '{
    "ruleId": "startup-time-rule",
    "type": "startupTime",
    "threshold": 3000,
    "description": "Startup time must be less than 3 seconds"
  }'
```

### 3.4 Run Validation

```bash
# First, ensure you have metrics for a session
# Then run validation
curl -X POST http://localhost:8080/api/v1/validation/run \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "demo-1",
    "platform": "web",
    "sessionId": "your-session-id"
  }'
```

### 3.5 Quality Gates

Quality gates enforce minimum quality standards:

- Startup time < 3 seconds
- Buffering time < 5% of duration
- Error count < 2
- Quality score > 0.7

**Exercise**: Modify thresholds and observe validation results.

---

## Session 4: Advanced Scenarios & Best Practices (45 minutes)

### 4.1 New Relic Monitoring Setup

1. **Configure New Relic Agent**

Edit `backend-api/src/main/resources/application.yml`:
```yaml
newrelic:
  enabled: true
  license-key: YOUR_LICENSE_KEY
  app-name: QoE API
```

2. **Import Dashboards**

Use the dashboard JSON files in `ops/monitoring/newrelic/dashboards/`

3. **Set Up Alerts**

Configure alerts using files in `ops/monitoring/newrelic/alerts/`

### 4.2 Custom NRQL Queries

Example queries in `ops/monitoring/newrelic/nrql-queries/`:

```sql
-- Average startup time by platform
SELECT average(startupTime) 
FROM QoEMetric 
WHERE timestamp >= SINCE 1 hour ago 
FACET platform
```

### 4.3 Performance Optimization

**Backend Optimization:**
- Database indexing on frequently queried fields
- Connection pooling
- Caching frequently accessed data

**Client Optimization:**
- Batch metric submissions
- Compress payloads
- Retry failed submissions

### 4.4 Real-World Failure Scenarios

**Scenario 1: High Buffering**
- Cause: Slow network
- Detection: `totalBufferingTime > threshold`
- Action: Alert and investigate network conditions

**Scenario 2: High Error Rate**
- Cause: Server issues or codec problems
- Detection: `errorCount > threshold`
- Action: Alert and check server logs

**Scenario 3: Quality Degradation**
- Cause: Multiple factors
- Detection: `playbackQuality = 'poor'`
- Action: Comprehensive investigation

### 4.5 Best Practices

1. **Metric Collection**
   - Collect metrics at regular intervals (5-10 seconds)
   - Include context (device, network, video metadata)
   - Handle failures gracefully

2. **Validation Rules**
   - Define clear thresholds
   - Platform-specific rules when needed
   - Regular review and adjustment

3. **Monitoring**
   - Set up dashboards for key metrics
   - Configure alerts for critical issues
   - Regular trend analysis

4. **CI/CD Integration**
   - Run tests on every PR
   - Enforce quality gates
   - Provide clear feedback

---

## Hands-On Exercises

### Exercise 1: Add a New Metric

**Task**: Add a new metric to track "seek operations"

1. Update the schema in `ops/shared/schema/qoe-metrics.schema.json`
2. Update the backend model in `backend-api/src/main/java/.../models/QoEMetric.java`
3. Update the web player to track seeks
4. Verify metrics are collected

### Exercise 2: Create a Custom Validation Rule

**Task**: Create a rule for bitrate stability

1. Add a new rule type in `ValidationService.java`
2. Calculate bitrate stability (low variance = stable)
3. Set threshold (e.g., variance < 20%)
4. Test the rule

### Exercise 3: Set Up Platform-Specific Alerts

**Task**: Create alerts for each platform

1. Create alert policies in New Relic
2. Set different thresholds per platform
3. Configure notification channels
4. Test alerts

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker compose logs backend

# Verify database connection
docker compose exec postgres psql -U qoe_user -d qoe_db
```

### Metrics Not Being Sent

1. Check browser console for errors
2. Verify API URL is correct
3. Check CORS settings
4. Verify network connectivity

### Tests Failing

1. Check test logs
2. Verify dependencies are installed
3. Check environment variables
4. Review test configuration

---

## Additional Resources

- [HLS.js Documentation](https://github.com/video-dev/hls.js/)
- [ExoPlayer Documentation](https://developer.android.com/guide/topics/media/exoplayer)
- [AVPlayer Documentation](https://developer.apple.com/documentation/avfoundation/avplayer)
- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [New Relic Documentation](https://docs.newrelic.com/)

---

## Workshop Completion Checklist

- [ ] Backend API running and accessible
- [ ] Web player collecting and sending metrics
- [ ] Metrics visible in database
- [ ] Validation rules created and tested
- [ ] GitHub Actions workflows understood
- [ ] New Relic monitoring configured (optional)
- [ ] At least one exercise completed

---

## Next Steps

1. **Extend the Implementation**
   - Add more platforms (Roku, Apple TV)
   - Implement real-time dashboards
   - Add machine learning for quality prediction

2. **Production Readiness**
   - Add authentication/authorization
   - Implement rate limiting
   - Add comprehensive error handling
   - Set up production monitoring

3. **Team Adoption**
   - Document your QoE standards
   - Train team members
   - Integrate into existing workflows

---

## Questions & Support

For questions during the workshop, please ask the instructor or refer to:
- Project README files
- Code comments
- API documentation (Swagger UI at `/swagger-ui/index.html`, OpenAPI at `/v3/api-docs`)

---

**Thank you for participating in the DevOpsDays Raleigh 2026 workshop!**
