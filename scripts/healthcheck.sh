#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-http://localhost:8000}
echo "Checking $BASE/health" && curl -sf $BASE/health | jq '.'
echo "Metrics sample:" && curl -sf $BASE/metrics | head -n 5
echo "OK"
