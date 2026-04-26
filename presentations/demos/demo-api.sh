#!/usr/bin/env bash
# QoE workshop — API demo script. Run from anywhere; uses workshop-relative paths only for hints.
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8080}"

echo "== QoE API demo (BASE: ${API_BASE}) =="
echo

echo "-- Health --"
curl -sS "${API_BASE}/actuator/health" | head -c 400
echo
echo

echo "-- POST sample metric --"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_ID="workshop-$(date +%s)"
POST_BODY=$(cat <<JSON
{
  "platform": "web",
  "videoId": "workshop-demo",
  "sessionId": "${SESSION_ID}",
  "timestamp": "${TS}",
  "deviceInfo": {
    "deviceType": "desktop",
    "os": "Linux",
    "browser": "Chrome",
    "screenResolution": "1920x1080"
  },
  "metrics": {
    "playbackState": "playing",
    "currentTime": 30.0,
    "duration": 180.0,
    "totalBufferingTime": 1.2,
    "startupTime": 1600,
    "currentBitrate": 2500000,
    "bitrateSwitches": 1,
    "errorCount": 0,
    "playbackQuality": "excellent"
  }
}
JSON
)

curl -sS -X POST "${API_BASE}/api/v1/metrics" \
  -H "Content-Type: application/json" \
  -d "${POST_BODY}"
echo
echo

echo "-- GET metrics (platform=web, limit jq if available) --"
if command -v jq >/dev/null 2>&1; then
  curl -sS "${API_BASE}/api/v1/metrics?platform=web" | jq '.[0:5]'
else
  curl -sS "${API_BASE}/api/v1/metrics?platform=web" | head -c 1200
  echo
fi
echo

echo "-- GET summary (platform=web) --"
if command -v jq >/dev/null 2>&1; then
  curl -sS "${API_BASE}/api/v1/metrics/summary?platform=web" | jq .
else
  curl -sS "${API_BASE}/api/v1/metrics/summary?platform=web"
  echo
fi
echo

echo "-- GET videos --"
if command -v jq >/dev/null 2>&1; then
  curl -sS "${API_BASE}/api/v1/videos" | jq .
else
  curl -sS "${API_BASE}/api/v1/videos"
  echo
fi

echo
echo "Done. Open http://localhost:3000 (player) and http://localhost:8081/videos/ (CDN test) with compose stack running."
