# Ops

Workshop utility resources covering infrastructure setup, observability, and shared schema definitions.

## Structure

```
ops/
├── infrastructure/          # Local streaming infrastructure scripts
│   ├── server/nginx.conf            # Nginx video CDN config
│   ├── transcoding/generate-hls.sh  # FFmpeg HLS transcoder
│   ├── test-content/generate-test-video.sh  # Synthetic test video generator
│   └── network-simulation/tc-slow.sh        # Linux traffic shaper
├── monitoring/              # New Relic observability config
│   └── newrelic/
│       ├── newrelic.yml             # Agent configuration
│       ├── dashboards/              # Dashboard JSON (importable)
│       ├── alerts/                  # Alert policy JSON
│       └── nrql-queries/            # Useful NRQL queries
└── shared/schema/           # Canonical QoE metrics schema
    ├── qoe-metrics.schema.json      # JSON Schema
    └── qoe-metrics.types.ts         # TypeScript type definitions
```

---

## Infrastructure

### Generate a synthetic test video (requires FFmpeg)

```bash
cd ops/infrastructure/test-content
./generate-test-video.sh output.mp4 30      # 30-second test video
```

### Transcode to HLS multi-bitrate streams

```bash
cd ops/infrastructure/transcoding
./generate-hls.sh /path/to/input.mp4 /path/to/output-dir
```

This produces 1080p / 720p / 480p HLS streams with a `master.m3u8` playlist.

### Serve videos locally with Nginx

The `server/nginx.conf` is used automatically by Docker Compose:

```bash
docker compose up nginx -d
# Videos served at http://localhost:8081/videos/
```

Or manually:

```bash
nginx -c $(pwd)/ops/infrastructure/server/nginx.conf
```

### Simulate a slow network (Linux only — requires root)

```bash
cd ops/infrastructure/network-simulation
sudo ./tc-slow.sh eth0 1mbit 100ms 1%
#                  ^     ^      ^    ^ packet loss
#                  |     |      latency
#                  |     bandwidth
#                  network interface
```

This is useful for deliberately triggering buffering events to validate QoE metric collection. Reset with:

```bash
sudo tc qdisc del dev eth0 root
```

---

## Monitoring (New Relic)

### Agent setup

Copy `newrelic.yml` into your application directory and set your license key:

```bash
cp ops/monitoring/newrelic/newrelic.yml backend-api/
# Set NEW_RELIC_LICENSE_KEY env var or edit newrelic.yml directly
```

### Import dashboard

1. Go to **New Relic → Dashboards → Import dashboard**
2. Paste the contents of `ops/monitoring/newrelic/dashboards/qoe-dashboard.json`

### Import alerts

Use the New Relic API or CLI to apply alert policies:

```bash
# Example using New Relic CLI (nr1)
nr1 nerdgraph:query --file ops/monitoring/newrelic/alerts/high-buffering.json
```

### Useful NRQL queries

See `ops/monitoring/newrelic/nrql-queries/qoe-metrics.nrql` for ready-to-use queries including:

- Average startup time by platform
- Buffering rate over time
- Error rate by video ID
- Quality score distribution

---

## Shared Schema

The canonical definition of the QoE metric payload used by all player clients and validated by the backend.

### JSON Schema

`ops/shared/schema/qoe-metrics.schema.json` — use to validate payloads in tests or tooling:

```bash
# Validate a payload with ajv-cli
npx ajv validate -s ops/shared/schema/qoe-metrics.schema.json -d your-payload.json
```

### TypeScript types

`ops/shared/schema/qoe-metrics.types.ts` — import into any TypeScript project:

```typescript
import type { QoEMetricPayload } from '../../ops/shared/schema/qoe-metrics.types'
```

When the schema changes, update both files and bump the Flyway migration in `backend-api/src/main/resources/db/migration/` if database columns are affected.
