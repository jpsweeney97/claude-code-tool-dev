---
paths: .claude/hooks/**
---

# Hook Development

Hooks are scripts that execute in response to Claude Code events. They can observe, log, modify, or block operations.

## When to Use Hooks

- **Enforce policies**: Block dangerous commands, require confirmation for destructive ops
- **Capture context**: Log tool usage, record session activity, capture decisions
- **Inject context**: Add system reminders, load relevant docs, provide runtime info
- **Integrate systems**: Notify external services, sync state, trigger workflows

## When NOT to Use Hooks

- **Complex logic requiring conversation**: Use skills instead (hooks can't converse)
- **One-off commands**: Use commands instead (hooks run automatically)
- **Subagent orchestration**: Use agents instead (hooks are synchronous)
- **Heavy computation**: Hooks block execution; keep them fast (<1s ideal, <60s max)

## Structure

Hooks are executable scripts with optional PEP 723-style frontmatter (our convention for `sync-settings`):

```
.claude/hooks/
├── <name>.py           # Hook script (executable)
└── ...
```

## Hook Script Format

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60
# ///

import json
import sys

def main():
    # Read event data from stdin
    event = json.load(sys.stdin)

    # Process and decide
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Exit codes determine behavior
    # 0 = allow, 1 = error (logged), 2 = block

    if should_block(tool_input):
        print("Blocked: reason here", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Event Types

| Event | When | Can Block | Use Case |
|-------|------|-----------|----------|
| **PreToolUse** | Before tool call | Yes | Validate commands, enforce policies |
| **PostToolUse** | After tool completes | No | Log results, capture outputs |
| **UserPromptSubmit** | User submits prompt | Yes | Inject context, validate input |
| **Stop** | Main agent finishes | Yes | Cleanup, final checks |
| **SubagentStop** | Subagent completes | Yes | Validate subagent output |
| **SessionStart** | Session begins | No | Initialize state, load context |
| **SessionEnd** | Session terminates | No | Cleanup, persist state |
| **PreCompact** | Before context compaction | No | Preserve critical context |
| **Notification** | Notification sent | No | External integrations |
| **PermissionRequest** | Permission dialog | Yes | Auto-approve/deny patterns |

## Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| **0** | Success | Operation proceeds; stdout processed (see below) |
| **2** | Blocking error | Operation blocked; only stderr used as error message |
| **Other** | Non-blocking error | Logged to debug; operation proceeds; stderr shown in verbose mode |

**Critical**: Use exit code 2 to block operations. Any other non-zero code (including 1) is a non-blocking error.

### stdout Behavior by Event (exit 0)

| Event | stdout Behavior |
|-------|-----------------|
| `UserPromptSubmit` | Added as context to the conversation |
| `SessionStart` | Added as context to the conversation |
| All other events | Shown in verbose mode (ctrl+o) only |

JSON in stdout is parsed for structured control on exit 0. On exit 2, JSON in stdout is ignored.

## Matcher Patterns

Matchers filter which events trigger the hook. Syntax:
- **Exact match**: `Write` matches only Write tool (case-sensitive)
- **Regex**: `Edit|Write` or `Notebook.*`
- **Wildcard**: `*` matches all
- **Empty/omitted**: Same as `*`

### Tool Matchers (PreToolUse, PostToolUse, PermissionRequest)

| Pattern | Matches |
|---------|---------|
| `Bash` | Bash tool only |
| `Write` | Write tool only |
| `Edit\|Write` | Either Edit or Write |
| `mcp__memory__.*` | All tools from memory MCP server |
| `*` or omit | All tools |

**MCP tool naming**: `mcp__<server>__<tool>` (e.g., `mcp__filesystem__read_file`)

### Notification Type Matchers

| Pattern | Matches |
|---------|---------|
| `permission_prompt` | Permission requests |
| `idle_prompt` | Idle notifications (60+ seconds) |
| `auth_success` | Authentication success |
| `elicitation_dialog` | MCP tool elicitation |

### PreCompact Matchers

| Pattern | Matches |
|---------|---------|
| `manual` | `/compact` command |
| `auto` | Auto-compact (context window full) |

### SessionStart Matchers

| Pattern | Matches |
|---------|---------|
| `startup` | New session startup |
| `resume` | `--resume`, `--continue`, or `/resume` |
| `clear` | `/clear` command |
| `compact` | After auto or manual compact |

## Input/Output Contract

### Input (stdin)

Hooks receive JSON on stdin. Common fields across all events:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/conversation.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions",
  "hook_event_name": "PreToolUse"
}
```

Event-specific additional fields:

| Event | Additional Fields |
|-------|-------------------|
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id` |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` |
| `UserPromptSubmit` | `prompt` |
| `Notification` | `message`, `notification_type` |
| `Stop`, `SubagentStop` | `stop_hook_active` |
| `PreCompact` | `trigger` (manual/auto), `custom_instructions` |
| `SessionStart` | `source` (startup/resume/clear/compact) |
| `SessionEnd` | `reason` (clear/logout/prompt_input_exit/other) |

**SessionStart special**: Receives `CLAUDE_ENV_FILE` environment variable for persisting env vars.

### Output

| Channel | Exit 0 | Exit 2 | Other Exit |
|---------|--------|--------|------------|
| **stdout** | Processed (JSON or text) | Ignored | Ignored |
| **stderr** | Ignored | Shown as error | Shown in verbose mode |

## Frontmatter Fields (Project Convention)

**Note**: The PEP 723-style frontmatter is this project's convention for `sync-settings`. Native Claude Code configures hooks via `settings.json` directly.

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `event` | Yes | string | Event type from table above |
| `matcher` | No | string | Filter pattern (tool/notification type/etc.) |
| `timeout` | No | integer | Seconds (default 60) |

## Design Principles

### Keep hooks fast
Hooks block execution. Target <1 second; never exceed timeout.

### Fail safe
If your hook errors (exit 1), the operation proceeds. Design for graceful degradation.

### Be specific with matchers
Broad matchers (`*`) on PreToolUse add latency to every tool call.

### Use stderr for block messages
At exit 2, stderr is shown to Claude. Make messages actionable.

### Don't rely on state
Hooks may run in any order; don't assume prior hooks ran.

## Common Patterns

### Block dangerous commands

```python
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'git\s+push\s+.*--force',
    r'DROP\s+TABLE',
]

def check_command(cmd):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return f"Blocked: matches dangerous pattern '{pattern}'"
    return None
```

### Inject session context

```python
# UserPromptSubmit hook
def add_context(event):
    context = gather_project_context()
    print(json.dumps({"context": context}))  # stdout for context injection
    sys.exit(0)
```

### Log tool usage

```python
# PostToolUse hook
def log_usage(event):
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "tool": event["tool_name"],
            "input": event["tool_input"],
        }) + "\n")
    sys.exit(0)
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Non-2 exit for blocking | Any exit except 2 is non-blocking | Use exit 2 to block |
| JSON in stdout at exit 2 | Ignored; only stderr used | Print error to stderr |
| Not reading stdin | Miss event data | Always `json.load(sys.stdin)` |
| Sync network calls without timeout | Hook hangs | Add timeouts; use async |
| Broad matcher on slow hook | Every tool call slows | Narrow matcher or optimize |
| Modifying files during PreToolUse | Race conditions | Log only; modify in PostToolUse |
| Assuming hook order | Hooks run in parallel | Design for independent execution |
| Not checking `stop_hook_active` | Infinite loop if blocking Stop | Check flag to prevent recursion |

## Testing

### Manual testing

```bash
# Test hook directly with mock input
echo '{"tool_name": "Bash", "tool_input": {"command": "ls"}}' | python .claude/hooks/my-hook.py
echo $?  # Check exit code
```

### Integration testing

1. Create hook in `.claude/hooks/`
2. Make executable: `chmod +x .claude/hooks/<name>.py`
3. Run `uv run scripts/sync-settings` to register
4. Start new Claude Code session
5. Trigger the event and verify behavior

## Workflow

1. Create `.claude/hooks/<name>.py` with frontmatter
2. Make executable: `chmod +x .claude/hooks/<name>.py`
3. Test manually with mock JSON input
4. Sync: `uv run scripts/sync-settings` (generates settings.json entry)
5. Test in Claude Code session
6. Promote: `uv run scripts/promote hook <name>`

**Important**: Claude Code reads hooks from `settings.json`, not from files directly. The `sync-settings` script generates config from frontmatter.

## Compliance Checklist

Before promoting a hook, verify:

- [ ] Frontmatter includes valid `event` type
- [ ] Matcher is specific (not `*` on slow hooks)
- [ ] Exit codes are correct (2 for block, not 1)
- [ ] Reads stdin JSON properly
- [ ] Stderr messages are actionable (for exit 2)
- [ ] Execution time is reasonable (<1s ideal)
- [ ] Error handling doesn't cause exit 1 on expected conditions
- [ ] No race conditions with file operations
- [ ] Tested with mock input before integration

## See Also

- **settings.md** — Configure hooks inline in settings.json
- **skills.md** — Use skills for complex logic (hooks can't converse)
- **plugins.md** — Bundle hooks with plugins for distribution
- **commands.md** — Use commands for user-invoked actions (hooks are automatic)

## References

Authoritative specification (imported for full context):
- @.claude/skills/claude-tool-audit/references/fallback-specs.md — Hook event types, exit codes, anti-patterns
