# QoE Test Automation Framework

Test automation framework for Quality of Experience validation across platforms, following quality-engineering-test patterns.

## Features

- **API Tests**: REST API validation using REST Assured
- **Web Tests**: Selenium-based web player testing
- **Mobile Tests**: Appium-based mobile app testing (Android/iOS)
- **Validation Tests**: QoE metrics validation using custom validation engine
- **TestNG**: Test execution and reporting

## Structure

```
qoe-automation-tests/
├── src/main/java/com/devopsdays/qoe/framework/
│   ├── validation/          # Validation engine
│   ├── models/              # Data models
│   └── utils/               # Utility classes
├── src/test/java/com/devopsdays/qoe/tests/
│   ├── api/                 # API tests
│   ├── web/                 # Web player tests
│   ├── mobile/              # Mobile app tests
│   └── validation/          # Validation tests
└── src/test/resources/
    ├── testng.xml           # TestNG suite configuration
    └── test-config.properties
```

## Running Tests

### All Tests
```bash
mvn test
```

### Specific Test Suite
```bash
mvn test -DsuiteXmlFile=src/test/resources/testng.xml
```

### API Tests Only
```bash
mvn test -Dtest=QoEMetricsApiTest
```

### Web Tests Only
```bash
mvn test -Dtest=WebPlayerQoETest
```

### Mobile Tests Only
```bash
mvn test -Dtest=MobileQoETest
```

## Configuration

Edit `src/test/resources/test-config.properties` to configure:
- API base URL
- Web player URL
- Mobile platform (android/ios)
- Appium server URL
- Timeouts

## Prerequisites

- Java 17+
- Maven 3.8+
- ChromeDriver (for web tests)
- Appium server (for mobile tests)
- Backend API running (for API tests)

## CI/CD Integration

The framework is designed to run in CI/CD pipelines via GitHub Actions. See `.github/workflows/qoe-validation.yml` for example usage.
