#!/bin/sh
set -eu
BASE="${BASE:-http://localhost:8080}"
curl -fsS "$BASE/health/live"
curl -fsS -H 'Content-Type: application/json' -d '{"question":"What is a transformer?"}' "$BASE/query"
