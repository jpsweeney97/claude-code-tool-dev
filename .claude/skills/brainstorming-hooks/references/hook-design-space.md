# Hook Design Space

Comprehensive reference for hook event types, hook types, matchers, and output mechanisms.

## Table of Contents

1. [Event Types](#event-types)
2. [Hook Types](#hook-types)
3. [Matchers](#matchers)
4. [Output Mechanisms](#output-mechanisms)
5. [Input Schemas](#input-schemas)

---

## Event Types

| Event | When It Fires | Can Block | Primary Use Cases |
|-------|---------------|-----------|-------------------|
| **PreToolUse** | Before tool execution | Yes | Validate commands, enforce policies, transform input |
| **PostToolUse** | After tool succeeds | No | Log results, trigger follow-up actions, validate output |
| **PostToolUseFailure** | After tool fails | No | Error tracking, retry logic, failure patterns |
| **PermissionRequest** | Permission dialog shown | Yes | Auto-approve patterns, deny dangerous ops |
| **UserPromptSubmit** | User submits prompt | Yes | Inject context, validate input, block sensitive prompts |
| **Stop** | Claude finishes responding | Yes | Quality gates, ensure completeness |
| **SubagentStop** | Subagent finishes | Yes | Validate subagent output, ensure task completion |
| **SubagentStart** | Subagent spawns | No | Track subagent usage, log delegation patterns |
| **PreCompact** | Before context compaction | No | Preserve critical context, inject summaries |
| **Setup** | `--init`, `--init-only`, `--maintenance` | No | One-time setup, dependency installation, migrations |
| **SessionStart** | Session begins or resumes | No | Load context, set environment, inject reminders |
| **SessionEnd** | Session terminates | No | Cleanup, persist state, log session stats |
| **Notification** | Claude sends notifications | No | Custom alerts, external integrations |

### Event Selection Guide

**Want to prevent something?**
- PreToolUse — block before it happens
- PermissionRequest — intercept the permission dialog
- UserPromptSubmit — block the prompt itself
- Stop/SubagentStop — prevent completion until criteria met

**Want to react to something?**
- PostToolUse — after successful tool execution
- PostToolUseFailure — after failed tool execution
- SessionEnd — when session terminates

**Want to inject context?**
- SessionStart — once at session start
- UserPromptSubmit — every prompt
- PreCompact — before context is compacted

**Want to track/log something?**
- PostToolUse — tool usage
- SubagentStart/SubagentStop — subagent patterns
- SessionEnd — session statistics

---

## Hook Types

| Type | Execution | Decision Logic | Best For |
|------|-----------|----------------|----------|
| **command** | Runs bash/script | You implement | Deterministic rules, pattern matching, file checks |
| **prompt** | Queries Haiku LLM | LLM evaluates | Judgment calls, context-aware decisions |
| **agent** | Agentic with tools | Agent reasons | Complex verification needing tool access (plugins only) |

### When to Use Each

**Command hooks** (default):
- Pattern matching (regex, glob)
- File existence/content checks
- Environment validation
- Deterministic allow/block rules
- Fast execution required (<1s)

**Prompt hooks**:
- "Is this safe?" judgments
- Context-aware decisions
- Natural language evaluation
- When rules are hard to codify

**Agent hooks** (plugins only):
- Need to read files to make decision
- Need to run commands to verify
- Complex multi-step verification

### Performance Comparison

| Type | Latency | Resource Cost |
|------|---------|---------------|
| command | ~10-100ms | Local CPU only |
| prompt | ~1-5s | API call to Haiku |
| agent | ~5-30s | Multiple API calls |

---

## Matchers

Matchers filter which events trigger the hook. Syntax varies by event type.

### Tool Matchers (PreToolUse, PostToolUse, PermissionRequest)

| Pattern | Matches |
|---------|---------|
| `Bash` | Bash tool only (exact, case-sensitive) |
| `Write` | Write tool only |
| `Edit\|Write` | Either Edit or Write |
| `Notebook.*` | NotebookEdit, NotebookRead, etc. |
| `mcp__memory__.*` | All tools from memory MCP server |
| `mcp__.*__read.*` | Any MCP read tool |
| `*` or omit | All tools |

**MCP tool naming:** `mcp__<server>__<tool>`

### Notification Matchers

| Matcher | Triggers On |
|---------|-------------|
| `permission_prompt` | Permission requests |
| `idle_prompt` | Idle >60 seconds |
| `auth_success` | Authentication success |
| `elicitation_dialog` | MCP tool elicitation |

### PreCompact Matchers

| Matcher | Triggers On |
|---------|-------------|
| `manual` | `/compact` command |
| `auto` | Auto-compact (context full) |

### SessionStart Matchers

| Matcher | Triggers On |
|---------|-------------|
| `startup` | New session |
| `resume` | `--resume`, `--continue`, `/resume` |
| `clear` | `/clear` command |
| `compact` | After compaction |

### Setup Matchers

| Matcher | Triggers On |
|---------|-------------|
| `init` | `--init` or `--init-only` |
| `maintenance` | `--maintenance` |

---

## Output Mechanisms

### Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| **0** | Success | Operation proceeds; stdout processed |
| **2** | Blocking error | Operation blocked; stderr shown to Claude |
| **Other** | Non-blocking error | Logged; operation proceeds |

**Critical:** Exit 2 blocks. Exit 1 does NOT block.

### stdout/stderr by Event

| Event | stdout (exit 0) | stderr (exit 2) |
|-------|-----------------|-----------------|
| UserPromptSubmit | Added as context | Shown to user (blocks prompt) |
| SessionStart | Added as context | Shown to user |
| PreToolUse | Verbose mode only | Shown to Claude (blocks tool) |
| PostToolUse | Verbose mode only | Shown to Claude |
| Stop/SubagentStop | Verbose mode only | Shown to Claude (blocks stop) |
| Others | Verbose mode only | Verbose mode only |

### JSON Output (exit 0 only)

JSON in stdout enables advanced control. Common fields:

```json
{
  "continue": true,
  "stopReason": "string",
  "suppressOutput": true,
  "systemMessage": "string"
}
```

#### PreToolUse JSON

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "string",
    "updatedInput": { "field": "new value" },
    "additionalContext": "string"
  }
}
```

| Field | Effect |
|-------|--------|
| `permissionDecision: "allow"` | Bypasses permission system |
| `permissionDecision: "deny"` | Blocks tool, reason shown to Claude |
| `permissionDecision: "ask"` | Shows permission dialog |
| `updatedInput` | Modifies tool input before execution |
| `additionalContext` | Added to Claude's context |

#### UserPromptSubmit JSON

```json
{
  "decision": "block",
  "reason": "string",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "string"
  }
}
```

| Field | Effect |
|-------|--------|
| `decision: "block"` | Prevents prompt processing, erases prompt |
| `additionalContext` | Added as context for Claude |

#### Stop/SubagentStop JSON

```json
{
  "decision": "block",
  "reason": "string"
}
```

| Field | Effect |
|-------|--------|
| `decision: "block"` | Prevents stopping, Claude continues with reason |

#### SessionStart JSON

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "string"
  }
}
```

#### PermissionRequest JSON

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow|deny",
      "updatedInput": { "field": "value" },
      "message": "string",
      "interrupt": true
    }
  }
}
```

---

## Input Schemas

All hooks receive JSON on stdin with common fields:

```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions",
  "hook_event_name": "string"
}
```

### Event-Specific Fields

**PreToolUse / PostToolUse:**
- `tool_name`: Tool being called
- `tool_input`: Tool parameters
- `tool_use_id`: Unique identifier
- `tool_response`: (PostToolUse only) Tool output

**UserPromptSubmit:**
- `prompt`: User's submitted prompt

**Stop / SubagentStop:**
- `stop_hook_active`: Boolean — true if already continuing from a stop hook

**SubagentStart / SubagentStop:**
- `agent_id`: Subagent identifier
- `agent_type`: Agent name (SubagentStart)
- `agent_transcript_path`: Subagent's transcript (SubagentStop)

**SessionStart:**
- `source`: startup|resume|clear|compact
- `model`: Model identifier
- `agent_type`: If started with `--agent`

**SessionEnd:**
- `reason`: clear|logout|prompt_input_exit|other

**PreCompact:**
- `trigger`: manual|auto
- `custom_instructions`: User's compact instructions

**Notification:**
- `message`: Notification content
- `notification_type`: Type of notification

### Environment Variables

| Variable | Available In | Description |
|----------|--------------|-------------|
| `CLAUDE_PROJECT_DIR` | All | Project root (absolute path) |
| `CLAUDE_CODE_REMOTE` | All | `"true"` if remote/web |
| `CLAUDE_PLUGIN_ROOT` | Plugin hooks | Plugin directory |
| `CLAUDE_ENV_FILE` | SessionStart, Setup | Path for env persistence |
