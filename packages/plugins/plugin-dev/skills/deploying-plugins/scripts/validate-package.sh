#!/bin/bash
# validate-package.sh - Validate plugin package loads correctly
#
# Tests that a plugin can be loaded by Claude Code without errors.
# Checks component registration (commands, skills, agents).
#
# Usage: validate-package.sh <plugin-path>
# Exit: 0 = loads successfully, 1 = load failure
#
# Dependencies: claude CLI

set -uo pipefail

PLUGIN_PATH="${1:-.}"
PLUGIN_PATH="${PLUGIN_PATH%/}"

# Resolve to absolute path
if [[ "$PLUGIN_PATH" != /* ]]; then
    PLUGIN_PATH="$(cd "$PLUGIN_PATH" 2>/dev/null && pwd)" || {
        echo "ERROR: Cannot access plugin path: $1"
        exit 1
    }
fi

if [[ ! -d "$PLUGIN_PATH" ]]; then
    echo "ERROR: Plugin path does not exist: $PLUGIN_PATH"
    exit 1
fi

echo "Package Validation: $PLUGIN_PATH"
echo "========================================"
echo ""

# Check if claude CLI is available
if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found"
    echo "Install Claude Code to validate packages"
    exit 1
fi

# Get plugin name from manifest
plugin_name="unknown"
if [[ -f "$PLUGIN_PATH/.claude-plugin/plugin.json" ]]; then
    plugin_name=$(jq -r '.name // "unknown"' "$PLUGIN_PATH/.claude-plugin/plugin.json" 2>/dev/null)
fi

echo "Plugin: $plugin_name"
echo ""

# Count components
commands_count=0
skills_count=0
agents_count=0

if [[ -d "$PLUGIN_PATH/commands" ]]; then
    commands_count=$(find "$PLUGIN_PATH/commands" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

if [[ -d "$PLUGIN_PATH/skills" ]]; then
    skills_count=$(find "$PLUGIN_PATH/skills" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

if [[ -d "$PLUGIN_PATH/agents" ]]; then
    agents_count=$(find "$PLUGIN_PATH/agents" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

echo "Components detected:"
echo "  Commands: $commands_count"
echo "  Skills: $skills_count"
echo "  Agents: $agents_count"
echo ""

# Validate with claude plugin validate
echo "Loading validation..."
if claude plugin validate "$PLUGIN_PATH" 2>&1 | grep -qiE "(valid|passed)"; then
    echo ""
    echo "✓ Plugin loads successfully"
    echo "✓ $commands_count command(s) registered"
    echo "✓ $skills_count skill(s) loaded"
    echo "✓ $agents_count agent(s) available"
    echo ""
    echo "========================================"
    echo "RESULT: Package validated successfully"
    echo "Ready for distribution."
    exit 0
else
    echo ""
    echo "✗ Plugin failed to load"
    echo ""
    echo "Run 'claude plugin validate $PLUGIN_PATH' for details"
    echo "Or use 'claude --debug --plugin-dir $PLUGIN_PATH' to debug"
    echo ""
    echo "========================================"
    echo "RESULT: Package validation failed"
    exit 1
fi
