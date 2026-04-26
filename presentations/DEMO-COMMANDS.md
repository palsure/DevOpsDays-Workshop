# Demo commands — QoE workshop

Assume the stack is up from repo root: `docker compose up -d --build`.

Set optional base URL for remote demos:

```bash
export API_BASE="${API_BASE:-http://localhost:8080}"
```

---

## 1. Health

```bash
curl -sS "${API_BASE}/actuator/health" | jq .
```

---

## 2. Ingest a QoE metric (`POST /api/v1/metrics`)

`timestamp` must be ISO-8601 instant. Adjust `sessionId` per demo.

```bash
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -sS -X POST "${API_BASE}/api/v1/metrics" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"web\",
    \"videoId\": \"workshop-demo\",
    \"sessionId\": \"facilitator-session-001\",
    \"timestamp\": \"${TS}\",
    \"deviceInfo\": {
      \"deviceType\": \"desktop\",
      \"os\": \"macOS\",
      \"browser\": \"Chrome\",
      \"screenResolution\": \"1920x1080\"
    },
    \"metrics\": {
      \"playbackState\": \"playing\",
      \"currentTime\": 42.0,
      \"duration\": 300.0,
      \"totalBufferingTime\": 0.8,
      \"startupTime\": 1400,
      \"currentBitrate\": 2800000,
      \"bitrateSwitches\": 2,
      \"errorCount\": 0,
      \"playbackQuality\": \"excellent\"
    }
  }" | jq .
```

**Poor experience variant** (for summary / validation story): set `"startupTime": 5000`, `"totalBufferingTime": 12`, `"errorCount": 4`, `"playbackQuality": "poor"`.

---

## 3. List metrics

All metrics:

```bash
curl -sS "${API_BASE}/api/v1/metrics" | jq '.[0:3]'
```

Filter by platform:

```bash
curl -sS "${API_BASE}/api/v1/metrics?platform=web" | jq 'length'
```

---

## 4. Summary

```bash
curl -sS "${API_BASE}/api/v1/metrics/summary?platform=web" | jq .
```

If no rows yet, the API returns a message payload; after POST, expect aggregates like `totalSessions`, `averageStartupTime`, etc.

---

## 5. Videos catalog

```bash
curl -sS "${API_BASE}/api/v1/videos" | jq .
```

(Empty array is valid if no seed data — explain catalog is populated via API or migrations in real deployments.)

---

## 6. Trends (optional — needs data in time window)

Requires `platform`, `startTime`, and `endTime` query params (ISO instants). Example window (last hour) — adjust times if you get empty arrays:

```bash
START=$(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '1 hour ago' +"%Y-%m-%dT%H:%M:%SZ")
END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -sS "${API_BASE}/api/v1/metrics/trends?platform=web&startTime=${START}&endTime=${END}" | jq .
```

On Linux use `date -u -d '1 hour ago'`; on macOS use `date -u -v-1H` as above.

---

## 7. Browser quick checks

- Open http://localhost:3000 — player UI; title should relate to QoE/Player (`WebPlayerQoETest` assertion).  
- Open http://localhost:8081/videos/ — static content for CDN simulation.

---

## 8. Automated tests (from repo)

```bash
cd qoe-automation-tests
mvn -q test -Dtest=QoEMetricsApiTest
mvn -q test -Dtest=QoEValidationTest
```

---

## 9. Pipeline acceptance (demo API — same rules as CI)

Create a run, push per-platform counts (`api`, `web`, `android`, `ios`, `automation`), then finalize. Pass rate is `sum(passed) / sum(total)`; status becomes `RELEASED` if it is ≥ the server threshold (default **80%** as a fraction `0.8` in config), else `BLOCKED`.

```bash
RUN=$(curl -sS -X POST "${API_BASE:-http://localhost:8080}/api/v1/pipeline-runs" \
  -H "Content-Type: application/json" \
  -d '{"githubRunId":"demo-cli"}' | jq -r .runId)

for p in api web android ios automation; do
  curl -sS -X POST "${API_BASE:-http://localhost:8080}/api/v1/pipeline-runs/${RUN}/platforms" \
    -H "Content-Type: application/json" \
    -d "{\"platform\":\"$p\",\"passed\":9,\"failed\":1,\"skipped\":0,\"total\":10}" > /dev/null
done

curl -sS -X POST "${API_BASE:-http://localhost:8080}/api/v1/pipeline-runs/${RUN}/finalize" | jq .
curl -sS "${API_BASE:-http://localhost:8080}/api/v1/pipeline-runs/latest" | jq .
```

GitHub Actions: see `.github/workflows/build-acceptance-release.yml` (aggregate **80%** gate, optional **Release** on `main` when the gate passes).

---

## 10. Teardown

```bash
docker compose down
```

To also remove the named volume (fresh DB next boot), which applies new Postgres init scripts such as pipeline tables:

```bash
docker compose down -v
```
