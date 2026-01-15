---
description: Run comprehensive plugin audit. Invokes the `plugin-audit` skill with structured output, severity ratings, and fix suggestions. Use this command for on-demand audits; the skill loads automatically when discussing audit topics.
argument-hint: "[path] [--json]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
---

# Plugin Audit Command

Perform a comprehensive audit of a Claude Code plugin, checking structure, component quality, security, and best practices.

## Arguments

- `$1` - Plugin path (defaults to current directory if not provided)
- `--json` flag in arguments enables JSON output for CI/scripting

## Audit Process

### 1. Locate and Validate Plugin

First, determine the plugin path:
- If path argument provided, use it
- Otherwise, use current working directory
- Verify `.claude-plugin/plugin.json` exists to confirm it's a valid plugin

If not a valid plugin directory, report error and exit.

### 2. Load Auditing Knowledge

The `plugin-audit` skill provides comprehensive validation rules. Reference:
- `$CLAUDE_PLUGIN_ROOT/skills/plugin-audit/SKILL.md` for methodology
- `$CLAUDE_PLUGIN_ROOT/skills/plugin-audit/references/` for detailed rules per category

### 3. Run Validation Scripts

Execute deterministic validation scripts for objective checks:

**Syntax validation** (JSON/YAML validity):
```
bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-syntax.sh <plugin-path>
```

**Structure validation** (manifest, directories, required fields):
```
bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-structure.sh <plugin-path>
```

### 4. Perform Content Quality Analysis

Beyond scripts, analyze content quality:

**Skills:**
- Description uses third-person format
- Contains specific trigger phrases (quoted strings)
- Body uses imperative form (not "you should")
- Appropriate length (<3000 words, ideally 1500-2000)
- Avoids weak trigger words (help, assist, general, various)

**Commands:**
- Instructions written FOR Claude, not TO user
- Has usage examples
- allowed-tools follows least privilege

**Agents:**
- Has specific `<example>` blocks
- Examples are concrete and realistic
- System prompt is substantive

### 5. Generate Report

#### Standard Output (Markdown)

```markdown
# Plugin Audit Report: {plugin-name}

## Summary
| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | X     | ✅/❌   |
| WARNING  | X     | ✅/⚠️   |
| INFO     | X     | ℹ️      |

## Issues

### ❌ CRITICAL
[List each critical issue]

### ⚠️ WARNING
[List each warning]

### ℹ️ INFO
[List each suggestion]

## Passed Checks
[Summary of what passed validation]
```

#### Each Issue Format

```markdown
#### [RULE-ID] Issue title
**File:** `path/to/file.md:line`
**Issue:** What's wrong
**Why:** Brief explanation of impact
**Fix:** Actionable suggestion
```

#### JSON Output (when --json flag present)

```json
{
  "plugin": "plugin-name",
  "path": "/path/to/plugin",
  "timestamp": "ISO-8601",
  "summary": {
    "critical": 0,
    "warning": 3,
    "info": 2,
    "passed": true
  },
  "issues": [
    {
      "id": "SK001",
      "severity": "warning",
      "category": "skills",
      "file": "skills/my-skill/SKILL.md",
      "line": 3,
      "message": "Description uses first-person",
      "fix": "Change to third-person format"
    }
  ],
  "passed_checks": ["structure", "security", "hooks"]
}
```

### 6. Exit Status and Next Steps

**Exit with non-zero status if critical issues found** - important for CI integration.

After displaying the report, offer next steps:

"Audit complete. Would you like to:
1. **Auto-fix** straightforward issues (X issues can be auto-fixed)
2. **Interactive repair** session for all issues
3. **Review manually** - no automated changes"

If user chooses option 1 or 2, invoke the `/plugin-dev:fix-plugin` command.

## Audit Categories

Run checks in this order:

1. **Structure** - manifest, directories, naming (S001-S013)
2. **Skills** - SKILL.md quality, descriptions, content (SK001-SK013)
3. **Commands** - frontmatter, documentation, tools (C001-C010)
4. **Agents** - triggering, examples, system prompt (A001-A010)
5. **Hooks** - JSON validity, events, paths (H001-H010)
6. **MCP** - configuration, environment variables (M001-M008)
7. **Security** - credentials, paths, dangerous commands (SEC001-SEC009)
8. **Cross-component** - consistency, references, documentation (X001-X008)

## Examples

**Audit current directory:**
```
/audit-plugin
```

**Audit specific plugin:**
```
/audit-plugin ~/.claude/plugins/my-plugin
```

**JSON output for CI:**
```
/audit-plugin ~/.claude/plugins/my-plugin --json
```
