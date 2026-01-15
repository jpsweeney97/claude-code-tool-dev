#!/usr/bin/env bash
# validate_skill.sh — Structural validation for SKILL.md files
#
# Exit codes:
#   0 - Pass (or not a skill file)
#   1 - Warning (non-blocking issues)
#   2 - Block (structural errors - missing required fields)
#
# Environment:
#   $TOOL_INPUT - JSON containing file_path from Write/Edit tool

set -euo pipefail

# Early exit: skip if SKILL.md not in input at all (avoids grep/sed overhead)
[[ "${TOOL_INPUT:-}" != *"SKILL.md"* ]] && exit 0

# Parse file path from tool input
FILE_PATH=$(echo "$TOOL_INPUT" | grep -oE '"file_path"\s*:\s*"[^"]+"' | sed 's/.*: *"//' | sed 's/"$//' 2>/dev/null || true)

# Fallback: try 'path' field
if [[ -z "$FILE_PATH" ]]; then
    FILE_PATH=$(echo "$TOOL_INPUT" | grep -oE '"path"\s*:\s*"[^"]+"' | sed 's/.*: *"//' | sed 's/"$//' 2>/dev/null || true)
fi

# Skip if we couldn't parse the path
[[ -z "$FILE_PATH" ]] && exit 0

# Skip if not a SKILL.md file
[[ ! "$FILE_PATH" =~ SKILL\.md$ ]] && exit 0

# Skip if file doesn't exist (shouldn't happen for PostToolUse, but safety check)
[[ ! -f "$FILE_PATH" ]] && exit 0

# --- Validation begins ---

ERRORS=()
WARNINGS=()

# Extract frontmatter (between first two ---)
FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "$FILE_PATH" 2>/dev/null | sed '1d;$d')

if [[ -z "$FRONTMATTER" ]]; then
    ERRORS+=("Missing YAML frontmatter (must start with ---)")
else
    # Check required fields
    if ! echo "$FRONTMATTER" | grep -qE '^name:\s*\S'; then
        ERRORS+=("Missing required field: 'name' in frontmatter")
    fi

    if ! echo "$FRONTMATTER" | grep -qE '^description:\s*\S'; then
        ERRORS+=("Missing required field: 'description' in frontmatter")
    fi
fi

# Count H2 sections (## Heading)
SECTION_COUNT=$(grep -cE '^## ' "$FILE_PATH" 2>/dev/null || echo 0)

if [[ "$SECTION_COUNT" -lt 11 ]]; then
    WARNINGS+=("Found $SECTION_COUNT/11 sections (skill may be incomplete)")
fi

# --- Report results ---

# Print errors
for err in "${ERRORS[@]:-}"; do
    [[ -n "$err" ]] && echo "ERROR: $err" >&2
done

# Print warnings
for warn in "${WARNINGS[@]:-}"; do
    [[ -n "$warn" ]] && echo "WARNING: $warn" >&2
done

# Exit with appropriate code
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "Skill validation failed: ${#ERRORS[@]} error(s)" >&2
    exit 2
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    exit 1
fi

exit 0
