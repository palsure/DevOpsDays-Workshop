# QoE Android Player

Android video player with ExoPlayer and QoE metrics collection.

## Features

- HLS video playback using ExoPlayer
- Real-time QoE metrics collection
- Automatic metrics submission to backend API
- Buffering event tracking
- Error tracking
- Bitrate switch detection
- Quality assessment

## Setup

1. Open the project in Android Studio
2. Sync Gradle files
3. Run on an emulator or device

## Configuration

Update the API base URL in `QoEApiService.kt`:
- For emulator: `http://10.0.2.2:8080/api/v1`
- For physical device: Use your computer's IP address

## Usage

1. Enter an HLS video URL
2. Enter a video ID
3. Tap "Play Video"
4. Metrics are automatically collected and sent every 5 seconds
