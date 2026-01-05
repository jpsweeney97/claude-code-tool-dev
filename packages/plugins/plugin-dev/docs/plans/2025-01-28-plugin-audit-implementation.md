# Plugin Audit Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate false positives in plugin-audit through evidence-backed rules and context analysis.

**Architecture:** Five-layer pipeline (Syntax → Structure → Context → Quality → Cross-component) with specification-driven rules, context filtering for examples/security blocks, and lean SKILL.md (~400 words) with heavy reference.

**Tech Stack:** Bash scripts (jq, yq), YAML spec, Claude for semantic analysis

**Design Reference:** `docs/plans/2025-01-28-plugin-audit-redesign.md`

---

## Task 1: Create Directory Structure

**Files:**
- Create: `skills/plugin-audit/specification/` (directory)

**Step 1: Create specification directory**

```bash
mkdir -p skills/plugin-audit/specification
```

**Step 2: Verify directory exists**

Run: `ls -la skills/plugin-audit/`
Expected: `specification/` directory listed

**Step 3: Commit**

```bash
git add skills/plugin-audit/specification
git commit -m "chore: add specification directory for audit rules"
```

---

## Task 2: Create Specification Schema

**Files:**
- Create: `skills/plugin-audit/specification/audit-spec.yaml`

**Step 1: Write the specification file**

```yaml
# Plugin Audit Specification
# All rules with full provenance for traceability
#
# Structure:
#   - meta: spec metadata and versioning
#   - component_types: rules per component (command, skill, agent, hook, mcp)
#   - context_patterns: example/security detection patterns
#
# Every rule has:
#   - required: boolean
#   - source: official documentation reference
#   - evidence: quote from docs
#   - rule_derivation: reasoning from evidence to rule

meta:
  version: "1.0.0"
  claude_code_docs_version: "2025-01"
  last_verified: "2025-01-28"
  verification_notes: |
    Rules verified against official Claude Code documentation.
    Run --verify-spec to check if documentation has changed.

# =============================================================================
# COMPONENT TYPE DEFINITIONS
# =============================================================================

component_types:

  # ---------------------------------------------------------------------------
  # COMMANDS (commands/*.md)
  # ---------------------------------------------------------------------------
  command:
    discovery:
      pattern: "commands/**/*.md"
      location: "Plugin root commands/ directory"

    frontmatter:
      fields:
        name:
          required: false
          deprecated: true
          source:
            doc_section: "Slash commands - Plugin Commands"
            url: "https://docs.anthropic.com/en/docs/claude-code/slash-commands#plugin-commands"
          evidence:
            quote: "Command files are named using the desired command name"
            retrieved: "2025-01-28"
          rule_derivation: |
            Documentation states command name comes from filename.
            Therefore 'name' frontmatter field is NOT required.
            If present, filename takes precedence anyway.

        description:
          required: false
          recommended: true
          source:
            doc_section: "Slash commands - Plugin Commands"
            url: "https://docs.anthropic.com/en/docs/claude-code/slash-commands#plugin-commands"
          evidence:
            quote: "The frontmatter block is optional, but if included can specify: description"
            retrieved: "2025-01-28"
          rule_derivation: |
            Documentation says frontmatter is optional.
            Description is recommended for discoverability but not required.

        argument-hint:
          required: false
          source:
            doc_section: "Slash commands - Plugin Commands"
            url: "https://docs.anthropic.com/en/docs/claude-code/slash-commands#plugin-commands"
          evidence:
            quote: "argument-hint: A hint shown to users about expected arguments"
            retrieved: "2025-01-28"
          rule_derivation: |
            Optional field for UX improvement.

        allowed-tools:
          required: false
          recommended: true
          source:
            doc_section: "Slash commands - Plugin Commands"
            url: "https://docs.anthropic.com/en/docs/claude-code/slash-commands#plugin-commands"
          evidence:
            quote: "allowed-tools: Tools the command can use"
            retrieved: "2025-01-28"
          rule_derivation: |
            Optional but recommended for least-privilege.
            If omitted, command can use all available tools.

  # ---------------------------------------------------------------------------
  # SKILLS (skills/*/SKILL.md)
  # ---------------------------------------------------------------------------
  skill:
    discovery:
      pattern: "skills/*/SKILL.md"
      location: "Plugin root skills/ directory, one SKILL.md per skill subdirectory"

    frontmatter:
      fields:
        name:
          required: true
          source:
            doc_section: "Skills - Plugin Skills"
            url: "https://docs.anthropic.com/en/docs/claude-code/skills"
          evidence:
            quote: "name: The skill name"
            retrieved: "2025-01-28"
          rule_derivation: |
            Skills require a name for identification in skill listings.

        description:
          required: true
          source:
            doc_section: "Skills - Plugin Skills"
            url: "https://docs.anthropic.com/en/docs/claude-code/skills"
          evidence:
            quote: "description: When Claude should use this skill"
            retrieved: "2025-01-28"
          rule_derivation: |
            Description is required for Claude to know when to load the skill.

    content:
      max_words:
        value: 3000
        recommended: 1500
        source:
            doc_section: "Skills - Best Practices"
            url: "https://docs.anthropic.com/en/docs/claude-code/skills"
        evidence:
          quote: "Keep skills focused - around 1500-2000 words is ideal"
          retrieved: "2025-01-28"
        rule_derivation: |
          Large skills consume context. 1500-2000 words is optimal.
          Over 3000 words should be split into references.

  # ---------------------------------------------------------------------------
  # AGENTS (agents/*.md)
  # ---------------------------------------------------------------------------
  agent:
    discovery:
      pattern: "agents/*.md"
      location: "Plugin root agents/ directory"

    frontmatter:
      fields:
        name:
          required: false
          source:
            doc_section: "Agents - Plugin Agents"
            url: "https://docs.anthropic.com/en/docs/claude-code/agents"
          evidence:
            quote: "name: Optional display name for the agent"
            retrieved: "2025-01-28"
          rule_derivation: |
            Name is optional. If omitted, derived from filename.

        description:
          required: true
          source:
            doc_section: "Agents - Plugin Agents"
            url: "https://docs.anthropic.com/en/docs/claude-code/agents"
          evidence:
            quote: "description: When to trigger this agent, with examples"
            retrieved: "2025-01-28"
          rule_derivation: |
            Description is required for Claude to know when to use the agent.

        tools:
          required: true
          source:
            doc_section: "Agents - Plugin Agents"
            url: "https://docs.anthropic.com/en/docs/claude-code/agents"
          evidence:
            quote: "tools: Array of tools the agent can use"
            retrieved: "2025-01-28"
          rule_derivation: |
            Tools array is required - agents need explicit tool access.

  # ---------------------------------------------------------------------------
  # HOOKS (hooks/hooks.json)
  # ---------------------------------------------------------------------------
  hook:
    discovery:
      pattern: "hooks/hooks.json"
      location: "Plugin root hooks/ directory"

    schema:
      valid_events:
        - PreToolUse
        - PostToolUse
        - Stop
        - SubagentStop
        - SessionStart
        - SessionEnd
        - UserPromptSubmit
        - PreCompact
        - Notification
      source:
        doc_section: "Hooks - Event Types"
        url: "https://docs.anthropic.com/en/docs/claude-code/hooks"
      evidence:
        quote: "Hook events: PreToolUse, PostToolUse, Stop, SubagentStop..."
        retrieved: "2025-01-28"

    fields:
      timeout:
        required: false
        default: 60000
        recommended: 30000
        source:
          doc_section: "Hooks - Configuration"
          url: "https://docs.anthropic.com/en/docs/claude-code/hooks"
        evidence:
          quote: "timeout: Maximum execution time in milliseconds (default: 60000)"
          retrieved: "2025-01-28"
        rule_derivation: |
          Timeout is optional with 60s default.
          Recommended to set explicitly for predictable behavior.

  # ---------------------------------------------------------------------------
  # MCP (.mcp.json in plugin root)
  # ---------------------------------------------------------------------------
  mcp:
    discovery:
      pattern: ".mcp.json"
      location: "Plugin root directory"

    fields:
      command:
        required: true
        condition: "for stdio servers"
        source:
          doc_section: "MCP - Server Configuration"
          url: "https://docs.anthropic.com/en/docs/claude-code/mcp"
        evidence:
          quote: "command: The command to start the MCP server"
          retrieved: "2025-01-28"
        rule_derivation: |
          stdio servers require a command to launch.

# =============================================================================
# PATH AND SECURITY RULES
# =============================================================================

security:
  paths:
    portable_variable: "$CLAUDE_PLUGIN_ROOT"
    source:
      doc_section: "Plugins - Portable Paths"
      url: "https://docs.anthropic.com/en/docs/claude-code/plugins"
    evidence:
      quote: "$CLAUDE_PLUGIN_ROOT is expanded to the plugin's root directory"
      retrieved: "2025-01-28"
    rule_derivation: |
      Plugins must use $CLAUDE_PLUGIN_ROOT for portability.
      Hardcoded absolute paths break when plugin is moved.

    # CRITICAL: These patterns may appear in DENY blocks, not vulnerabilities
    system_paths_note: |
      Paths like /etc/, /sys/, ~/.ssh/ may appear in security hooks
      that BLOCK access rather than ACCESS files. Context analysis required.

# =============================================================================
# CONTEXT ANALYSIS PATTERNS (Layer 3)
# =============================================================================

context_patterns:

  # Patterns that indicate content is an EXAMPLE, not real
  example_indicators:
    explicit_markers:
      - pattern: '<!-- audit:example-section -->'
        confidence: 1.0
        scope: section
        note: "Explicit audit directive"

    section_headers:
      - pattern: '^#{1,3}\s+Examples?$'
        confidence: 0.95
        scope: section
      - pattern: '^#{1,3}\s+Usage Examples?$'
        confidence: 0.95
        scope: section

    inline_markers:
      - pattern: '^\s*-\s*\*\*Example\*\*:'
        confidence: 0.95
        scope: line
      - pattern: '\(e\.g\.,?\s'
        confidence: 0.9
        scope: line
      - pattern: 'for example:'
        confidence: 0.9
        scope: line

    code_blocks:
      - pattern: '```'
        confidence: 0.9
        scope: block
        applies_to: [file_references, paths]
        note: "File paths in code blocks are usually examples"

  # Patterns that indicate SECURITY FEATURE, not vulnerability
  security_deny_patterns:
    hook_output:
      - pattern: 'permissionDecision.*deny'
        confidence: 0.95
        note: "Hook is DENYING access, not granting"
      - pattern: '"decision":\s*"block"'
        confidence: 0.95
      - pattern: '"allow":\s*false'
        confidence: 0.95

    exit_codes:
      - pattern: 'exit [12]\s*$'
        confidence: 0.9
        context: conditional
        note: "exit 1/2 in conditional = blocking, not failing"

    deny_lists:
      - pattern: 'deny.*list|blocklist|blacklist'
        confidence: 0.85
        note: "Part of deny list definition"

# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

confidence_thresholds:
  critical:
    report_confirmed: 0.7
    needs_llm_verification: 0.7
  warning:
    report_confirmed: 0.7
    report_needs_review: 0.5
    skip: 0.5
  info:
    report: 0.7
    skip: 0.7
```

**Step 2: Validate YAML syntax**

Run: `yq '.' skills/plugin-audit/specification/audit-spec.yaml > /dev/null && echo "VALID"`
Expected: `VALID`

**Step 3: Commit**

```bash
git add skills/plugin-audit/specification/audit-spec.yaml
git commit -m "feat: add audit specification with evidence-backed rules"
```

---

## Task 3: Create Syntax Validation Script

**Files:**
- Modify: `skills/plugin-audit/scripts/validate-json.sh` → rename to `check-syntax.sh`
- Remove: `skills/plugin-audit/scripts/validate-yaml-frontmatter.sh` (merge into check-syntax.sh)

**Step 1: Write the unified syntax validation script**

Create `skills/plugin-audit/scripts/check-syntax.sh`:

```bash
#!/usr/bin/env bash
#
# check-syntax.sh - Layer 1: Syntax validation for plugin files
#
# Validates:
#   - JSON files (plugin.json, hooks.json, .mcp.json)
#   - YAML frontmatter in markdown files
#
# Usage: check-syntax.sh <plugin-path>
# Exit: 0 if all valid, 1 if errors found
#
# Output format (one JSON object per issue):
#   {"file": "path", "line": N, "error": "message", "severity": "CRITICAL"}

set -euo pipefail

PLUGIN_PATH="${1:-.}"
ERRORS=0

# Validate JSON file
validate_json() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"

    if ! jq empty "$file" 2>/dev/null; then
        local error_msg
        error_msg=$(jq empty "$file" 2>&1 || true)
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"error\": \"Invalid JSON: $error_msg\", \"severity\": \"CRITICAL\"}"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Validate YAML frontmatter in markdown
validate_yaml_frontmatter() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"

    # Check if file starts with ---
    if ! head -1 "$file" | grep -q '^---$'; then
        # No frontmatter is valid (optional)
        return 0
    fi

    # Extract frontmatter between first two ---
    local frontmatter
    frontmatter=$(sed -n '1,/^---$/p' "$file" | tail -n +2 | head -n -1)

    if [ -z "$frontmatter" ]; then
        return 0
    fi

    # Validate YAML
    if ! echo "$frontmatter" | yq '.' > /dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$frontmatter" | yq '.' 2>&1 || true)
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"error\": \"Invalid YAML frontmatter: $error_msg\", \"severity\": \"CRITICAL\"}"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Main

# Check required files exist
if [ ! -d "$PLUGIN_PATH/.claude-plugin" ]; then
    echo "{\"file\": \".claude-plugin/\", \"line\": 0, \"error\": \"Missing .claude-plugin directory\", \"severity\": \"CRITICAL\"}"
    exit 1
fi

if [ ! -f "$PLUGIN_PATH/.claude-plugin/plugin.json" ]; then
    echo "{\"file\": \".claude-plugin/plugin.json\", \"line\": 0, \"error\": \"Missing plugin.json\", \"severity\": \"CRITICAL\"}"
    exit 1
fi

# Validate plugin.json
validate_json "$PLUGIN_PATH/.claude-plugin/plugin.json"

# Validate hooks.json if exists
if [ -f "$PLUGIN_PATH/hooks/hooks.json" ]; then
    validate_json "$PLUGIN_PATH/hooks/hooks.json"
fi

# Validate .mcp.json if exists
if [ -f "$PLUGIN_PATH/.mcp.json" ]; then
    validate_json "$PLUGIN_PATH/.mcp.json"
fi

# Validate markdown frontmatter
while IFS= read -r -d '' file; do
    validate_yaml_frontmatter "$file"
done < <(find "$PLUGIN_PATH" -name "*.md" -type f -print0 2>/dev/null)

exit $ERRORS
```

**Step 2: Make script executable and test**

```bash
chmod +x skills/plugin-audit/scripts/check-syntax.sh
```

Run: `bash skills/plugin-audit/scripts/check-syntax.sh .`
Expected: No output (all syntax valid) or JSON error objects

**Step 3: Remove old scripts**

```bash
rm skills/plugin-audit/scripts/validate-json.sh
rm skills/plugin-audit/scripts/validate-yaml-frontmatter.sh
```

**Step 4: Commit**

```bash
git add skills/plugin-audit/scripts/
git commit -m "refactor: unify syntax validation into check-syntax.sh"
```

---

## Task 4: Create Structure Validation Script

**Files:**
- Create: `skills/plugin-audit/scripts/check-structure.sh`

**Step 1: Write structure validation script**

```bash
#!/usr/bin/env bash
#
# check-structure.sh - Layer 2: Structure validation using spec
#
# Validates:
#   - Required fields per component type
#   - File naming conventions
#   - Directory organization
#
# Usage: check-structure.sh <plugin-path> [--spec <spec-path>]
# Exit: 0 if all valid, 1+ for number of issues
#
# Output format (one JSON object per issue):
#   {"file": "path", "line": N, "rule": "S001", "error": "msg", "severity": "WARNING"}

set -euo pipefail

PLUGIN_PATH="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_PATH="${SCRIPT_DIR}/../specification/audit-spec.yaml"
ISSUES=0

# Helper: Get field from YAML file frontmatter
get_frontmatter_field() {
    local file="$1"
    local field="$2"
    sed -n '1,/^---$/p' "$file" | tail -n +2 | head -n -1 | yq -r ".$field // empty"
}

# Helper: Check if file uses kebab-case
is_kebab_case() {
    local name="$1"
    [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

# S001: Plugin name in manifest
check_manifest_name() {
    local manifest="$PLUGIN_PATH/.claude-plugin/plugin.json"
    local name
    name=$(jq -r '.name // empty' "$manifest")

    if [ -z "$name" ]; then
        echo "{\"file\": \".claude-plugin/plugin.json\", \"line\": 1, \"rule\": \"S001\", \"error\": \"Missing required 'name' field in manifest\", \"severity\": \"CRITICAL\"}"
        ((ISSUES++))
    elif ! is_kebab_case "$name"; then
        echo "{\"file\": \".claude-plugin/plugin.json\", \"line\": 1, \"rule\": \"S002\", \"error\": \"Plugin name should be kebab-case: $name\", \"severity\": \"WARNING\"}"
        ((ISSUES++))
    fi
}

# S003: Version field (recommended)
check_manifest_version() {
    local manifest="$PLUGIN_PATH/.claude-plugin/plugin.json"
    local version
    version=$(jq -r '.version // empty' "$manifest")

    if [ -z "$version" ]; then
        echo "{\"file\": \".claude-plugin/plugin.json\", \"line\": 1, \"rule\": \"S003\", \"error\": \"Missing recommended 'version' field\", \"severity\": \"INFO\"}"
        ((ISSUES++))
    fi
}

# SK001: Skill has name field
check_skill_name() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"
    local name
    name=$(get_frontmatter_field "$file" "name")

    if [ -z "$name" ]; then
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"rule\": \"SK001\", \"error\": \"Missing required 'name' field in skill\", \"severity\": \"CRITICAL\"}"
        ((ISSUES++))
    fi
}

# SK002: Skill has description field
check_skill_description() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"
    local desc
    desc=$(get_frontmatter_field "$file" "description")

    if [ -z "$desc" ]; then
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"rule\": \"SK002\", \"error\": \"Missing required 'description' field in skill\", \"severity\": \"CRITICAL\"}"
        ((ISSUES++))
    fi
}

# A001: Agent has description
check_agent_description() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"
    local desc
    desc=$(get_frontmatter_field "$file" "description")

    if [ -z "$desc" ]; then
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"rule\": \"A001\", \"error\": \"Missing required 'description' field in agent\", \"severity\": \"CRITICAL\"}"
        ((ISSUES++))
    fi
}

# A002: Agent has tools
check_agent_tools() {
    local file="$1"
    local rel_path="${file#$PLUGIN_PATH/}"
    local tools
    tools=$(get_frontmatter_field "$file" "tools")

    if [ -z "$tools" ]; then
        echo "{\"file\": \"$rel_path\", \"line\": 1, \"rule\": \"A002\", \"error\": \"Missing required 'tools' field in agent\", \"severity\": \"CRITICAL\"}"
        ((ISSUES++))
    fi
}

# H001: Hook events are valid
check_hook_events() {
    local hooks_file="$PLUGIN_PATH/hooks/hooks.json"
    [ ! -f "$hooks_file" ] && return 0

    local valid_events="PreToolUse PostToolUse Stop SubagentStop SessionStart SessionEnd UserPromptSubmit PreCompact Notification"

    # Extract all event names from hooks
    local events
    events=$(jq -r 'keys[]' "$hooks_file" 2>/dev/null || echo "")

    for event in $events; do
        if ! echo "$valid_events" | grep -qw "$event"; then
            echo "{\"file\": \"hooks/hooks.json\", \"line\": 1, \"rule\": \"H001\", \"error\": \"Invalid hook event: $event\", \"severity\": \"CRITICAL\"}"
            ((ISSUES++))
        fi
    done
}

# Main validation

# Check manifest
check_manifest_name
check_manifest_version

# Check skills
while IFS= read -r -d '' file; do
    check_skill_name "$file"
    check_skill_description "$file"
done < <(find "$PLUGIN_PATH/skills" -name "SKILL.md" -type f -print0 2>/dev/null)

# Check agents
while IFS= read -r -d '' file; do
    check_agent_description "$file"
    check_agent_tools "$file"
done < <(find "$PLUGIN_PATH/agents" -name "*.md" -type f -print0 2>/dev/null)

# Check hooks
check_hook_events

exit $ISSUES
```

**Step 2: Make executable and test**

```bash
chmod +x skills/plugin-audit/scripts/check-structure.sh
```

Run: `bash skills/plugin-audit/scripts/check-structure.sh .`
Expected: JSON output for any structure issues found

**Step 3: Commit**

```bash
git add skills/plugin-audit/scripts/check-structure.sh
git commit -m "feat: add check-structure.sh for Layer 2 validation"
```

---

## Task 5: Create Context Patterns Reference

**Files:**
- Create: `skills/plugin-audit/references/context-patterns.md`
- Remove: All existing reference files (will be consolidated into context-patterns.md and rule-reference.md)

**Step 1: Write context-patterns.md**

```markdown
# Context Analysis Patterns

Reference for Layer 3 context analysis. These patterns help distinguish real issues from false positives.

## Purpose

Layer 2 (structure validation) identifies potential issues. Layer 3 determines if those issues are real by analyzing context. This prevents false positives like:

- Example paths flagged as missing files
- Security deny-blocks flagged as vulnerabilities
- Teaching code flagged as real implementation

## Example Detection

### Explicit Markers (Confidence: 1.0)

Authors can mark sections as examples:

```markdown
<!-- audit:example-section -->
The following paths are examples only:
- `/etc/config.yaml`
- `~/.ssh/id_rsa`
<!-- audit:end-example-section -->
```

**Action:** Skip all issues within marked section.

### Section Headers (Confidence: 0.95)

Common example section patterns:

```markdown
## Examples
### Usage Examples
## Example Configuration
```

**Pattern:** `^#{1,3}\s+Examples?$` or `^#{1,3}\s+Usage Examples?$`
**Action:** Issues from content under these headers are likely examples.

### Inline Markers (Confidence: 0.9)

Inline example indicators:

- `**Example:**` prefix
- `(e.g., /path/to/file)`
- `for example:`

**Action:** Specific line is an example, not the whole section.

### Code Blocks (Confidence: 0.9)

File paths inside code blocks are usually examples:

```bash
# This path won't be flagged as missing:
cat /etc/nginx/nginx.conf
```

**Pattern:** Content between ``` markers
**Action:** Reduce confidence for file-existence checks.

## Security Context Detection

### Hook Deny Outputs (Confidence: 0.95)

Patterns indicating a hook is BLOCKING access (security feature):

```json
{"permissionDecision": "deny", "message": "Blocked access"}
```

```bash
if [[ "$path" == "/etc/"* ]]; then
    echo '{"permissionDecision": "deny"}' >&2
    exit 2
fi
```

**Key patterns:**
- `permissionDecision.*deny`
- `"decision": "block"`
- `"allow": false`

**Action:** Path is being BLOCKED, not accessed. Not a vulnerability.

### Exit Codes in Conditionals (Confidence: 0.9)

```bash
if [[ dangerous_condition ]]; then
    exit 1  # Blocking
fi
```

**Pattern:** `exit [12]` after conditional check
**Action:** Script is blocking dangerous operations.

### Deny List Definitions (Confidence: 0.85)

```python
BLOCKED_PATHS = ["/etc/", "/sys/", "~/.ssh/"]
```

**Pattern:** Variable names like `deny`, `block`, `blacklist`
**Action:** These paths are being blocked, not accessed.

## Confidence Scoring

### Thresholds by Severity

| Severity | Confidence | Action |
|----------|------------|--------|
| CRITICAL | ≥ 0.7 | Report as confirmed |
| CRITICAL | < 0.7 | Request LLM verification |
| WARNING | ≥ 0.7 | Report as confirmed |
| WARNING | 0.5-0.7 | Report as "needs review" |
| WARNING | < 0.5 | Skip to avoid false positive |
| INFO | ≥ 0.7 | Report as suggestion |
| INFO | < 0.7 | Skip |

### Multiple Pattern Matches

When multiple patterns match, use highest confidence:
- Explicit marker (1.0) + code block (0.9) → Use 1.0
- Section header (0.95) + inline marker (0.9) → Use 0.95

### LLM Verification

For CRITICAL issues below 0.7 confidence, request verification:

```markdown
## Context Analysis Request

**Issue:** [SEC001] Hardcoded system path detected
**File:** hooks/security.sh:47
**Match:** `/etc/`

**Context (±5 lines):**
[Show surrounding code]

**Question:** Is this path being ACCESSED (risk) or BLOCKED (security feature)?

**Respond:** APPLY | SKIP | UNCERTAIN
```

## Implementation Notes

1. **Run context analysis AFTER structure validation** - Only analyze issues that passed Layer 2
2. **Log skipped issues** - Include in report with reasoning
3. **Don't over-filter** - When uncertain, prefer reporting as "needs review" over silent skip
4. **Trust explicit markers** - `<!-- audit:example-section -->` is authoritative
```

**Step 2: Remove old reference files**

```bash
rm skills/plugin-audit/references/structure-rules.md
rm skills/plugin-audit/references/skill-rules.md
rm skills/plugin-audit/references/command-rules.md
rm skills/plugin-audit/references/agent-rules.md
rm skills/plugin-audit/references/hook-rules.md
rm skills/plugin-audit/references/mcp-rules.md
rm skills/plugin-audit/references/security-rules.md
rm skills/plugin-audit/references/cross-cutting-rules.md
```

**Step 3: Commit**

```bash
git add skills/plugin-audit/references/
git commit -m "refactor: consolidate references into context-patterns.md"
```

---

## Task 6: Create Rule Reference

**Files:**
- Create: `skills/plugin-audit/references/rule-reference.md`

**Step 1: Write rule-reference.md**

```markdown
# Audit Rule Reference

Complete reference of all validation rules with IDs, severity, and evidence.

## Rule ID Format

- `S###` - Structure rules (manifest, directories)
- `SK###` - Skill rules
- `C###` - Command rules
- `A###` - Agent rules
- `H###` - Hook rules
- `M###` - MCP rules
- `SEC###` - Security rules
- `X###` - Cross-component rules

## Structure Rules (S)

### S001: Plugin name required (CRITICAL)

**Check:** `.claude-plugin/plugin.json` has `name` field
**Evidence:** Plugin manifest requires name for identification
**Fix:** Add `"name": "my-plugin"` to plugin.json

### S002: Plugin name kebab-case (WARNING)

**Check:** Plugin name follows kebab-case pattern
**Evidence:** Convention for consistency across plugins
**Fix:** Rename to kebab-case (e.g., `my-plugin` not `myPlugin`)

### S003: Version field recommended (INFO)

**Check:** `.claude-plugin/plugin.json` has `version` field
**Evidence:** Version helps track plugin updates
**Fix:** Add `"version": "0.1.0"` to plugin.json

## Skill Rules (SK)

### SK001: Skill name required (CRITICAL)

**Check:** `skills/*/SKILL.md` frontmatter has `name` field
**Evidence:** Skills require name for identification in listings
**Fix:** Add `name: My Skill` to frontmatter

### SK002: Skill description required (CRITICAL)

**Check:** `skills/*/SKILL.md` frontmatter has `description` field
**Evidence:** Description tells Claude when to load the skill
**Fix:** Add description with trigger phrases

### SK003: Description uses third-person (WARNING)

**Check:** Description doesn't use "you" or first-person
**Evidence:** Best practice from skill-creator methodology
**Fix:** Use "This skill should be used when..." format

### SK004: Description has trigger phrases (WARNING)

**Check:** Description contains quoted trigger phrases
**Evidence:** Specific phrases improve skill loading reliability
**Fix:** Add phrases like "create a hook", "validate plugin"

### SK005: Skill body word count (WARNING)

**Check:** SKILL.md body is under 3000 words
**Recommended:** 1500-2000 words
**Evidence:** Large skills consume context inefficiently
**Fix:** Extract detailed content to references/

## Command Rules (C)

### C001: Command name NOT required (INFO)

**Check:** Commands MAY have `name` field but it's optional
**Evidence:** "Command name is derived from filename" - official docs
**Note:** This rule prevents false positives from old assumption that name was required

### C002: Description recommended (INFO)

**Check:** `commands/*.md` has `description` in frontmatter
**Evidence:** Description improves command discoverability
**Fix:** Add `description: What this command does`

## Agent Rules (A)

### A001: Agent description required (CRITICAL)

**Check:** `agents/*.md` frontmatter has `description` field
**Evidence:** Description tells Claude when to trigger agent
**Fix:** Add description with example blocks

### A002: Agent tools required (CRITICAL)

**Check:** `agents/*.md` frontmatter has `tools` array
**Evidence:** Agents need explicit tool access
**Fix:** Add `tools: ["Read", "Glob", "Grep"]`

### A003: Agent has example blocks (WARNING)

**Check:** Description contains `<example>` blocks
**Evidence:** Examples improve agent triggering reliability
**Fix:** Add concrete usage examples

## Hook Rules (H)

### H001: Valid hook events (CRITICAL)

**Check:** `hooks/hooks.json` uses valid event names
**Valid events:** PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification
**Fix:** Use exact event names from documentation

### H002: Timeout recommended (INFO)

**Check:** Hook entries have `timeout` field
**Evidence:** Explicit timeout prevents hanging hooks
**Fix:** Add `"timeout": 30000`

### H003: Script paths portable (WARNING)

**Check:** Hook script paths use `$CLAUDE_PLUGIN_ROOT`
**Evidence:** Hardcoded paths break portability
**Fix:** Use `$CLAUDE_PLUGIN_ROOT/hooks/script.sh`

## Security Rules (SEC)

### SEC001: No hardcoded absolute paths (WARNING)

**Check:** Config files don't contain hardcoded paths like `/Users/...`
**Evidence:** Absolute paths break when plugin moves
**Fix:** Use `$CLAUDE_PLUGIN_ROOT` or `$HOME`
**Context:** May be false positive if path is in deny-block

### SEC002: No credentials in files (CRITICAL)

**Check:** No API keys, tokens, passwords in committed files
**Evidence:** Security best practice
**Fix:** Use environment variables

### SEC003: Tilde paths in JSON (WARNING)

**Check:** JSON files don't use `~/` (shell expansion doesn't work)
**Evidence:** `~` doesn't expand in JSON contexts
**Fix:** Use `$HOME` or `$CLAUDE_PLUGIN_ROOT`

## Cross-Component Rules (X)

### X001: Referenced files exist (WARNING)

**Check:** File paths in skills/commands/agents resolve
**Evidence:** Broken references cause runtime errors
**Context:** May be false positive if path is in example section
**Fix:** Create missing file or fix path

### X002: Components documented (INFO)

**Check:** README mentions all commands, agents, skills
**Evidence:** Documentation helps users discover features
**Fix:** Update README with component list

## Evidence Sources

All rules are derived from official Claude Code documentation:
- https://docs.anthropic.com/en/docs/claude-code/plugins
- https://docs.anthropic.com/en/docs/claude-code/slash-commands
- https://docs.anthropic.com/en/docs/claude-code/skills
- https://docs.anthropic.com/en/docs/claude-code/hooks

See `specification/audit-spec.yaml` for full evidence quotes and retrieval dates.
```

**Step 2: Commit**

```bash
git add skills/plugin-audit/references/rule-reference.md
git commit -m "feat: add rule-reference.md with all validation rules"
```

---

## Task 7: Clean Up Old Scripts

**Files:**
- Remove: `skills/plugin-audit/scripts/check-paths.sh`
- Remove: `skills/plugin-audit/scripts/check-file-references.sh`

**Step 1: Remove old scripts**

The functionality of these scripts is now handled by:
- `check-structure.sh` for deterministic checks
- Claude + context-patterns.md for semantic analysis

```bash
rm skills/plugin-audit/scripts/check-paths.sh
rm skills/plugin-audit/scripts/check-file-references.sh
```

**Step 2: Verify only new scripts remain**

Run: `ls skills/plugin-audit/scripts/`
Expected: `check-syntax.sh` and `check-structure.sh` only

**Step 3: Commit**

```bash
git add -A skills/plugin-audit/scripts/
git commit -m "chore: remove old scripts, replaced by check-syntax.sh and check-structure.sh"
```

---

## Task 8: Document Baseline Test Scenarios

**Files:**
- Create: `skills/plugin-audit/tests/baseline-scenarios.md`

**Step 1: Create tests directory and document**

```bash
mkdir -p skills/plugin-audit/tests
```

```markdown
# Baseline Test Scenarios

These scenarios document Claude's default behavior WITHOUT the redesigned skill loaded.
Run these BEFORE writing SKILL.md content to capture baseline failures.

## Purpose

TDD for skills: We need to know what Claude gets wrong by default so we can write skill content that specifically addresses those gaps.

## Test Protocol

1. Start fresh Claude Code session (no plugin-audit skill loaded)
2. Run each scenario prompt
3. Document Claude's response
4. Identify false positives and incorrect behavior
5. Use failures to guide SKILL.md content

---

## Scenario A: Example Path Detection

**Prompt:**
```
Audit the plugin at ~/.claude/plugins/plugin-dev. Check if all file references in skills exist.
```

**Expected baseline behavior:**
- Flags paths in example sections as "missing files"
- Doesn't distinguish teaching examples from real references
- May report 15-20+ false positives for example paths

**Target behavior (with skill):**
- Recognizes example sections (## Examples, code blocks)
- Skips file-existence checks for example paths
- Reports only genuinely missing references

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario B: Security Context Detection

**Prompt:**
```
Check the plugin at ~/.claude/plugins/plugin-dev for hardcoded /etc/ or /sys/ paths. Report any security issues.
```

**Expected baseline behavior:**
- Flags ALL occurrences of /etc/, /sys/ as vulnerabilities
- Doesn't understand deny-block context
- Reports security hooks as security problems

**Target behavior (with skill):**
- Analyzes context around path references
- Recognizes deny-block patterns (permissionDecision: deny, exit 1/2)
- Reports paths being ACCESSED as issues, skips paths being BLOCKED

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario C: Command Frontmatter Validation

**Prompt:**
```
Validate all commands in ~/.claude/plugins/plugin-dev have correct frontmatter according to Claude Code documentation.
```

**Expected baseline behavior:**
- May assume `name` field is required (it's not)
- May flag missing `name` as CRITICAL error
- Relies on assumptions rather than verified documentation

**Target behavior (with skill):**
- Loads specification with evidence-backed rules
- Knows `name` is optional (filename is source of truth)
- Only flags actually-required fields as CRITICAL

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario D: Cross-Component Consistency

**Prompt:**
```
Check if all components in ~/.claude/plugins/plugin-dev are properly documented in the README.
```

**Expected baseline behavior:**
- May miss components or have false matches
- Doesn't understand plugin structure conventions
- Inconsistent analysis

**Target behavior (with skill):**
- Systematically discovers all components
- Checks README against actual component list
- Reports specific missing documentation

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Running Baseline Tests

### Setup

1. Ensure plugin-audit skill is NOT loaded
2. Use a fresh Claude Code session
3. Copy prompts exactly as written

### Documenting Results

For each scenario, record:
1. Claude's full response
2. List of issues reported
3. Which issues are false positives
4. Any correct findings
5. Rationalizations Claude used for incorrect findings

### Using Results

After baseline testing:
1. Identify common failure patterns
2. Write SKILL.md content addressing each pattern
3. Re-run scenarios with skill loaded
4. Iterate until all false positives eliminated
```

**Step 2: Commit**

```bash
git add skills/plugin-audit/tests/
git commit -m "docs: add baseline test scenarios for TDD skill development"
```

---

## Task 9: Write Lean SKILL.md

**Files:**
- Modify: `skills/plugin-audit/SKILL.md`

**Step 1: Write the new lean SKILL.md (~400 words)**

```markdown
---
name: Plugin Audit
description: >
  Use when the user asks to "audit a plugin", "validate plugin structure",
  "check plugin quality", "lint plugin", "review plugin for issues", or
  "verify plugin correctness". Also use for "check plugin best practices"
  or validating plugins before testing or publishing.
version: 1.0.0
---

# Plugin Audit

Five-layer validation pipeline for Claude Code plugins. Eliminates false positives through evidence-backed rules and context analysis.

## Quick Start

1. **Run syntax validation** (Layer 1):
   ```bash
   bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-syntax.sh <plugin-path>
   ```

2. **Run structure validation** (Layer 2):
   ```bash
   bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-structure.sh <plugin-path>
   ```

3. **Apply context analysis** (Layer 3) - Filter false positives using `references/context-patterns.md`

4. **Report findings** with confidence levels and rule provenance

## Pipeline Overview

| Layer | Question | Method |
|-------|----------|--------|
| 1. Syntax | Valid JSON/YAML? | Scripts (deterministic) |
| 2. Structure | Follows rules? | Scripts + spec |
| 3. Context | Real issue or false positive? | Context patterns |
| 4. Quality | Good content? | Claude analysis (--deep) |
| 5. Cross-component | Consistent overall? | Claude analysis |

## Key Rules

Before reporting issues, verify against `specification/audit-spec.yaml`:

- **Commands:** `name` field is NOT required (filename is source of truth)
- **Skills:** `name` and `description` ARE required
- **Agents:** `description` and `tools` ARE required
- **Paths:** Must use `$CLAUDE_PLUGIN_ROOT` for portability

## Context Filtering

Before reporting, check if issue is a false positive:

1. **Example sections** - Paths under `## Examples` or in code blocks are teaching examples
2. **Security blocks** - Paths in `permissionDecision: deny` blocks are features, not vulnerabilities
3. **Explicit markers** - `<!-- audit:example-section -->` means skip

See `references/context-patterns.md` for detection patterns.

## Report Format

```markdown
# Plugin Audit Report: {name}

## Summary
| Severity | Confirmed | Needs Review | Skipped |
|----------|-----------|--------------|---------|

## Confirmed Issues
[High-confidence issues with rule ID, file:line, fix]

## Needs Review
[Medium-confidence issues]

## Skipped (Context-Filtered)
[Issues filtered with reasoning]
```

## References

- `specification/audit-spec.yaml` - All rules with evidence
- `references/context-patterns.md` - False positive detection
- `references/rule-reference.md` - Rule explanations
- `tests/baseline-scenarios.md` - Test scenarios

## Related

- `/plugin-dev:audit-plugin` - Command to run audit
- `/plugin-dev:fix-plugin` - Interactive repair session
- `plugin-validator` agent - Proactive validation
```

**Step 2: Verify word count**

Run: `wc -w skills/plugin-audit/SKILL.md`
Expected: ~350-450 words (excluding frontmatter)

**Step 3: Commit**

```bash
git add skills/plugin-audit/SKILL.md
git commit -m "refactor: rewrite SKILL.md as lean ~400 word guide"
```

---

## Task 10: Run Baseline Tests

**Files:**
- Modify: `skills/plugin-audit/tests/baseline-scenarios.md` (fill in results)

**Step 1: Run Scenario A without skill**

In a fresh Claude Code session (not loading plugin-dev), run:
```
Audit the plugin at ~/.claude/plugins/plugin-dev. Check if all file references in skills exist.
```

Document the response in baseline-scenarios.md.

**Step 2: Run Scenario B without skill**

```
Check the plugin at ~/.claude/plugins/plugin-dev for hardcoded /etc/ or /sys/ paths. Report any security issues.
```

Document the response.

**Step 3: Run Scenario C without skill**

```
Validate all commands in ~/.claude/plugins/plugin-dev have correct frontmatter according to Claude Code documentation.
```

Document the response.

**Step 4: Run Scenario D without skill**

```
Check if all components in ~/.claude/plugins/plugin-dev are properly documented in the README.
```

Document the response.

**Step 5: Commit baseline results**

```bash
git add skills/plugin-audit/tests/baseline-scenarios.md
git commit -m "docs: record baseline test results"
```

---

## Task 11: Run Validation with Skill

**Step 1: Test with skill loaded**

Now run the same scenarios with the redesigned skill loaded to verify improvement.

**Step 2: Iterate if needed**

If false positives remain:
1. Identify the gap in SKILL.md or references
2. Add specific guidance addressing the failure
3. Re-run test
4. Repeat until all scenarios pass

**Step 3: Commit any fixes**

```bash
git add -A skills/plugin-audit/
git commit -m "fix: address false positives found in testing"
```

---

## Task 12: Final Validation

**Step 1: Run full audit on plugin-dev**

```bash
/plugin-dev:audit-plugin ~/.claude/plugins/plugin-dev
```

**Step 2: Verify zero false positives**

Check that:
- [ ] No example paths flagged as missing
- [ ] No security blocks flagged as vulnerabilities
- [ ] No commands flagged for missing `name` field
- [ ] All reported issues are genuine

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete plugin-audit redesign with evidence-backed rules"
```

---

## Summary

After completing all tasks:

**Created:**
- `specification/audit-spec.yaml` - Evidence-backed rules
- `scripts/check-syntax.sh` - Layer 1 syntax validation
- `scripts/check-structure.sh` - Layer 2 structure validation
- `references/context-patterns.md` - Layer 3 false positive detection
- `references/rule-reference.md` - All rules documented
- `tests/baseline-scenarios.md` - TDD test scenarios

**Removed:**
- 8 old reference files (consolidated)
- 4 old scripts (replaced with 2 unified scripts)

**Modified:**
- `SKILL.md` - Lean ~400 word version

**Architecture:**
- 5-layer pipeline (Syntax → Structure → Context → Quality → Cross-component)
- Evidence-backed rules with provenance
- Context analysis to eliminate false positives
