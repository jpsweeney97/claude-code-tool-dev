# Rules Sync with Official Claude Code Docs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update 6 rules files + 1 fallback-specs to match official Claude Code documentation.

**Architecture:** Direct file edits with find/replace operations. Checkpoint commit first, rules commit second, fallback-specs commit third.

**Tech Stack:** Bash, grep for verification

---

## Task 1: Pre-Flight Verification

**Files:**
- Read: `docs/documentation/*-reference.md`

**Step 1: Verify source docs exist**

Run: `for f in skills hooks commands subagents plugins plugin-marketplace settings; do test -f "docs/documentation/${f}-reference.md" || echo "MISSING: $f"; done`

Expected: No output (all files exist)

**Step 2: Create checkpoint commit**

Run: `git add -A && git commit -m "chore: checkpoint before rules sync" --allow-empty`

Expected: Commit created or "nothing to commit"

---

## Task 2: Delete Duplicate Skill

**Files:**
- Delete: `.claude/skills/claude-tool-audit/`

**Step 1: Verify directory exists**

Run: `ls -la .claude/skills/claude-tool-audit/`

Expected: Directory listing showing files

**Step 2: Delete the directory**

Run: `rm -rf .claude/skills/claude-tool-audit/`

Expected: No output

**Step 3: Verify deletion**

Run: `ls .claude/skills/ | grep claude-tool-audit`

Expected: No output (directory gone)

---

## Task 3: Update Backward References

**Files:**
- Modify: `.claude/rules/hooks.md`
- Modify: `.claude/rules/commands.md`
- Modify: `.claude/rules/plugins.md`
- Modify: `.claude/rules/agents.md`
- Modify: `.claude/rules/mcp-servers.md`

**Step 1: Find all occurrences**

Run: `grep -r "claude-tool-audit" .claude/rules/`

Expected: 5 matches (one per file)

**Step 2: Replace in all files**

Use Edit tool with `replace_all: true` on each file:
- Find: `claude-tool-audit`
- Replace: `auditing-tool-designs`

**Step 3: Verify replacement**

Run: `grep -r "claude-tool-audit" .claude/rules/`

Expected: No output

---

## Task 4: Update skills.md Frontmatter Example

**Files:**
- Modify: `.claude/rules/skills.md:24-34`

**Step 1: Replace the YAML example**

Find (lines 24-34):
```yaml
---
name: skill-name
description: One-line description for skill list
allowed-tools: ["Tool1", "Tool2"]  # Optional: auto-approve these tools
metadata:                           # Optional
  version: "1.0.0"
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---
```

Replace with:
```yaml
---
name: skill-name                    # Required: lowercase, hyphens, max 64 chars
description: One-line description   # Required: max 1024 chars
allowed-tools: Tool1, Tool2         # Optional: comma or YAML list
model: claude-sonnet-4-20250514     # Optional: specific model
context: fork                       # Optional: run in isolated subagent
agent: general-purpose              # Optional: agent type when context: fork
hooks:                              # Optional: component-scoped hooks
  PreToolUse:
    - matcher: Bash
      command: ./validate.sh
user-invocable: true                # Optional: controls slash menu visibility
disable-model-invocation: false     # Optional: blocks Skill tool invocation
---
```

**Step 2: Verify new fields present**

Run: `grep -E "context:|agent:|hooks:|user-invocable:|disable-model-invocation:" .claude/rules/skills.md | wc -l`

Expected: `5`

---

## Task 5: Update commands.md Frontmatter Table

**Files:**
- Modify: `.claude/rules/commands.md:55-56`

**Step 1: Add hooks row to table**

Find:
```markdown
| `disable-model-invocation` | No | boolean | Prevent Skill tool from calling this command |
```

Replace with:
```markdown
| `disable-model-invocation` | No | boolean | Prevent Skill tool from calling this command |
| `hooks` | No | object | PreToolUse, PostToolUse, or Stop handlers scoped to command |
```

**Step 2: Verify hooks field added**

Run: `grep "hooks.*PreToolUse.*PostToolUse.*Stop" .claude/rules/commands.md`

Expected: 1 match

---

## Task 6: Update agents.md Permission Mode

**Files:**
- Modify: `.claude/rules/agents.md:68`

**Step 1: Add ignore to permissionMode row**

Find:
```markdown
| `permissionMode` | No | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
```

Replace with:
```markdown
| `permissionMode` | No | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`, `ignore` |
```

**Step 2: Verify ignore added**

Run: `grep "permissionMode.*ignore" .claude/rules/agents.md`

Expected: 1 match

---

## Task 7: Update hooks.md with New Sections

**Files:**
- Modify: `.claude/rules/hooks.md` (insert before line 82, before `## Exit Codes`)

**Step 1: Find insertion point**

Run: `grep -n "## Exit Codes" .claude/rules/hooks.md`

Expected: Line 82

**Step 2: Insert Hook Types and Component-Scoped Hooks sections**

Insert BEFORE `## Exit Codes`:

```markdown
## Hook Types

| Type | Description | Model | Availability |
|------|-------------|-------|--------------|
| `command` | Execute bash script | N/A | All hooks |
| `prompt` | LLM-based evaluation | Haiku | All hooks |
| `agent` | Agentic verifier with tools | Configurable | Plugins only |

### Command Hook (Default)

```json
{
  "type": "command",
  "command": "~/.claude/hooks/validate.py",
  "timeout": 30
}
```

### Prompt Hook

```json
{
  "type": "prompt",
  "prompt": "Is this command safe to run? Respond ALLOW or BLOCK."
}
```

### Agent Hook (Plugins Only)

```json
{
  "type": "agent",
  "agent": "security-reviewer",
  "timeout": 120
}
```

## Component-Scoped Hooks

Skills, commands, and agents can define hooks directly in their frontmatter:

```yaml
---
name: my-skill
hooks:
  PreToolUse:
    - matcher: Bash
      command: ./validate.sh
      once: true          # Skills/commands only; NOT agents
  Stop:
    - command: ./cleanup.sh
---
```

**Note:** The `once: true` option is supported for skills and commands only (NOT agents).

```

**Step 3: Verify sections added**

Run: `grep -c "## Hook Types\|## Component-Scoped Hooks" .claude/rules/hooks.md`

Expected: `2`

---

## Task 8: Update plugins.md Hooks Section

**Files:**
- Modify: `.claude/rules/plugins.md:177-180`

**Step 1: Add hook types after JSON example**

Find (line 178):
```markdown
}
```

Insert after the closing brace of the JSON example:
```markdown

**Hook types**:
- `command`: Execute shell commands or scripts
- `prompt`: Evaluate a prompt with an LLM (uses `$ARGUMENTS` placeholder)
- `agent`: Run an agentic verifier with tools (plugins only)
```

**Step 2: Update Available events line**

Find:
```markdown
**Available events**: PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit, Notification, Stop, SubagentStop, SessionStart, SessionEnd, PreCompact
```

Replace with:
```markdown
**Available events**: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, UserPromptSubmit, Notification, Stop, SubagentStart, SubagentStop, SessionStart, SessionEnd, PreCompact
```

**Step 3: Verify updates**

Run: `grep "PostToolUseFailure\|SubagentStart" .claude/rules/plugins.md`

Expected: Both terms in output

Run: `grep "agent.*agentic verifier" .claude/rules/plugins.md`

Expected: 1 match

---

## Task 9: Update settings.md Permission Modes

**Files:**
- Modify: `.claude/rules/settings.md:83`

**Step 1: Add ignore row to Permission Modes table**

Find:
```markdown
| `bypassPermissions` | Skips all prompts (requires safe environment) |
```

Replace with:
```markdown
| `bypassPermissions` | Skips all prompts (requires safe environment) |
| `ignore` | No permissions enforced |
```

**Step 2: Verify ignore added**

Run: `grep "ignore.*No permissions" .claude/rules/settings.md`

Expected: 1 match

---

## Task 10: Commit Rules Changes

**Step 1: Stage rules files**

Run: `git add .claude/rules/`

**Step 2: Create commit**

```bash
git commit -m "docs(rules): sync with official Claude Code specs

- Add 5 frontmatter fields to skills.md (context, agent, hooks, user-invocable, disable-model-invocation)
- Add hooks field to commands.md frontmatter table
- Add ignore permission mode to agents.md and settings.md
- Add Hook Types and Component-Scoped Hooks sections to hooks.md
- Add PostToolUseFailure/SubagentStart events and hook types to plugins.md
- Update backward refs: claude-tool-audit → auditing-tool-designs"
```

Expected: Commit created

---

## Task 11: Rewrite fallback-specs.md

**Files:**
- Overwrite: `.claude/skills/auditing-tool-designs/references/fallback-specs.md`

**Step 1: Replace entire file**

Write the complete new content (from original plan lines 229-453).

**Step 2: Verify key additions present**

Run: `grep -E "context.*fork|once.*true|ignore" .claude/skills/auditing-tool-designs/references/fallback-specs.md | wc -l`

Expected: `3` or more matches

---

## Task 12: Commit fallback-specs

**Step 1: Stage file**

Run: `git add .claude/skills/auditing-tool-designs/references/fallback-specs.md`

**Step 2: Create commit**

```bash
git commit -m "docs(fallback-specs): comprehensive rewrite from official docs

Expanded from 160 to ~220 lines with:
- Hook types (command/prompt/agent)
- Component-scoped hooks with once:true caveat
- ignore permission mode
- PostToolUseFailure and SubagentStart events"
```

Expected: Commit created

---

## Task 13: Final Verification

**Step 1: Run all verification checks**

```bash
# 1. Duplicate skill deleted
ls .claude/skills/ | grep -c claude-tool-audit  # Expect: 0

# 2. Backward refs updated
grep -r "claude-tool-audit" .claude/rules/  # Expect: no output

# 3. skills.md — new fields present
grep -E "context:|agent:|hooks:|user-invocable:|disable-model-invocation:" .claude/rules/skills.md | wc -l  # Expect: 5

# 4. commands.md — hooks field added
grep "hooks.*PreToolUse" .claude/rules/commands.md | wc -l  # Expect: 1

# 5. agents.md — ignore added
grep "permissionMode.*ignore" .claude/rules/agents.md | wc -l  # Expect: 1

# 6. hooks.md — new sections added
grep -c "## Hook Types\|## Component-Scoped Hooks" .claude/rules/hooks.md  # Expect: 2

# 7. plugins.md — events and types updated
grep "PostToolUseFailure" .claude/rules/plugins.md | wc -l  # Expect: 1
grep "SubagentStart" .claude/rules/plugins.md | wc -l  # Expect: 1

# 8. settings.md — ignore added
grep "ignore.*No permissions" .claude/rules/settings.md | wc -l  # Expect: 1

# 9. fallback-specs.md — key additions present
grep -c "context.*fork\|once.*true\|ignore" .claude/skills/auditing-tool-designs/references/fallback-specs.md  # Expect: 3+
```

**Step 2: Review git log**

Run: `git log --oneline -3`

Expected: 3 commits (checkpoint, rules sync, fallback-specs)
