#!/bin/bash
# preflight.sh - Pre-flight validation for plugin deployment
#
# Wraps 'claude plugin validate' and adds additional deployment checks:
# - Secrets detection (API keys, tokens, passwords)
# - Path portability (${CLAUDE_PLUGIN_ROOT} usage)
# - Test presence check (informational)
#
# Usage: preflight.sh <plugin-path>
# Exit: 0 = all checks pass, 1 = failures found
#
# Dependencies: claude CLI, grep

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

errors=0
warnings=0

print_result() {
    local status="$1"
    local message="$2"
    if [[ "$status" == "pass" ]]; then
        echo "✓ $message"
    elif [[ "$status" == "fail" ]]; then
        echo "✗ $message"
        ((errors++))
    elif [[ "$status" == "warn" ]]; then
        echo "⚠ $message"
        ((warnings++))
    fi
}

echo "Pre-flight Checks for: $PLUGIN_PATH"
echo "========================================"
echo ""

# Check 1: claude plugin validate
echo "1. Structure Validation"
if command -v claude &>/dev/null; then
    if claude plugin validate "$PLUGIN_PATH" 2>&1 | grep -qiE "(valid|passed)"; then
        print_result "pass" "Plugin structure valid (claude plugin validate)"
    else
        print_result "fail" "Plugin structure invalid - run 'claude plugin validate $PLUGIN_PATH' for details"
    fi
else
    print_result "warn" "claude CLI not found - skipping structure validation"
fi
echo ""

# Check 2: Secrets detection
echo "2. Secrets Scan"
SECRET_PATTERNS=(
    'api[_-]?key\s*[=:]\s*["\x27][A-Za-z0-9]'
    'secret[_-]?key\s*[=:]\s*["\x27][A-Za-z0-9]'
    'password\s*[=:]\s*["\x27][A-Za-z0-9]'
    'token\s*[=:]\s*["\x27][A-Za-z0-9]'
    'sk-[A-Za-z0-9]{20,}'
    'ghp_[A-Za-z0-9]{36}'
    'gho_[A-Za-z0-9]{36}'
)

secrets_found=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    # Exclude common placeholder patterns used in documentation
    if grep -rEi "$pattern" "$PLUGIN_PATH" --include="*.md" --include="*.json" --include="*.sh" --include="*.py" 2>/dev/null \
        | grep -viE "example|placeholder|your[-_]|<[^>]+>|\{[^}]+\}|mypassword|\"password\"|xxx|changeme|dummy|test[-_]?key|sample" \
        | head -1 > /dev/null; then
        secrets_found=1
        break
    fi
done

if [[ $secrets_found -eq 0 ]]; then
    print_result "pass" "No hardcoded secrets detected"
else
    print_result "fail" "Potential secrets found - review and remove hardcoded credentials"
fi
echo ""

# Check 3: Path portability
echo "3. Path Portability"
absolute_paths_found=0

# Check hooks.json for absolute paths
if [[ -f "$PLUGIN_PATH/hooks/hooks.json" ]]; then
    if grep -E '"/[A-Za-z]' "$PLUGIN_PATH/hooks/hooks.json" 2>/dev/null | grep -v 'CLAUDE_PLUGIN_ROOT' > /dev/null; then
        absolute_paths_found=1
    fi
fi

# Check .mcp.json for absolute paths
if [[ -f "$PLUGIN_PATH/.mcp.json" ]]; then
    if grep -E '"/[A-Za-z]' "$PLUGIN_PATH/.mcp.json" 2>/dev/null | grep -v 'CLAUDE_PLUGIN_ROOT' > /dev/null; then
        absolute_paths_found=1
    fi
fi

if [[ $absolute_paths_found -eq 0 ]]; then
    print_result "pass" "Paths use \${CLAUDE_PLUGIN_ROOT} (portable)"
else
    print_result "fail" "Absolute paths found - use \${CLAUDE_PLUGIN_ROOT} for portability"
fi
echo ""

# Check 4: Required documentation
echo "4. Documentation"
if [[ -f "$PLUGIN_PATH/README.md" ]]; then
    print_result "pass" "README.md exists"
else
    print_result "fail" "README.md missing (required for distribution)"
fi

if [[ -f "$PLUGIN_PATH/CHANGELOG.md" ]]; then
    print_result "pass" "CHANGELOG.md exists"
else
    print_result "warn" "CHANGELOG.md missing (recommended)"
fi
echo ""

# Check 5: Tests presence (informational)
echo "5. Tests"
if find "$PLUGIN_PATH" -name "*.test.*" -o -name "*_test.*" -o -name "test_*" 2>/dev/null | head -1 | grep -q .; then
    print_result "pass" "Tests found"
elif find "$PLUGIN_PATH/scripts" -name "validate*.sh" 2>/dev/null | head -1 | grep -q .; then
    print_result "pass" "Validation scripts found"
else
    print_result "warn" "No tests found (optional but recommended)"
fi
echo ""

# Summary
echo "========================================"
if [[ $errors -eq 0 ]]; then
    if [[ $warnings -eq 0 ]]; then
        echo "RESULT: All checks passed"
    else
        echo "RESULT: Passed with $warnings warning(s)"
    fi
    echo "Ready for deployment."
    exit 0
else
    echo "RESULT: $errors error(s), $warnings warning(s)"
    echo "Fix errors before proceeding."
    exit 1
fi
