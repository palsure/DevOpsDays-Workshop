FROM gradle:8.7-jdk21 AS build

WORKDIR /app

COPY build.gradle settings.gradle gradle.properties ./
COPY gradle ./gradle
COPY src ./src

# Tests run in CI pipeline — skip here to keep image build fast
RUN gradle bootJar -x test --no-daemon

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

# Fixed name from bootJar task — avoids ambiguous COPY when multiple jars exist
COPY --from=build /app/build/libs/application.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
