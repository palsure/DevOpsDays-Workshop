# QoE Web Player

React/TypeScript web video player with HLS.js and QoE metrics collection.

## Features

- HLS video playback using HLS.js
- Real-time QoE metrics collection
- Automatic metrics submission to backend API
- Buffering event tracking
- Error tracking
- Bitrate switch detection
- Quality assessment

## Setup

```bash
npm install
npm run dev
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8080/api/v1
```

## Usage

The player automatically collects and sends QoE metrics to the backend API every 5 seconds. Metrics include:

- Playback state
- Current time and duration
- Buffering events
- Startup time
- Current bitrate and resolution
- Bitrate switches
- Errors
- Frame statistics
- Network speed estimation
- Playback quality assessment
