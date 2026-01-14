# Agents Documentation Harmonization Design

**Date:** 2026-01-10
**Goal:** Harmonize `.claude/rules/agents.md` with `docs/extension-reference/agents/` — both sources consistent and cross-referenced, serving their respective audiences.

## Audience Distinction

| Source | Purpose |
|--------|---------|
| `.claude/rules/agents.md` | Development guide — loaded contextually when working in `.claude/agents/`, focused on *how to build* agents with patterns, anti-patterns, checklists |
| `docs/extension-reference/agents/` | Reference specification — authoritative source for *what exists*, schema details, all features documented |

## Summary of Changes

### Rules File Changes (14 modifications)

| Category | Count | Items |
|----------|-------|-------|
| High-severity fixes | 3 | Hooks format, built-in models, Task tool parameters |
| Medium-severity fixes | 2 | permissionMode values, resume section |
| New sections | 4 | Location priority, project-level hooks, env variables, resume |
| Expanded sections | 4 | Frontmatter table, background execution, context isolation, model guidance |

### Docs File Changes (4 files)

| File | Changes |
|------|---------|
| agents-overview.md | +1 section (When NOT to Use) |
| agents-frontmatter.md | Remove `prompt` field, fix context line, fix tools/skills type to string, +1 table |
| agents-task-tool.md | Fix description field wording |
| agents-patterns.md | +2 sections (Anti-patterns, Testing) |

---

## Rules File: High-Severity Fixes

### Fix 1: Hooks Format (lines 92-99)

Replace simplified format with correct nested schema:

```yaml
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./scripts/validate-command.sh
  Stop:
    - hooks:
        - type: command
          command: ./scripts/cleanup.sh
```

Add note:
> The nested `hooks` array with `type: command` is required. This structure supports future hook types beyond shell commands.

### Fix 2: Built-in Models (lines 324-328)

Change table to:

| Type | Model | Tools | Notes |
|------|-------|-------|-------|
| `general-purpose` | Inherits | All | Multi-step modification tasks |
| `Plan` | Inherits | Read, Glob, Grep, Bash | Plan mode architecture |
| `Explore` | Haiku | Glob, Grep, Read, Bash (read-only) | Thoroughness: quick, medium, very thorough |

Expand "Choose the right model" section:
> Built-in agents `general-purpose` and `Plan` inherit the main conversation's model. Override with the `model` parameter when invoking via Task tool if needed.

### Fix 3: Task Tool Parameters (lines 108-114)

Reorder with required fields first:

```markdown
Task tool parameters:
- description: "Short summary"   # Required (brief description of task)
- prompt: "<task details>"       # Required
- subagent_type: "<name>"        # Required
- model: "haiku"                 # Optional override
- resume: "<agentId>"            # Optional: continue previous agent
- max_turns: 10                  # Optional turn limit
- run_in_background: true        # Optional async execution
```

---

## Rules File: Medium-Severity Fixes

### Fix 1: Remove `ignore` from permissionMode

Update line 68 to:
```markdown
| `permissionMode` | No | string | `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions` |
```

### Fix 2: New "Resuming Agents" Subsection

Add after "Background Execution" section:

```markdown
## Resuming Agents

Agents can be resumed to continue work with full context preserved.

### Resume Pattern

\`\`\`typescript
// Initial invocation returns agentId
Task(description: "Review auth", prompt: "...", subagent_type: "reviewer")
// Returns: { agentId: "abc123", ... }

// Resume later with new instructions
Task(resume: "abc123", prompt: "Now also check authorization")
\`\`\`

### When to Resume

- Continuing multi-phase work
- Adding follow-up tasks
- Correcting or refining output

### Storage

Transcripts persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`

Auto-deleted after `cleanupPeriodDays` (default: 30).
```

---

## Rules File: New Sections

### Section 1: Location Priority (after line 22)

```markdown
## Agent Priority

When multiple agents share the same name, higher priority wins:

| Priority | Scope | Path |
|----------|-------|------|
| 1 (highest) | Session | `--agents` CLI flag (JSON) |
| 2 | Project | `.claude/agents/<name>.md` |
| 3 | User | `~/.claude/agents/<name>.md` |
| 4 (lowest) | Plugin | Plugin's `agents/` directory |

This allows project-level agents to shadow user-level agents for testing.
```

### Section 2: Project-Level Agent Hooks (after hooks example)

```markdown
### Project-Level Agent Hooks

Beyond hooks in agent frontmatter, define hooks in `settings.json` that respond to agent lifecycle:

\`\`\`json
{
  "hooks": {
    "SubagentStart": [
      { "matcher": "db-agent", "hooks": [{ "type": "command", "command": "./setup.sh" }] }
    ],
    "SubagentStop": [
      { "matcher": "db-agent", "hooks": [{ "type": "command", "command": "./cleanup.sh" }] }
    ]
  }
}
\`\`\`

| Event | When | Matcher |
|-------|------|---------|
| `SubagentStart` | Agent begins | Agent name |
| `SubagentStop` | Agent completes | Agent name |

Use `matcher` to target specific agents. Omit to run for all agents.
```

### Section 3: Hook Environment Variables

```markdown
### Hook Environment Variables

Hook commands receive context via environment variables:

| Variable | Description |
|----------|-------------|
| `$TOOL_INPUT` | JSON string of the tool's input parameters |

Example validation script:

\`\`\`bash
#!/bin/bash
# Block write queries in db-reader agent
if echo "$TOOL_INPUT" | grep -qiE '(INSERT|UPDATE|DELETE|DROP)'; then
  echo "Write operations not allowed" >&2
  exit 2  # Block the tool call
fi
exit 0
\`\`\`
```

---

## Rules File: Expanded Sections

### Expand 1: Frontmatter Fields Table

Add `disallowedTools` row and tip for `description`:

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | Yes | string | Unique identifier (lowercase + hyphens) |
| `description` | Yes | string | Natural language description. Include "use proactively" to encourage auto-delegation |
| `tools` | No | string | Comma-separated allowlist; omit to inherit all |
| `disallowedTools` | No | string | Comma-separated denylist; removed from inherited/specified tools |
| `model` | No | string | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | string | `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions` |
| `skills` | No | string | Comma-separated skills to auto-load (injected at startup, not inherited from parent) |
| `hooks` | No | object | `PreToolUse`, `PostToolUse`, or `Stop` handlers |

### Expand 2: Background Execution Section

Add comparison table:

```markdown
### Background Execution Limitations

Background agents differ from foreground:

| Aspect | Foreground | Background |
|--------|------------|------------|
| MCP tools | Available | Not available |
| Permissions | Prompts pass through | Auto-deny if not pre-approved |
| AskUserQuestion | Works | Fails (agent continues) |
| Recovery | N/A | Resume in foreground to retry |
```

### Expand 3: Context Isolation

Change:
> Each agent invocation starts fresh. Don't assume prior state or shared memory.

To:
> Each agent invocation starts fresh. Agents receive only their system prompt (markdown body) and basic environment details (working directory, platform). They do **not** receive the full Claude Code system prompt or parent conversation context.

---

## Docs Changes

### agents-overview.md

Add after "When to Use" section:

```markdown
## When NOT to Use

- **Tasks requiring conversation** — Agents can't ask follow-up questions mid-execution
- **Shared state operations** — Agents run in separate contexts; no state sharing
- **Simple single-file reads** — Use Read tool directly (lower overhead)
- **Quick lookups** — Use Grep/Glob directly (agents add latency)
```

### agents-frontmatter.md

1. Remove `prompt` from schema example (lines 24-30)
2. Remove `prompt` row from Field Reference table
3. Change line 121 from "frontmatter `prompt` + markdown body" to "markdown body after frontmatter"
4. Fix `tools` and `skills` fields:
   - Change type from "array" to "string" in Field Reference table
   - Change schema examples from array format to comma-separated string format
5. Add Model Selection Guide table after `model` field:

```markdown
### Model Selection Guide

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Doc lookup, simple queries | haiku | Fast, economical |
| Standard development | sonnet | Balanced |
| Complex architecture, planning | opus | Highest capability |
```

### agents-task-tool.md

Change line 31 description from "Short description (3-5 words)" to "Brief task description"

### agents-patterns.md

Add at end:

```markdown
## Anti-patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Vague task instructions | Agent interprets broadly, wastes turns | Be specific |
| No output format | Main thread gets unstructured dumps | Specify format |
| Using opus for simple lookups | Slow and expensive | Use haiku |
| Expecting shared state | Agents are isolated | Pass all context in prompt |
| No constraints | Agent scope-creeps | Add explicit boundaries |
| Returning raw file contents | Context pollution | Require summaries |

## Testing Agents

1. Create agent in `.claude/agents/`
2. Test via Task tool: `subagent_type: "<name>"`
3. Verify output format matches specification
4. Test edge cases (empty results, large outputs)
5. Verify tool restrictions work as expected
```

---

## Implementation Order

1. **Rules file high-severity fixes** — Hooks format, built-in models, Task parameters
2. **Rules file medium-severity fixes** — permissionMode, resume section
3. **Rules file new sections** — Priority, project hooks, env variables
4. **Rules file expanded sections** — Frontmatter table, background execution, context isolation
5. **Docs fixes** — agents-overview, agents-frontmatter (including tools/skills format fix), agents-task-tool, agents-patterns

## Decisions Log

| # | Issue | Decision | Rationale |
|---|-------|----------|-----------|
| High 1 | Hooks format | Update + explanatory note | Correct schema, educational |
| High 2 | Built-in models | "Inherits" + expand guidance | Comprehensive |
| High 3 | Task description | Add + reorder required first | Clear hierarchy |
| Med 1 | tools/skills format | Keep rules as-is (string); fix docs to string | Rules correct, docs wrong |
| Med 2 | permissionMode | Remove `ignore` | Match docs |
| Med 3 | resume | New subsection | Workflow pattern |
| Gap 1 | Location priority | Add to rules | Essential for testing |
| Gap 2 | /agents command | Skip | UI feature, not dev guide |
| Gap 3 | disallowedTools | Add + example | Correctness |
| Gap 4 | prompt field | Fix docs (not a field) | Docs error |
| Gap 5 | Context isolation | Expand + fix docs | Clarify both |
| Gap 6 | SubagentStart/Stop | Dedicated section | Comprehensive |
| Gap 7 | $TOOL_INPUT | Env vars section | Actionable |
| Gap 8 | MCP inheritance | Add to background | Warning needed |
| Gap 9 | Ctrl+B | Skip | UI shortcut |
| Gap 10 | Explore thoroughness | Add to table | One line addition |
| Gap 11 | --disallowedTools CLI | Skip | Settings is primary |
| Gap 12 | "Use proactively" | Add tip | Actionable |
| Gap 13 | Storage path | Add to resume | Debugging aid |
| Gap 14 | cleanupPeriodDays | Add to resume | Context |
| Gap 15 | Background permissions | Expand section | Important differences |
| Port 1 | When NOT to use | Add to overview | Completes guidance |
| Port 2 | Required sections | Skip | Opinionated |
| Port 3 | Anti-patterns | Add to patterns | Fits theme |
| Port 4 | Compliance checklist | Skip | Workflow-specific |
| Port 5 | Model selection | Add to frontmatter | Informed choices |
| Port 6 | Testing | Add to patterns | Best practices |

---

## Audit Notes

**Verified 2026-01-10:** Design document audited against source files.

**Corrections applied:**
- tools/skills format: Originally planned to change rules to array format. Corrected after user confirmed comma-separated string is the valid format. Rules are correct; docs need fixing.

**Minor line reference note:**
- "lines 124-125" for context isolation (design said "line 125-126") — will be adjusted during implementation based on actual line numbers after earlier edits
