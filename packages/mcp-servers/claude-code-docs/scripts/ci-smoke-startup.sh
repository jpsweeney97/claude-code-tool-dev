#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${RUNNER_TEMP:-/tmp}"
LOG_FILE="${TMP_DIR}/claude-code-docs-startup-smoke.log"
CACHE_PATH="${TMP_DIR}/claude-code-docs-startup-cache/llms-full.txt"

mkdir -p "$(dirname "${CACHE_PATH}")"

export REQUIRE_INDEX_ON_STARTUP=true
export CACHE_PATH

node "${ROOT_DIR}/dist/index.js" >"${LOG_FILE}" 2>&1 &
PID=$!

cleanup() {
  if kill -0 "${PID}" 2>/dev/null; then
    kill -TERM "${PID}" 2>/dev/null || true
    wait "${PID}" || true
  fi
}
trap cleanup EXIT

DEADLINE=$((SECONDS + 90))
while (( SECONDS < DEADLINE )); do
  if grep -q "Index ready" "${LOG_FILE}"; then
    exit 0
  fi
  if ! kill -0 "${PID}" 2>/dev/null; then
    echo "startup smoke failed: process exited before index became ready" >&2
    cat "${LOG_FILE}" >&2 || true
    exit 1
  fi
  sleep 1
done

echo "startup smoke failed: timed out waiting for 'Index ready' log line" >&2
cat "${LOG_FILE}" >&2 || true
exit 1

