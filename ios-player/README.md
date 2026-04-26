# QoE iOS Player

iOS video player module containing both a reusable Swift Package library and a runnable SwiftUI demo app.

## Structure

```
ios-player/
├── Package.swift                   # Swift Package (QoePlayer library + tests)
├── Sources/QoePlayer/
│   ├── QoECollector.swift          # Core metrics collector (UIKit)
│   └── VideoPlayerViewController.swift  # AVPlayer-backed view controller
├── Tests/QoePlayerTests/           # Unit tests for the library
├── QoePlayerApp/                   # SwiftUI demo app sources
│   ├── QoePlayerAppApp.swift       # App entry point (@main)
│   ├── ContentView.swift           # Stream catalog list
│   ├── VideoPlayerView.swift       # Full-screen player with QoE collection
│   └── QoECollector.swift          # SwiftUI-optimised collector (@MainActor)
├── QoePlayerApp.xcodeproj          # Xcode project for the demo app
└── deploy-firebase.sh              # Firebase App Distribution deploy script
```

## Library (Swift Package)

The `QoePlayer` Swift Package provides a `VideoPlayerViewController` and `QoECollector` that can be added to any iOS project via Swift Package Manager.

### Add as a dependency

In `Package.swift`:
```swift
.package(path: "../ios-player")
```

Or in Xcode: **File → Add Package Dependencies** → choose local path.

### Usage

```swift
import QoePlayer

let playerVC = VideoPlayerViewController()
playerVC.videoURL = URL(string: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
playerVC.videoId = "ios-demo-1"
playerVC.apiBaseURL = "http://localhost:8080/api/v1"
present(playerVC, animated: true)
```

### Run library tests

```bash
cd ios-player
swift test
```

## Demo App (Xcode Project)

The `QoePlayerApp.xcodeproj` is a SwiftUI workshop demo app with a stream catalog and full-screen HLS playback.

### Run on simulator

```bash
cd ios-player
xcodebuild \
  -project QoePlayerApp.xcodeproj \
  -scheme QoePlayerApp \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  build
```

Or open `QoePlayerApp.xcodeproj` in Xcode and press **Run**.

### Deploy to Firebase App Distribution

```bash
cd ios-player
FIREBASE_APP_ID=<your-app-id> APPLE_TEAM_ID=<your-team-id> ./deploy-firebase.sh
```

## Configuration

| Setting | Location | Default |
|---|---|---|
| API base URL (library) | `VideoPlayerViewController.apiBaseURL` | `http://localhost:8080/api/v1` |
| API base URL (app) | `QoePlayerApp/QoECollector.swift` → `apiBase` | `http://localhost:8080/api/v1` |

For a physical device replace `localhost` with your computer's local IP address.
