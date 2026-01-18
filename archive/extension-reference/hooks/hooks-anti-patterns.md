---
id: hooks-anti-patterns
topic: Hook Anti-Patterns
category: hooks
tags: [anti-patterns, mistakes, debugging, troubleshooting]
requires: [hooks-overview, hooks-exit-codes]
related_to: [hooks-best-practices, hooks-debugging]
official_docs: https://code.claude.com/en/hooks
---

# Hook Anti-Patterns

Common mistakes when writing hooks and how to fix them.

## Exit Code Mistakes

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Using exit 1 to block | Exit 1 is non-blocking | Use exit 2 to block |
| JSON in stdout at exit 2 | Ignored; only stderr used | Print error to stderr |

```bash
# Wrong: exit 1 doesn't block
echo "Error" >&2
exit 1  # Operation proceeds anyway

# Right: exit 2 blocks
echo "BLOCKED: reason" >&2
exit 2
```

## Input/Output Mistakes

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Not reading stdin | Miss event data | Always `json.load(sys.stdin)` |
| Ignoring tool_input | Can't validate actual command | Parse and check tool_input |

```python
# Wrong: ignoring stdin
def main():
    # No input read - hook has no context
    sys.exit(0)

# Right: always read stdin
def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    # Now you can validate
```

## Performance Mistakes

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Sync network calls without timeout | Hook hangs indefinitely | Add timeouts; use async |
| Broad matcher on slow hook | Every tool call slows down | Narrow matcher or optimize |

```json
// Wrong: runs slow hook on every tool
{
  "matcher": "*",
  "hooks": [{"command": "./slow-validator.sh"}]
}

// Right: only run on relevant tools
{
  "matcher": "Bash",
  "hooks": [{"command": "./bash-validator.sh"}]
}
```

## Timing Mistakes

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Modifying files during PreToolUse | Race conditions with tool | Log only; modify in PostToolUse |
| Assuming hook order | Hooks run in parallel | Design for independent execution |

## Stop Hook Mistakes

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Not checking `stop_hook_active` | Infinite loop when blocking Stop | Check flag to prevent recursion |

```python
def main():
    event = json.load(sys.stdin)

    # Wrong: always block Stop
    if should_continue():
        print("Keep working", file=sys.stderr)
        sys.exit(2)  # Could loop forever

    # Right: check the flag
    if event.get("stop_hook_active"):
        sys.exit(0)  # Already continuing from a Stop hook

    if should_continue():
        print("Keep working", file=sys.stderr)
        sys.exit(2)
```

## Key Points

- Exit 2 blocks, exit 1 does NOT
- Always read stdin for event context
- Use specific matchers for slow hooks
- Check `stop_hook_active` in Stop hooks
- Don't modify files in PreToolUse
