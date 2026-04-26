# Local Testing Guide

Step-by-step instructions to run unit tests, E2E tests, and view reports for every module.

---

## Prerequisites

| Tool | Min version | Install |
|---|---|---|
| Java (JDK) | 17+ | `brew install --cask temurin@17` |
| Gradle | via wrapper (`gradlew`) | included in each module |
| Docker Desktop | 24+ | [docs.docker.com](https://docs.docker.com/desktop/mac/install/) |
| Node.js | 18+ | `brew install node` |
| npm | 9+ | bundled with Node |
| Maven | 3.9+ | `brew install maven` |
| Allure CLI | 2.27+ | `brew install allure` |
| Xcode | 15+ | Mac App Store *(iOS only)* |

---

## Start the shared backend stack

Most E2E and automation tests target the live API.  
Start it once and leave it running for all modules:

```bash
# from the repository root
docker compose up -d

# verify everything is healthy
docker compose ps
curl http://localhost:8080/actuator/health
```

**Running services:**

| Service | URL |
|---|---|
| Backend API | http://localhost:8080 |
| Web Player | http://localhost:3000 |
| Nginx (reverse proxy) | http://localhost:8081 |
| PostgreSQL | localhost:5432 |

Stop the stack when done:

```bash
docker compose down
```

---

## 1 — Backend API (`backend-api/`)

The API uses separate Gradle tasks for unit and E2E tests.  
The E2E tests are fully self-contained: they spin up their own throwaway  
PostgreSQL via Testcontainers — **no running stack required**.

### 1.1 Unit tests

```bash
cd backend-api
./gradlew unitTest
```

- Runs only tests tagged `@Tag("unit")`
- No Docker, no network access needed
- Fast (~10 s)

**View the HTML report:**

```bash
open build/reports/tests/unitTest/index.html
```

### 1.2 E2E / Integration tests

```bash
cd backend-api
./gradlew e2eTest
```

- Runs only tests tagged `@Tag("e2e")` (`QoEApiE2EIT`)
- Testcontainers automatically starts a fresh PostgreSQL container
- Docker must be running

**View the HTML report:**

```bash
open build/reports/tests/e2eTest/index.html
```

### 1.3 Allure report (E2E)

```bash
# run tests then generate + open report in one step
./gradlew e2eTest allureReport
```

The Allure report opens automatically in your browser.  
Manual path: `build/reports/allure-report/allureReport/index.html`

### 1.4 Run all tests together

```bash
./gradlew test allureReport
```

---

## 2 — Web Player (`web-player/`)

### 2.1 Unit tests (Vitest)

No server required — runs in a jsdom environment.

```bash
cd web-player
npm ci          # first time only
npm test
```

**JUnit XML output:** `web-player/test-results/vitest-junit.xml`

**Watch mode** (re-runs on file save):

```bash
npm run test:watch
```

### 2.2 E2E tests (Playwright) — against the Docker app

The Docker web player at `http://localhost:3000` must be running.

```bash
cd web-player

# install Chromium browser (first time only)
npm run e2e:install

# run E2E tests against localhost:3000
npm run e2e:docker
```

**Watch the browser while tests run:**

```bash
npm run e2e:docker:headed
```

**Debug a single test interactively:**

```bash
npm run e2e:debug
```

**Throttled network tests** (simulates slow connections):

```bash
npm run e2e:docker:throttle
```

**View the Playwright HTML report:**

```bash
npx playwright show-report
```

> The report is saved to `web-player/playwright-report/index.html`.

### 2.3 Allure report (Web E2E)

```bash
# requires allure CLI: brew install allure
npm run allure:report
```

---

## 3 — Android Player (`android-player/`)

Requires **Java 17+** and **Android SDK** (or Android Studio).

### 3.1 Unit tests

```bash
cd android-player
./gradlew test
```

Runs all JUnit 4 unit tests in `app/src/test/`.

**Run only the Debug variant** (faster):

```bash
./gradlew testDebugUnitTest
```

**View the HTML report:**

```bash
open app/build/reports/tests/testDebugUnitTest/index.html
```

**JUnit XML output:** `app/build/test-results/testDebugUnitTest/`

### 3.2 Lint

```bash
./gradlew lint
```

**View lint report:**

```bash
open app/build/reports/lint-results-debug.html
```

### 3.3 Build debug APK

```bash
./gradlew assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`

### 3.4 Instrumented / UI tests  
*(requires a connected device or running emulator)*

```bash
./gradlew connectedDebugAndroidTest
```

---

## 4 — iOS Player (`ios-player/`)

Requires **macOS with Xcode 15+**.

### 4.1 Unit tests — Swift Package

```bash
cd ios-player
swift test
```

Tests inside `Tests/QoePlayerTests/` are discovered and run automatically.

**Verbose output** (shows individual test case pass/fail):

```bash
swift test --verbose
```

### 4.2 Build the Xcode app (simulator)

```bash
xcodebuild \
  -project QoePlayerApp.xcodeproj \
  -scheme QoePlayerApp \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  clean build \
  CODE_SIGN_IDENTITY="" \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGNING_ALLOWED=NO \
  | xcpretty
```

> Install `xcpretty` for readable output: `gem install xcpretty`

### 4.3 Run Xcode tests in the simulator

```bash
xcodebuild test \
  -project QoePlayerApp.xcodeproj \
  -scheme QoePlayerApp \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  | xcpretty --report html --output build/reports/tests/index.html
```

**View the report:**

```bash
open build/reports/tests/index.html
```

---

## 5 — Automation / System Tests (`qoe-automation-tests/`)

These are TestNG integration tests that run **against the live API**.  
The Docker stack must be running (`docker compose up -d`).

### 5.1 Run all automation tests

```bash
cd qoe-automation-tests
mvn test -Dapi.base.url=http://localhost:8080
```

### 5.2 Run a specific test suite

```bash
# API-only suite
mvn test -Dapi.base.url=http://localhost:8080 \
         -DsuiteXmlFile=src/test/resources/testng.xml

# Mobile suite
mvn test -Dapi.base.url=http://localhost:8080 \
         -DsuiteXmlFile=src/test/resources/testng-mobile.xml
```

### 5.3 Surefire XML results

Maven Surefire saves JUnit-compatible XML to:

```
qoe-automation-tests/target/surefire-reports/TEST-*.xml
```

### 5.4 Allure report

```bash
# generate HTML from allure-results/ captured during the test run
mvn allure:report

# open the report
open target/allure-report/index.html
```

---

## Quick-reference cheat sheet

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE           │  UNIT TESTS                  │  E2E / INTEGRATION        │
├─────────────────────────────────────────────────────────────────────────────┤
│  backend-api/     │  ./gradlew unitTest           │  ./gradlew e2eTest        │
│  web-player/      │  npm test                     │  npm run e2e:docker       │
│  android-player/  │  ./gradlew test               │  ./gradlew connectedTest  │
│  ios-player/      │  swift test                   │  xcodebuild test …        │
│  qoe-auto-tests/  │  —                            │  mvn test -Dapi.base.url… │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE           │  REPORT COMMAND                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  backend-api/     │  ./gradlew allureReport                                  │
│                   │  open build/reports/tests/unitTest/index.html            │
│  web-player/      │  npx playwright show-report                              │
│                   │  npm run allure:report                                   │
│  android-player/  │  open app/build/reports/tests/testDebugUnitTest/…       │
│  ios-player/      │  xcpretty --report html  (see section 4.3)              │
│  qoe-auto-tests/  │  mvn allure:report && open target/allure-report/…       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No matching toolchains found` (Gradle) | Install Java 17: `brew install --cask temurin@17` |
| `Could not connect to Docker` | Start Docker Desktop |
| `backend is not healthy` | `docker compose logs backend` to inspect errors |
| `npm run e2e:docker` fails immediately | Ensure Docker web-player is running: `docker compose up -d` |
| `xcode-select` error on iOS build | `sudo xcode-select -switch /Applications/Xcode.app` |
| `allure: command not found` | `brew install allure` |
| Playwright browsers missing | `npm run e2e:install` (inside `web-player/`) |
