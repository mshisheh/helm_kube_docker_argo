#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:?Usage: $0 http://EXTERNAL_IP}
REQUESTS=${REQUESTS:-100}
CONCURRENCY=${CONCURRENCY:-10}
PAYLOAD='{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

if command -v hey >/dev/null; then
  hey -n "${REQUESTS}" -c "${CONCURRENCY}" -m POST \
    -H 'Content-Type: application/json' -d "${PAYLOAD}" "${BASE_URL}/predict"
else
  echo "Install 'hey' for concurrent load; sending ${REQUESTS} sequential curl requests." >&2
  for _ in $(seq 1 "${REQUESTS}"); do
    curl --fail --silent --output /dev/null -H 'Content-Type: application/json' \
      -d "${PAYLOAD}" "${BASE_URL}/predict"
  done
  echo "Completed ${REQUESTS} requests."
fi
