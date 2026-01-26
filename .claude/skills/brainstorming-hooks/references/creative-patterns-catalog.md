# Creative Patterns Catalog

Non-obvious hook uses organized by goal. Use this during Phase 2 (Explore the Design Space) to surface alternatives beyond the obvious PreToolUse+Bash+block pattern.

## Table of Contents

1. [Enforce](#enforce) — Block, warn, require confirmation
2. [Capture](#capture) — Log, record, track
3. [Inject](#inject) — Context, reminders, dynamic state
4. [Integrate](#integrate) — Notify, sync, trigger external
5. [Underexplored Patterns](#underexplored-patterns) — PreCompact, SubagentStop, input transformation, cross-event state, prompt hooks

---

## Enforce

### Block Dangerous Operations

**Obvious:** PreToolUse + Bash + pattern match + exit 2
```python
# Block rm -rf /
if re.search(r'rm\s+-rf\s+/', command):
    print("Blocked: dangerous rm command", file=sys.stderr)
    sys.exit(2)
```

**Alternative 1: Warn instead of block**
Use JSON output to inject a warning, let Claude decide:
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "This command modifies system files. Proceed?",
        "additionalContext": "WARNING: This command affects system directories."
    }
}
print(json.dumps(output))
sys.exit(0)
```

**Alternative 2: Transform instead of reject**
Use `updatedInput` to make the command safer:
```python
# Add --dry-run to dangerous commands
safe_command = command + " --dry-run"
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {"command": safe_command}
    }
}
```

**Alternative 3: Prompt hook for judgment**
Let Haiku decide if the command is dangerous:
```json
{
  "type": "prompt",
  "prompt": "Is this command dangerous? Context: $ARGUMENTS. Respond {\"ok\": true} to allow or {\"ok\": false, \"reason\": \"explanation\"} to block."
}
```

### Require Confirmation for Sensitive Files

**Pattern:** PermissionRequest hook with auto-deny for sensitive paths
```python
file_path = event["tool_input"].get("file_path", "")
if any(p in file_path for p in [".env", "credentials", ".secrets"]):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "deny", "message": "Cannot modify sensitive files"}
        }
    }
    print(json.dumps(output))
```

### Quality Gates Before Completion

**Pattern:** Stop hook that prevents completion until criteria met
```python
# Check if tests were run
if not tests_were_run(transcript):
    output = {"decision": "block", "reason": "Tests have not been run. Please run tests before completing."}
    print(json.dumps(output))
    sys.exit(0)
```

**Important:** Check `stop_hook_active` to prevent infinite loops.

---

## Capture

### Log All Tool Usage

**Pattern:** PostToolUse hook for comprehensive logging
```python
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "tool": event["tool_name"],
    "input": event["tool_input"],
    "response": event.get("tool_response"),
    "session": event["session_id"]
}
with open(log_path, "a") as f:
    f.write(json.dumps(log_entry) + "\n")
```

### Track Command Patterns

**Pattern:** PostToolUse + Bash to analyze command frequency
```python
# Track which commands are run most often
command = event["tool_input"].get("command", "")
# Extract base command (first word)
base_cmd = command.split()[0] if command else ""
increment_counter(base_cmd)
```

### Record Failed Attempts

**Pattern:** PostToolUseFailure to track error patterns
```python
# Log failures for later analysis
failure = {
    "tool": event["tool_name"],
    "input": event["tool_input"],
    "error": event.get("error"),
    "timestamp": datetime.now().isoformat()
}
append_to_failures_log(failure)
```

### Audit Subagent Delegation

**Pattern:** SubagentStart + SubagentStop to track delegation patterns
```python
# SubagentStart hook
delegation = {
    "agent_id": event["agent_id"],
    "agent_type": event["agent_type"],
    "started": datetime.now().isoformat()
}

# SubagentStop hook — match by agent_id, record duration
```

---

## Inject

### Dynamic Project Context

**Pattern:** SessionStart to load relevant project state
```python
context = f"""
Current branch: {get_current_branch()}
Uncommitted changes: {get_uncommitted_count()} files
Recent commits:
{get_recent_commits(5)}
Open issues: {get_open_issues_summary()}
"""
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))
```

### Per-Prompt Context

**Pattern:** UserPromptSubmit to inject context on every prompt
```python
# Different from SessionStart — runs every prompt
context = f"Current time: {datetime.now().isoformat()}"
print(context)  # Plain text works too
```

### Tool-Specific Reminders

**Pattern:** PreToolUse + matcher to inject context for specific tools
```python
# Remind about testing requirements before Write
if event["tool_name"] == "Write":
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "Remember: All new files need corresponding tests."
        }
    }
    print(json.dumps(output))
```

### Preserve Context Before Compaction

**Pattern:** PreCompact to inject critical context that survives compaction
```python
# Load critical context that should survive compaction
critical = load_critical_context()  # e.g., key decisions, constraints
print(critical)  # Will be included in compact
```

### Environment Setup

**Pattern:** SessionStart with CLAUDE_ENV_FILE for persistent env vars
```bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
    echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
    echo 'export DEBUG=true' >> "$CLAUDE_ENV_FILE"
fi
```

---

## Integrate

### Desktop Notifications

**Pattern:** Notification hook for system alerts
```bash
#!/bin/bash
# macOS
osascript -e 'display notification "Claude needs input" with title "Claude Code"'

# Linux
notify-send "Claude Code" "Claude needs input"
```

### Slack/Discord Integration

**Pattern:** Notification or Stop hook for team alerts
```python
import requests

def notify_slack(message):
    requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)

# On Stop — notify team that task is complete
notify_slack(f"Claude completed task in session {event['session_id']}")
```

### External Linting/Formatting

**Pattern:** PostToolUse + Write|Edit to trigger formatters
```python
file_path = event["tool_input"].get("file_path", "")
if file_path.endswith(".py"):
    subprocess.run(["black", file_path], timeout=30)
elif file_path.endswith(".ts"):
    subprocess.run(["npx", "prettier", "--write", file_path], timeout=30)
```

### CI/CD Triggers

**Pattern:** SessionEnd or Stop to trigger pipelines
```python
if task_completed_successfully(transcript):
    trigger_ci_pipeline(branch=get_current_branch())
```

---

## Underexplored Patterns

These patterns use less common events or techniques that most users don't know about.

### PreCompact: Preserve Critical Context

**Problem:** When context is compacted, important information can be lost.

**Solution:** PreCompact hook injects critical context into the compaction:
```python
# Gather critical context that must survive
critical = {
    "key_decisions": load_session_decisions(),
    "constraints": load_active_constraints(),
    "current_task": get_current_task_summary()
}
print(json.dumps(critical, indent=2))
```

**Use cases:**
- Preserve key architectural decisions
- Maintain constraint awareness across compaction
- Keep task context when context gets long

### SubagentStop: Validate Subagent Output

**Problem:** Subagents might return incomplete or incorrect results.

**Solution:** SubagentStop hook validates before results return to main thread:
```json
{
  "type": "prompt",
  "prompt": "Evaluate if this subagent completed its task. Input: $ARGUMENTS. Check if: 1) Task was fully addressed 2) No errors occurred 3) Output is actionable. Return {\"ok\": true} or {\"ok\": false, \"reason\": \"what's missing\"}."
}
```

**Use cases:**
- Ensure code review agents actually reviewed all files
- Verify research agents found relevant information
- Check that exploration agents covered required areas

### SubagentStart: Track Delegation Patterns

**Problem:** Want to understand when/why Claude delegates to subagents.

**Solution:** SubagentStart hook logs delegation:
```python
delegation = {
    "timestamp": datetime.now().isoformat(),
    "agent_type": event["agent_type"],
    "agent_id": event["agent_id"],
    "parent_context": get_recent_context(event["transcript_path"])
}
log_delegation(delegation)
```

### Input Transformation with updatedInput

**Problem:** Want to modify tool inputs without blocking.

**Solutions:**

**Add safety flags:**
```python
# Add --dry-run to dangerous commands
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {"command": command + " --dry-run"}
    }
}
```

**Normalize paths:**
```python
# Ensure absolute paths
file_path = event["tool_input"]["file_path"]
if not file_path.startswith("/"):
    abs_path = os.path.join(os.getcwd(), file_path)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {"file_path": abs_path}
        }
    }
```

**Inject defaults:**
```python
# Add timeout to commands that don't have one
if "timeout" not in event["tool_input"]:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {**event["tool_input"], "timeout": 60000}
        }
    }
```

### Cross-Event State Patterns

**Problem:** Hook needs information from an earlier event.

**Solution:** Use file-based state to communicate across hooks:

**SessionStart — initialize state:**
```python
state = {"session_start": datetime.now().isoformat(), "tools_used": []}
save_state(event["session_id"], state)
```

**PostToolUse — update state:**
```python
state = load_state(event["session_id"])
state["tools_used"].append(event["tool_name"])
save_state(event["session_id"], state)
```

**Stop — check state:**
```python
state = load_state(event["session_id"])
if "Write" in state["tools_used"] and "Bash" not in state["tools_used"]:
    # Files were written but tests weren't run
    output = {"decision": "block", "reason": "Files were modified but tests weren't run."}
```

### Prompt Hooks for Nuanced Judgment

**Problem:** Rule-based logic can't capture all edge cases.

**Solution:** Let Haiku make the judgment call:

**Security review:**
```json
{
  "type": "prompt",
  "prompt": "Review this bash command for security issues: $ARGUMENTS. Consider: injection risks, privilege escalation, data exposure. Respond {\"ok\": true} if safe, {\"ok\": false, \"reason\": \"specific concern\"} if risky."
}
```

**Completeness check:**
```json
{
  "type": "prompt",
  "prompt": "Has Claude completed the user's request? Context: $ARGUMENTS. Check if all requirements were addressed. Respond {\"ok\": true} to allow stopping, {\"ok\": false, \"reason\": \"what's missing\"} to continue."
}
```

**Code quality gate:**
```json
{
  "type": "prompt",
  "prompt": "Review this code change: $ARGUMENTS. Is it production-ready? Check for: error handling, edge cases, documentation. Respond with verdict."
}
```

### Setup Hooks for One-Time Operations

**Problem:** Some setup only needs to run once, not every session.

**Solution:** Setup hooks with `--init` or `--maintenance`:

```python
# Only runs with: claude --init
# Perfect for:
# - Installing dependencies
# - Running migrations
# - Generating config files
# - Downloading assets

if not dependencies_installed():
    subprocess.run(["npm", "install"])
if not migrations_current():
    subprocess.run(["npm", "run", "migrate"])
```

**Trigger:** `claude --init` or `claude --maintenance`

---

## Pattern Selection Guide

| Goal | First Choice | Alternative |
|------|--------------|-------------|
| Block dangerous commands | PreToolUse + exit 2 | PermissionRequest auto-deny |
| Log tool usage | PostToolUse | — |
| Inject context once | SessionStart | Setup |
| Inject context every prompt | UserPromptSubmit | — |
| Warn but don't block | PreToolUse + additionalContext | PreToolUse + permissionDecision: "ask" |
| Transform input | PreToolUse + updatedInput | — |
| Quality gate before done | Stop + decision: "block" | Prompt hook on Stop |
| Validate subagent output | SubagentStop | — |
| Preserve context in compact | PreCompact | — |
| Desktop notification | Notification | — |
| Judgment call (not rules) | Prompt hook | — |
| Track patterns across session | Cross-event state | — |
