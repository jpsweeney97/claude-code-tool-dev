#!/bin/bash
# check-structure.sh - Layer 2: Structure validation for plugin files
#
# Validates plugin structure against audit specification rules.
# Checks required fields and organization, NOT syntax (Layer 1 handles that).
#
# Usage: check-structure.sh <plugin-path>
# Output: JSON objects (one per line) for each issue found
# Exit: Count of errors (0 = success)
#
# Dependencies: jq (JSON), yq (YAML)
#
# Rules checked:
#   S000: Meta/infrastructure errors (missing plugin path, missing dependencies)
#   S001: Plugin name required in manifest
#   S002: Plugin name should be kebab-case
#   S003: Version field recommended
#   SK001: Skill name required in frontmatter
#   SK002: Skill description required in frontmatter
#   A001: Agent description required in frontmatter
#   A002: Agent tools required in frontmatter
#   H001: Hook events must be valid

set -uo pipefail

PLUGIN_PATH="${1:-.}"
PLUGIN_PATH="${PLUGIN_PATH%/}"  # Remove trailing slash

# Resolve to absolute path for consistent relative path calculation
if [[ "$PLUGIN_PATH" != /* ]]; then
    PLUGIN_PATH="$(cd "$PLUGIN_PATH" 2>/dev/null && pwd)"
fi

if [[ ! -d "$PLUGIN_PATH" ]]; then
    echo '{"file": ".", "line": 0, "rule": "S000", "error": "Plugin path does not exist or is not a directory", "severity": "CRITICAL"}'
    exit 1
fi

errors=0

# Valid hook events per audit-spec.yaml
VALID_HOOK_EVENTS="PreToolUse PostToolUse Stop SubagentStop SessionStart SessionEnd UserPromptSubmit PreCompact Notification"

# Emit a structured error
emit_error() {
    local file="$1"
    local line="$2"
    local rule="$3"
    local error="$4"
    local severity="${5:-CRITICAL}"

    # Make path relative to plugin root
    local rel_file="${file#"$PLUGIN_PATH"/}"

    # Escape special characters in error message for JSON
    local escaped_error
    escaped_error=$(printf '%s' "$error" | jq -Rs '.')

    echo "{\"file\": \"$rel_file\", \"line\": $line, \"rule\": \"$rule\", \"error\": $escaped_error, \"severity\": \"$severity\"}"
    ((errors++))
}

# Check if required tools are available
check_dependencies() {
    local missing=0

    if ! command -v jq &>/dev/null; then
        emit_error "." 0 "S000" "Required dependency 'jq' not found"
        ((missing++))
    fi

    if ! command -v yq &>/dev/null; then
        emit_error "." 0 "S000" "Required dependency 'yq' not found"
        ((missing++))
    fi

    return $missing
}

# Extract YAML frontmatter from a markdown file
# Returns the frontmatter as a string, or empty if no frontmatter
extract_frontmatter() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    # Check if file starts with ---
    local first_line
    first_line=$(head -1 "$file")
    if [[ "$first_line" != "---" ]]; then
        return 0
    fi

    # Extract content between first and second ---
    awk '
        /^---$/ {
            if (count == 0) { count = 1; next }
            if (count == 1) { exit }
        }
        count == 1 { print }
    ' "$file"
}

# Get line number where frontmatter ends (after closing ---)
get_frontmatter_end_line() {
    local file="$1"

    awk '
        /^---$/ {
            count++
            if (count == 2) { print NR; exit }
        }
    ' "$file"
}

# Validate manifest (plugin.json)
# Rules: S001, S002, S003
validate_manifest() {
    local manifest="$PLUGIN_PATH/.claude-plugin/plugin.json"

    if [[ ! -f "$manifest" ]]; then
        emit_error ".claude-plugin/plugin.json" 0 "S001" "Plugin manifest does not exist"
        return 1
    fi

    # S001: Plugin name required
    local name
    name=$(jq -r '.name // empty' "$manifest" 2>/dev/null)
    if [[ -z "$name" ]]; then
        emit_error ".claude-plugin/plugin.json" 1 "S001" "Plugin name is required in manifest"
    else
        # S002: Name should be kebab-case
        if ! echo "$name" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'; then
            # Find line number of name field
            local line
            line=$(grep -n '"name"' "$manifest" | head -1 | cut -d: -f1)
            emit_error ".claude-plugin/plugin.json" "${line:-1}" "S002" "Plugin name '$name' should be kebab-case (lowercase with hyphens)"
        fi
    fi

    # S003: Version field recommended
    local version
    version=$(jq -r '.version // empty' "$manifest" 2>/dev/null)
    if [[ -z "$version" ]]; then
        emit_error ".claude-plugin/plugin.json" 1 "S003" "Version field is recommended in manifest" "WARNING"
    fi

    return 0
}

# Validate a single skill (SKILL.md)
# Rules: SK001, SK002
validate_skill() {
    local skill_file="$1"

    if [[ ! -f "$skill_file" ]]; then
        return 0
    fi

    local frontmatter
    frontmatter=$(extract_frontmatter "$skill_file")

    if [[ -z "$frontmatter" ]]; then
        emit_error "$skill_file" 1 "SK001" "Skill requires YAML frontmatter with 'name' field"
        emit_error "$skill_file" 1 "SK002" "Skill requires YAML frontmatter with 'description' field"
        return 1
    fi

    # SK001: Skill name required
    # Try to parse - if yq fails, skip (Layer 1 handles YAML syntax errors)
    local name
    if ! name=$(echo "$frontmatter" | yq -r '.name // ""' 2>/dev/null); then
        return 0  # YAML parse error - defer to Layer 1
    fi
    if [[ -z "$name" ]]; then
        emit_error "$skill_file" 2 "SK001" "Skill 'name' is required in frontmatter"
    fi

    # SK002: Skill description required
    local description
    if ! description=$(echo "$frontmatter" | yq -r '.description // ""' 2>/dev/null); then
        return 0  # YAML parse error - defer to Layer 1
    fi
    if [[ -z "$description" ]]; then
        emit_error "$skill_file" 2 "SK002" "Skill 'description' is required in frontmatter"
    fi

    return 0
}

# Validate all skills
validate_skills() {
    if [[ ! -d "$PLUGIN_PATH/skills" ]]; then
        return 0
    fi

    while IFS= read -r -d '' skill_dir; do
        local skill_file="$skill_dir/SKILL.md"
        if [[ -f "$skill_file" ]]; then
            validate_skill "$skill_file"
        fi
    done < <(find "$PLUGIN_PATH/skills" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
}

# Validate a single agent
# Rules: A001, A002
validate_agent() {
    local agent_file="$1"

    if [[ ! -f "$agent_file" ]]; then
        return 0
    fi

    local frontmatter
    frontmatter=$(extract_frontmatter "$agent_file")

    if [[ -z "$frontmatter" ]]; then
        emit_error "$agent_file" 1 "A001" "Agent requires YAML frontmatter with 'description' field"
        emit_error "$agent_file" 1 "A002" "Agent requires YAML frontmatter with 'tools' field"
        return 1
    fi

    # A001: Agent description required
    # Try to parse - if yq fails, skip (Layer 1 handles YAML syntax errors)
    local description
    if ! description=$(echo "$frontmatter" | yq -r '.description // ""' 2>/dev/null); then
        return 0  # YAML parse error - defer to Layer 1
    fi
    if [[ -z "$description" ]]; then
        emit_error "$agent_file" 2 "A001" "Agent 'description' is required in frontmatter"
    fi

    # A002: Agent tools required
    local tools
    if ! tools=$(echo "$frontmatter" | yq -r '.tools // ""' 2>/dev/null); then
        return 0  # YAML parse error - defer to Layer 1
    fi
    if [[ -z "$tools" || "$tools" == "null" ]]; then
        emit_error "$agent_file" 2 "A002" "Agent 'tools' is required in frontmatter"
    fi

    return 0
}

# Validate all agents
validate_agents() {
    if [[ ! -d "$PLUGIN_PATH/agents" ]]; then
        return 0
    fi

    while IFS= read -r -d '' agent_file; do
        validate_agent "$agent_file"
    done < <(find "$PLUGIN_PATH/agents" -maxdepth 1 -name "*.md" -type f -print0 2>/dev/null)
}

# Validate hooks.json
# Rules: H001
validate_hooks() {
    local hooks_file="$PLUGIN_PATH/hooks/hooks.json"

    if [[ ! -f "$hooks_file" ]]; then
        return 0
    fi

    # Read all events from the hooks file
    local events
    events=$(jq -r 'keys[]' "$hooks_file" 2>/dev/null)

    if [[ -z "$events" ]]; then
        return 0
    fi

    # Check each event name
    while IFS= read -r event; do
        local is_valid=false
        for valid_event in $VALID_HOOK_EVENTS; do
            if [[ "$event" == "$valid_event" ]]; then
                is_valid=true
                break
            fi
        done

        if [[ "$is_valid" == "false" ]]; then
            # Find line number of the invalid event
            local line
            line=$(grep -n "\"$event\"" "$hooks_file" | head -1 | cut -d: -f1)
            emit_error "hooks/hooks.json" "${line:-1}" "H001" "Invalid hook event '$event'. Valid events: $VALID_HOOK_EVENTS"
        fi
    done <<< "$events"
}

# Main validation logic
main() {
    # Check dependencies first
    if ! check_dependencies; then
        exit 1
    fi

    # Run all structure validations
    validate_manifest
    validate_skills
    validate_agents
    validate_hooks

    exit $errors
}

main
