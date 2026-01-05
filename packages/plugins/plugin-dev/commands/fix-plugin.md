---
description: Interactive repair session for plugin issues with auto-fix and guided resolution
argument-hint: "[path]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - TodoWrite
---

# Plugin Fix Command

Start an interactive repair session to fix issues identified in a plugin audit. Supports auto-fixing straightforward issues and guided resolution for complex ones.

## Arguments

- `$1` - Plugin path (defaults to current directory if not provided)

## Repair Process

### 1. Run or Retrieve Audit

First, get the current state of issues:
- Run `/plugin-dev:audit-plugin` on the plugin to get fresh results
- Parse the issues list by severity and category

### 2. Backup Strategy

Before making any changes, ensure safety:

**If plugin is in a git repository:**
- Verify with: `git -C <plugin-path> rev-parse --git-dir`
- If yes, rely on git for recovery
- Note: "Changes can be reverted with `git checkout .`"

**If NOT in a git repository:**
- Create backup directory: `<plugin-path>/.audit-backup-<timestamp>/`
- Copy files that will be modified
- Inform user: "Backups saved to .audit-backup-<timestamp>/"

### 3. Categorize Issues

Separate issues into two categories:

#### Auto-Fixable Issues

Mechanical fixes with a single correct answer:

| Issue Type | Auto-Fix Action |
|------------|----------------|
| Missing `version` field | Add `"version": "0.1.0"` to manifest |
| Non-kebab-case filename | Rename file to kebab-case |
| Missing `timeout` in hook | Add `"timeout": 30000` |
| Hardcoded absolute path | Replace with `$CLAUDE_PLUGIN_ROOT/...` |
| Missing `description` in manifest | Add placeholder description |
| Script not executable | Run `chmod +x` on script |
| Tilde path in JSON | Replace `~/` with `$HOME/` or `$CLAUDE_PLUGIN_ROOT/` |

#### Interactive Issues

Require user input or have trade-offs:

| Issue Type | Why Interactive |
|------------|----------------|
| Skill description needs rewrite | Multiple valid phrasings |
| Choose `allowed-tools` | Depends on command's needs |
| SKILL.md too long | User decides what to extract |
| Weak trigger phrases | User knows their use cases |
| Agent examples too vague | User provides realistic scenarios |
| System prompt too short | User defines agent's role |

### 4. Process Auto-Fixable Issues

Present all auto-fixable issues as a batch:

```
## Auto-Fixable Issues

I can automatically fix these X issues:

1. [S006] Add missing version to manifest
2. [H005] Add timeout to hooks.json
3. [SEC002] Replace hardcoded path in hooks/hooks.json
4. [S008] Rename MyCommand.md to my-command.md

Proceed with auto-fixes? [Yes / No / Select specific fixes]
```

Use AskUserQuestion to get confirmation:
- **Yes**: Apply all auto-fixes
- **No**: Skip auto-fixes, proceed to interactive
- **Select**: Let user choose which to apply

For each auto-fix applied:
1. Make the change using Edit or Write tool
2. Log what was changed
3. Verify fix resolved the issue

### 5. Process Interactive Issues

For each interactive issue, present context and options:

```
## Issue 2 of 5: Skill Description Quality

**File:** skills/my-skill/SKILL.md:3
**Current:**
```yaml
description: Use this skill when you need help with hooks
```

**Problems:**
- Uses second person ("you need")
- Vague trigger ("help with hooks")
- No specific trigger phrases

**Options:**

1. **Rewrite with standard pattern:**
   ```yaml
   description: >
     This skill should be used when the user asks to "create a hook",
     "add a PreToolUse hook", "validate hook configuration", or needs
     guidance on Claude Code hook development.
   ```

2. **Provide your own description:**
   Enter custom description text

3. **Skip this issue:**
   Leave unchanged for manual fix later
```

Use AskUserQuestion to get user's choice, then apply the selected fix.

### 6. Handle Complex Restructuring

For issues like "SKILL.md too long":

1. Show current word count and structure
2. Identify sections that could move to references/
3. Present extraction options:
   - "Extract 'Detailed Patterns' section to references/patterns.md?"
   - "Extract 'Advanced Techniques' to references/advanced.md?"
4. Perform extraction maintaining references in SKILL.md

### 7. Verify Fixes

After each fix or batch of fixes:
- Re-run the specific validation that caught the issue
- Confirm issue is resolved
- If not resolved, explain what went wrong

### 8. Summary Report

At the end of the session:

```
## Repair Session Complete

### Fixed
- ✅ [S006] Added version to manifest
- ✅ [SK005] Rewrote skill description in third-person
- ✅ [H005] Added timeout to hooks

### Skipped
- ⏭️ [SK008] SKILL.md length - user chose to address later

### Remaining
- ⚠️ [A004] Agent examples need more detail (manual fix required)

### Commands Run
- 4 files modified
- 0 files created
- Backup at: .audit-backup-20241228-143022/

### Verification
Run `/plugin-dev:audit-plugin` to confirm all issues are resolved.
```

## Interaction Patterns

### For Simple Choices

Use AskUserQuestion with clear options:

```
Fix the skill description?
- Option 1: Use suggested rewrite (recommended)
- Option 2: Enter custom text
- Option 3: Skip for now
```

### For Text Input

When user needs to provide content:

```
Enter the new skill description (should be third-person with trigger phrases):
>
```

### For Batch Decisions

When multiple similar issues exist:

```
Found 3 commands missing allowed-tools. How to proceed?
- Fix all with Read, Glob, Grep (safe default)
- Review each individually
- Skip all
```

## Safety Guidelines

1. **Never delete files** without explicit confirmation
2. **Always show before/after** for content changes
3. **Preserve formatting** when editing YAML/JSON
4. **Test JSON validity** after edits
5. **Offer to revert** if something goes wrong

## Examples

**Fix current directory plugin:**
```
/fix-plugin
```

**Fix specific plugin:**
```
/fix-plugin ~/.claude/plugins/my-plugin
```
