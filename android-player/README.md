# Android Player

Kotlin Android app using ExoPlayer for HLS video playback with real-time QoE metrics collection.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Kotlin |
| Video | ExoPlayer (Media3) |
| UI | Jetpack Compose / XML layouts |
| Build | Gradle (Kotlin DSL) |
| Min SDK | Android 8.0 (API 26) |

## Prerequisites

- Android Studio Hedgehog (2023.1) or later
- Android SDK API 34
- JDK 17
- Backend API running (see root `docker-compose.yml`)

## Setup

### 1. Open in Android Studio

```
File → Open → select the android-player/ directory
```

Wait for Gradle sync to complete.

### 2. Configure API URL

Open `app/src/main/java/com/devopsdays/qoe/android/network/QoEApiService.kt` and set the base URL:

| Environment | URL |
|---|---|
| Android Emulator | `http://10.0.2.2:8080/api/v1` |
| Physical device (same Wi-Fi) | `http://<your-machine-ip>:8080/api/v1` |

### 3. Run the app

Select a device or emulator in Android Studio and press **Run** (Shift+F10), or from the command line:

```bash
cd android-player
./gradlew installDebug
```

## Running Tests

### Unit tests

```bash
./gradlew test
```

### Instrumented tests (requires connected device or emulator)

```bash
./gradlew connectedAndroidTest
```

### Lint

```bash
./gradlew lint
```

## Build

### Debug APK

```bash
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk
```

### Release APK (requires signing config)

```bash
./gradlew assembleRelease
```

## Firebase App Distribution

Use the deploy script to build and upload a release build to Firebase App Distribution:

```bash
cd android-player
FIREBASE_APP_ID=<your-app-id> APPLE_TEAM_ID=<team> ./deploy-firebase.sh
```

Prerequisites: `firebase-tools` installed and `firebase login` completed.

## Project Structure

```
android-player/
├── app/
│   └── src/
│       ├── main/
│       │   ├── java/com/devopsdays/qoe/android/
│       │   │   ├── MainActivity.kt       # Entry point
│       │   │   ├── player/               # ExoPlayer setup + listeners
│       │   │   ├── collector/            # QoE metrics collector
│       │   │   └── network/              # API client (Retrofit / OkHttp)
│       │   └── res/                      # Layouts, drawables, strings
│       └── test/                         # Unit tests
├── build.gradle.kts
├── settings.gradle.kts
└── deploy-firebase.sh
```

## QoE Metrics Collected

Every 5 seconds the app sends a payload to `POST /api/v1/metrics` including:

- Platform: `android`
- Video ID and session ID
- Device info (model, OS version, screen resolution)
- Playback state (playing / paused / buffering / error)
- Current time and duration
- Buffering events and total buffering time
- Current bitrate and resolution
- Bitrate switch count
- Playback quality score (excellent / good / fair / poor)
