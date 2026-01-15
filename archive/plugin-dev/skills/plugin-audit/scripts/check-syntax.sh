#!/bin/bash
# check-syntax.sh - Layer 1: Syntax validation for plugin files
#
# Validates JSON and YAML syntax. Does NOT validate semantics, schemas, or content.
# Syntax errors are always CRITICAL - they prevent the plugin from loading.
#
# Usage: check-syntax.sh <plugin-path>
# Output: JSON objects (one per line) for each error found
# Exit: Count of errors (0 = success)
#
# Dependencies: jq (JSON), yq (YAML)

# Note: -e omitted intentionally; functions use return codes for control flow
set -uo pipefail

PLUGIN_PATH="${1:-.}"
PLUGIN_PATH="${PLUGIN_PATH%/}"  # Remove trailing slash

# Resolve to absolute path for consistent relative path calculation
if [[ "$PLUGIN_PATH" != /* ]]; then
    PLUGIN_PATH="$(cd "$PLUGIN_PATH" 2>/dev/null && pwd)"
fi

if [[ ! -d "$PLUGIN_PATH" ]]; then
    echo '{"file": ".", "line": 0, "error": "Plugin path does not exist or is not a directory", "severity": "CRITICAL"}'
    exit 1
fi

errors=0

# Emit a structured error
emit_error() {
    local file="$1"
    local line="$2"
    local error="$3"
    local severity="${4:-CRITICAL}"

    # Make path relative to plugin root
    local rel_file="${file#"$PLUGIN_PATH"/}"

    # Escape special characters in error message for JSON
    local escaped_error
    escaped_error=$(printf '%s' "$error" | jq -Rs '.')

    echo "{\"file\": \"$rel_file\", \"line\": $line, \"error\": $escaped_error, \"severity\": \"$severity\"}"
}

# Check if required tools are available
check_dependencies() {
    local missing=0

    if ! command -v jq &>/dev/null; then
        emit_error "." 0 "Required dependency 'jq' not found"
        ((missing++))
    fi

    if ! command -v yq &>/dev/null; then
        emit_error "." 0 "Required dependency 'yq' not found"
        ((missing++))
    fi

    return $missing
}

# Validate a single JSON file
# Returns: 0 if valid, 1 if invalid
validate_json_file() {
    local file="$1"
    local required="${2:-false}"  # Is this file required to exist?

    if [[ ! -f "$file" ]]; then
        if [[ "$required" == "true" ]]; then
            emit_error "$file" 0 "Required file does not exist"
            return 1
        fi
        return 0  # Optional file not present is OK
    fi

    # Try to parse the JSON
    local parse_error
    if ! parse_error=$(jq empty "$file" 2>&1); then
        # Extract line number from jq error if available
        # jq errors look like: "parse error (at <filename>:3): Expected..."
        local line=0
        if [[ "$parse_error" =~ :([0-9]+)\) ]]; then
            line="${BASH_REMATCH[1]}"
        fi

        # Clean up error message
        local clean_error
        clean_error=$(echo "$parse_error" | head -1 | sed 's/^parse error[^:]*: //')

        emit_error "$file" "$line" "Invalid JSON: $clean_error"
        return 1
    fi

    return 0
}

# Validate YAML frontmatter in a markdown file
# Returns: 0 if valid or no frontmatter, 1 if invalid frontmatter
validate_yaml_frontmatter() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    # Check if file starts with ---
    local first_line
    first_line=$(head -1 "$file")
    if [[ "$first_line" != "---" ]]; then
        # No frontmatter - not an error at syntax level
        return 0
    fi

    # Find the closing --- and extract frontmatter
    # Use awk to extract content between first and second ---
    local frontmatter
    frontmatter=$(awk '
        /^---$/ {
            if (count == 0) { count = 1; next }
            if (count == 1) { exit }
        }
        count == 1 { print }
    ' "$file")

    # Check if closing --- was found
    local has_closing
    has_closing=$(awk '/^---$/ { count++ } count == 2 { found = 1; exit } END { print found + 0 }' "$file")

    if [[ "$has_closing" != "1" ]]; then
        emit_error "$file" 1 "Unclosed frontmatter: missing closing '---'"
        return 1
    fi

    if [[ -z "$frontmatter" ]]; then
        # Empty frontmatter between --- and ---
        # This is technically valid YAML (empty document)
        return 0
    fi

    # Validate YAML syntax using yq
    local parse_error
    if ! parse_error=$(echo "$frontmatter" | yq '.' 2>&1 >/dev/null); then
        # yq errors often contain line info like "line 3:"
        local line=1  # Default to frontmatter start
        if [[ "$parse_error" =~ line[[:space:]]+([0-9]+) ]]; then
            line="${BASH_REMATCH[1]}"
            # Add 1 for the opening ---
            line=$((line + 1))
        fi

        # Clean up error message
        local clean_error
        clean_error=$(echo "$parse_error" | head -1)

        emit_error "$file" "$line" "Invalid YAML frontmatter: $clean_error"
        return 1
    fi

    return 0
}

# Main validation logic
main() {
    # Check dependencies first
    if ! check_dependencies; then
        exit 1
    fi

    # 1. Validate plugin.json (required)
    local manifest="$PLUGIN_PATH/.claude-plugin/plugin.json"
    if ! validate_json_file "$manifest" true; then
        ((errors++))
    fi

    # 2. Validate hooks.json (optional)
    local hooks="$PLUGIN_PATH/hooks/hooks.json"
    if ! validate_json_file "$hooks" false; then
        ((errors++))
    fi

    # 3. Validate .mcp.json (optional)
    local mcp="$PLUGIN_PATH/.mcp.json"
    if ! validate_json_file "$mcp" false; then
        ((errors++))
    fi

    # 4. Validate YAML frontmatter in all markdown files
    while IFS= read -r -d '' mdfile; do
        if ! validate_yaml_frontmatter "$mdfile"; then
            ((errors++))
        fi
    done < <(find "$PLUGIN_PATH" -name "*.md" -type f -print0 2>/dev/null)

    exit $errors
}

main
