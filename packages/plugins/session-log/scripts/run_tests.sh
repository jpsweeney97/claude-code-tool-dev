#!/bin/bash
# Run tests using system Python (workaround for uv sandbox issues)
# Usage: ./scripts/run_tests.sh [pytest args]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
MCP_DIR="$PLUGIN_DIR/mcp"
TESTS_DIR="$PLUGIN_DIR/tests"

# Ensure pytest is available
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing pytest to temp directory..."
    python3 -m pip install pytest -q --target /tmp/claude/pytest_temp 2>/dev/null
    export PYTHONPATH="/tmp/claude/pytest_temp:$PYTHONPATH"
fi

# Run tests with mcp directory in PYTHONPATH
cd "$PLUGIN_DIR"
PYTHONPATH="$MCP_DIR:$PYTHONPATH" python3 -m pytest "$TESTS_DIR" "$@"
