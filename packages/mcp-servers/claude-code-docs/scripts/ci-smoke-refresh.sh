#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${RUNNER_TEMP:-/tmp}"
LOG_FILE="${TMP_DIR}/claude-code-docs-refresh-smoke.log"
CACHE_PATH="${TMP_DIR}/claude-code-docs-refresh-cache/llms-full.txt"
STDIN_FIFO="${TMP_DIR}/claude-code-docs-refresh-smoke-$$.fifo"

mkdir -p "$(dirname "${CACHE_PATH}")"
mkfifo "${STDIN_FIFO}"

export CACHE_PATH
export REFRESH_INTERVAL_MS=60000

# Keep stdin open for the stdio transport so the process stays alive long
# enough to execute at least one scheduled background refresh.
exec 3<>"${STDIN_FIFO}"
node "${ROOT_DIR}/dist/index.js" <&3 >"${LOG_FILE}" 2>&1 &
PID=$!

cleanup() {
  exec 3>&- || true
  if kill -0 "${PID}" 2>/dev/null; then
    kill -TERM "${PID}" 2>/dev/null || true
    wait "${PID}" || true
  fi
}
trap cleanup EXIT

DEADLINE=$((SECONDS + 150))
while (( SECONDS < DEADLINE )); do
  if grep -q "Background refresh complete" "${LOG_FILE}"; then
    exit 0
  fi
  if ! kill -0 "${PID}" 2>/dev/null; then
    echo "refresh smoke failed: process exited before refresh completed" >&2
    cat "${LOG_FILE}" >&2 || true
    exit 1
  fi
  sleep 1
done

echo "refresh smoke failed: timed out waiting for a background refresh run" >&2
cat "${LOG_FILE}" >&2 || true
exit 1
