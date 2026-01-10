---
id: hooks-debugging
topic: Hook Debugging
category: hooks
tags: [debugging, troubleshooting, errors, logs]
requires: [hooks-overview, hooks-configuration]
related_to: [hooks-exit-codes, hooks-environment]
official_docs: https://code.claude.com/en/hooks
---

# Hook Debugging

Troubleshooting hooks that don't work as expected.

## Basic Troubleshooting

| Step | Action |
|------|--------|
| 1. Check configuration | Run `/hooks` to see registered hooks |
| 2. Verify syntax | Ensure JSON settings are valid |
| 3. Test commands | Run hook commands manually first |
| 4. Check permissions | Make sure scripts are executable |
| 5. Review logs | Use `claude --debug` for details |

## Common Issues

### Quotes Not Escaped

```json
// WRONG
{ "command": "echo "hello"" }

// CORRECT
{ "command": "echo \"hello\"" }
```

### Wrong Matcher

```json
// WRONG - case sensitive
{ "matcher": "bash" }

// CORRECT
{ "matcher": "Bash" }
```

### Command Not Found

```json
// WRONG - relative path
{ "command": "validate.sh" }

// CORRECT - absolute path
{ "command": "/home/user/.claude/hooks/validate.sh" }

// CORRECT - using project dir
{ "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate.sh" }
```

### Script Not Executable

```bash
# Make script executable
chmod +x ~/.claude/hooks/my-hook.sh
```

## Debug Mode

Run Claude Code with `--debug` to see hook execution:

```bash
claude --debug
```

### Debug Output Example

```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: ./validate.sh with timeout 60000ms
[DEBUG] Hook command completed with status 0: Success
```

## Verbose Mode

Press `Ctrl+O` during a session to toggle verbose mode. Shows:

- Which hook is running
- Command being executed
- Success/failure status
- Output or error messages

**Note:** PreToolUse/PermissionRequest/PostToolUse/Stop/SubagentStop output appears in verbose mode. UserPromptSubmit/SessionStart stdout is added as context for Claude instead.

## Advanced Debugging

| Technique | When to Use |
|-----------|-------------|
| Inspect execution | Use `claude --debug` for detailed logs |
| Validate JSON | Test hook input/output with external tools |
| Check environment | Verify environment variables are set |
| Test edge cases | Try unusual file paths or inputs |
| Monitor resources | Check for resource exhaustion |
| Structured logging | Implement logging in hook scripts |

## Logging in Hook Scripts

```bash
#!/bin/bash
# Add logging to debug hooks

log_file="$HOME/.claude/hook-debug.log"

echo "[$(date)] Hook triggered" >> "$log_file"
echo "  TOOL_INPUT: $TOOL_INPUT" >> "$log_file"
echo "  PWD: $PWD" >> "$log_file"

# Your hook logic here

echo "  Exit code: $?" >> "$log_file"
```

## Key Points

- Use `/hooks` to verify hook registration
- Use `claude --debug` for execution details
- Use `Ctrl+O` for verbose mode during session
- Test hook commands manually before configuring
- Always use absolute paths for scripts
