#!/bin/bash
# validate-docs.sh - Pre-commit hook for doc-auditor
# Validates documentation before allowing git commit
#
# This hook is DISABLED by default. To enable:
# 1. Edit hooks/hooks.json
# 2. Remove "disabled": true or set to false
#
# Behavior:
# - Blocks commits when ANY documentation issues exist
# - Requires scan results to be <1 hour old
# - Only checks when markdown files are being committed

set -e

# Get list of staged markdown files
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.md$' || true)

if [ -z "$STAGED_DOCS" ]; then
    # No docs being committed, allow
    exit 0
fi

# Check if scan results exist
SCAN_FILE=".claude/doc-auditor/scan-results.json"
if [ ! -f "$SCAN_FILE" ]; then
    echo "❌ No documentation scan found."
    echo "   Run /doc-auditor:scan before committing."
    exit 1
fi

# Check scan age (must be < 1 hour old)
# Handle both BSD (macOS) and GNU (Linux) stat
if stat -f %m "$SCAN_FILE" >/dev/null 2>&1; then
    # BSD stat (macOS)
    FILE_MTIME=$(stat -f %m "$SCAN_FILE")
else
    # GNU stat (Linux)
    FILE_MTIME=$(stat -c %Y "$SCAN_FILE")
fi

CURRENT_TIME=$(date +%s)
SCAN_AGE=$((CURRENT_TIME - FILE_MTIME))

if [ "$SCAN_AGE" -gt 3600 ]; then
    echo "⚠️  Documentation scan is stale (>1 hour old)."
    echo "   Run /doc-auditor:scan to refresh."
    exit 1
fi

# Check for ANY issues (strictest enforcement)
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  jq not installed. Cannot validate scan results."
    echo "   Install jq or disable this hook."
    exit 1
fi

ISSUE_COUNT=$(jq '.summary.total_issues // 0' "$SCAN_FILE" 2>/dev/null)

if [ "$ISSUE_COUNT" = "null" ] || [ -z "$ISSUE_COUNT" ]; then
    echo "⚠️  Scan results may be corrupted."
    echo "   Run /doc-auditor:scan to regenerate."
    exit 1
fi

if [ "$ISSUE_COUNT" -gt 0 ]; then
    echo "❌ Documentation has $ISSUE_COUNT issue(s)."
    echo ""

    # Show breakdown by severity
    jq -r '.summary.by_severity | to_entries[] | select(.value > 0) | "   \(.key): \(.value)"' "$SCAN_FILE" 2>/dev/null || true

    echo ""
    echo "   Run /doc-auditor:repair to resolve issues."
    exit 1
fi

echo "✅ Documentation passes all checks."
exit 0
