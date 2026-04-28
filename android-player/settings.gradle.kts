pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    // The New Relic Android plugin is published to Maven Central as an
    // artifact (`com.newrelic.agent.android:agent-gradle-plugin`) but does NOT
    // ship a plugin marker on plugins.gradle.org. Map the requested plugin id
    // to the real Maven coordinates so the `plugins { id("…") }` DSL resolves.
    resolutionStrategy {
        eachPlugin {
            if (requested.id.id == "com.newrelic.agent.android") {
                useModule("com.newrelic.agent.android:agent-gradle-plugin:${requested.version}")
            }
        }
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "QoePlayer"
include(":app")
