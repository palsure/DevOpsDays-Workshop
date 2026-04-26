# Web Player

React/TypeScript HLS video player that collects QoE metrics and sends them to the backend API every 5 seconds.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | React 18, TypeScript |
| Video | HLS.js |
| Build | Vite |
| Unit tests | Vitest |
| E2E tests | Playwright |
| Reports | Allure |

## Prerequisites

- Node.js 18+
- npm 9+
- Backend API running on port 8080

## Setup

```bash
cd web-player
npm install
```

Create a `.env` file (copy from example below):

```env
VITE_API_URL=http://localhost:8080/api/v1
```

> For Docker: the API URL is injected at build time via `VITE_API_URL`.

## Running the App

```bash
npm run dev
```

Opens at **http://localhost:5173**.

## Running Tests

### Unit tests

```bash
npm test
```

### E2E tests (Playwright — requires running app + backend)

```bash
# Install browsers once
npm run e2e:install

# Run against local dev server
npm run e2e

# Run with throttled network profile (triggers buffering events)
npm run e2e:throttle

# Run all profiles
npm run e2e:all
```

### E2E tests against Docker stack

```bash
# Start full stack first
docker compose up -d

npm run e2e:docker
npm run e2e:docker:throttle
npm run e2e:docker:all
```

### Interactive / debug modes

```bash
npm run e2e:headed     # visible browser
npm run e2e:debug      # Playwright inspector
npm run e2e:ui         # Playwright UI mode
```

### Allure report

```bash
# Generate + open
npm run allure:report

# Generate only
npm run allure:generate

# Open existing report
npm run allure:open
```

### Playwright HTML report

```bash
npm run report
```

## Build

```bash
npm run build
# Output in dist/
```

## Project Structure

```
web-player/
├── src/
│   ├── components/      # React components (Player, MetricsOverlay, etc.)
│   ├── services/        # QoE metric collection + API client
│   └── types/           # TypeScript type definitions
├── e2e/                 # Playwright E2E test specs
├── playwright.config.ts # Playwright config (chromium + throttle profiles)
├── vite.config.ts
├── Dockerfile
└── package.json
```

## Docker

```bash
# Build image
docker build -t qoe-web-player -f web-player/Dockerfile .

# Or start the full stack
docker compose up -d
```

The app is served via Nginx on **http://localhost:3000** in Docker.
