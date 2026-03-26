#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tsc 1>&2
exec node dist/index.js
