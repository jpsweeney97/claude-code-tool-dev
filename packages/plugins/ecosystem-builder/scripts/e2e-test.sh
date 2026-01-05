#!/bin/bash
# End-to-end test for ecosystem-builder CLI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_HOME="${TMPDIR:-/tmp}/ecosystem-builder-e2e-$$"
cleanup() { rm -rf "$TEST_HOME"; }
trap cleanup EXIT

echo "=== Ecosystem Builder E2E Test ==="
echo "Test home: $TEST_HOME"

mkdir -p "$TEST_HOME"
export HOME="$TEST_HOME"
cd "$PROJECT_DIR"

echo -e "\n1. Run with --mock..."
uv run bin/ecosystem-builder run --artifacts 2 --mock

echo -e "\n2. Check status..."
uv run bin/ecosystem-builder status

echo -e "\n3. Review staged..."
uv run bin/ecosystem-builder review

echo -e "\n4. Verify directories..."
ls -la "$TEST_HOME/.claude/ecosystem-builder/state/" 2>/dev/null || echo "(no state)"
ls -la "$TEST_HOME/.claude/ecosystem-builder/staging/skills/" 2>/dev/null || echo "(no staging)"

# Verify expected outcomes
if [[ ! -d "$TEST_HOME/.claude/ecosystem-builder/state" ]]; then
    echo "ERROR: State directory not created" >&2
    exit 1
fi

if [[ ! -d "$TEST_HOME/.claude/ecosystem-builder/staging/skills" ]]; then
    echo "ERROR: Staging directory not created" >&2
    exit 1
fi

echo -e "\n=== Test Complete ==="
