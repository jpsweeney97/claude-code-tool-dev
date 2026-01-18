---
id: hooks-best-practices
topic: Hook Best Practices
category: hooks
tags: [best-practices, design, performance, patterns]
requires: [hooks-overview]
related_to: [hooks-anti-patterns, hooks-debugging, hooks-security, hooks-examples]
official_docs: https://code.claude.com/en/hooks
---

# Hook Best Practices

Design principles for writing effective hooks.

## Keep Hooks Fast

Hooks block execution. Target <1 second; never exceed timeout.

- PreToolUse hooks delay every matching tool call
- Broad matchers (`*`) multiply the performance impact
- Network calls need timeouts; prefer async patterns

## Fail Safe

If your hook errors (exit 1), the operation proceeds. Design for graceful degradation.

- Exit 1 is non-blocking — only exit 2 blocks
- Hooks shouldn't be single points of failure
- Log errors for debugging but don't crash the workflow

## Be Specific with Matchers

Broad matchers add latency to every tool call.

```json
// Avoid: runs on every tool
{ "matcher": "*" }

// Better: only runs on file writes
{ "matcher": "Write|Edit" }

// Best: only runs on specific MCP server
{ "matcher": "mcp__memory__.*" }
```

## Use stderr for Block Messages

At exit 2, stderr is shown to Claude. Make messages actionable.

```bash
# Bad: vague
echo "Blocked" >&2

# Good: actionable
echo "BLOCKED: Command contains 'rm -rf /'. Use a safer deletion pattern." >&2
```

## Don't Rely on State

Hooks run in parallel with no guaranteed order. Design for independent execution.

- Don't assume another hook ran first
- Don't share state between hooks
- Each hook should be self-contained

## Key Points

- Performance: <1s ideal, specific matchers
- Safety: fail open (exit 1), block explicitly (exit 2)
- Independence: no shared state, no ordering assumptions
- Clarity: actionable stderr messages when blocking
