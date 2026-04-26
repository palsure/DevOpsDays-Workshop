# QoE Automation Tests

Java/TestNG test automation suite for end-to-end Quality of Experience validation across API, web, and mobile layers.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Java 17 |
| Test runner | TestNG |
| API testing | REST Assured |
| Web testing | Selenium WebDriver |
| Mobile testing | Appium |
| Build | Maven |
| Reports | Surefire XML + Maven site |

## Prerequisites

- Java 17+
- Maven 3.8+
- Backend API running on port 8080
- For web tests: ChromeDriver matching your Chrome version
- For mobile tests: Appium server running, connected device or emulator

## Setup

```bash
cd qoe-automation-tests
mvn dependency:resolve
```

### Configuration

Edit `src/test/resources/test-config.properties`:

```properties
api.base.url=http://localhost:8080/api/v1
web.player.url=http://localhost:3000
mobile.platform=android
appium.server.url=http://localhost:4723
test.timeout.seconds=30
```

## Running Tests

### All tests

```bash
mvn test
```

### Using TestNG suite (parallel execution)

```bash
mvn test -DsuiteXmlFile=src/test/resources/testng.xml
```

### API tests only

```bash
mvn test -Dtest=QoEMetricsApiTest
```

### Validation tests only

```bash
mvn test -Dtest=QoEValidationTest
```

### Web player tests only

```bash
mvn test -Dtest=WebPlayerQoETest
```

### Mobile tests only

```bash
mvn test -Dtest=MobileQoETest
```

### Skip a specific test class

```bash
mvn test -Dtest='!MobileQoETest'
```

### Run with a specific platform tag (TestNG groups)

```bash
mvn test -Dgroups=api
mvn test -Dgroups=validation
mvn test -Dgroups=mobile
```

## Test Reports

### Surefire XML (used by CI)

```
target/surefire-reports/*.xml
```

### HTML report

```bash
mvn surefire-report:report
open target/site/surefire-report.html
```

## CI Integration

Tests run in GitHub Actions as part of two workflows:

| Workflow | Job | Trigger |
|---|---|---|
| `qoe-validation.yml` | `qoe-test-framework` | Every push / PR |
| `build-acceptance-release.yml` | `acceptance-automation` | Release gate |

The CI `junit_to_summary.py` script parses the Surefire XML output to produce a GitHub step summary and Slack notification.

## Project Structure

```
qoe-automation-tests/
├── src/
│   ├── main/java/com/devopsdays/qoe/framework/
│   │   ├── validation/          # Validation engine (thresholds, scoring)
│   │   ├── models/              # Shared data models
│   │   └── utils/               # HTTP client, retry helpers
│   └── test/java/com/devopsdays/qoe/tests/
│       ├── api/                 # QoEMetricsApiTest — REST Assured API tests
│       ├── web/                 # WebPlayerQoETest — Selenium browser tests
│       ├── mobile/              # MobileQoETest — Appium device tests
│       └── validation/          # QoEValidationTest — threshold validation
├── src/test/resources/
│   ├── testng.xml               # Suite config (parallel groups, listeners)
│   └── test-config.properties   # URLs, timeouts, platform selection
└── pom.xml
```
