FROM gradle:7.6-jdk17 AS build

WORKDIR /app

COPY build.gradle settings.gradle ./
COPY src ./src

# Unit tests before packaging (no E2E / Testcontainers in image build)
RUN gradle unitTest bootJar --no-daemon

FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

# Fixed name from bootJar task — avoids ambiguous COPY when multiple jars exist
COPY --from=build /app/build/libs/application.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
