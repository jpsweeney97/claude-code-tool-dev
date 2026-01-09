---
id: agents-resumable
topic: Resumable Agents
category: agents
tags: [resume, continuation, context]
requires: [agents-overview, agents-task-tool]
related_to: [agents-permissions]
official_docs: https://code.claude.com/en/sub-agents
---

# Resumable Agents

Agents can be resumed to continue work with full context preserved.

## Resume Pattern

```typescript
// Initial invocation
Task(
  description: "Start code review",
  prompt: "Review the authentication module",
  subagent_type: "code-reviewer"
)
// Returns: { agentId: "abc123", ... }

// Resume later
Task(
  resume: "abc123",
  prompt: "Now also review the authorization module"
)
// Agent continues with full previous context
```

## Technical Details

| Aspect | Detail |
|--------|--------|
| Storage | Transcripts stored as `agent-{agentId}.jsonl` |
| Recording | Disabled during resume |
| Sync/Async | Works with both sync and async agents |

## When to Resume

Resume agents when:
- Continuing multi-phase work
- Adding follow-up tasks
- Correcting or refining output
- Need previous context preserved

Don't resume when:
- Starting fresh work
- Previous context is irrelevant
- Agent state is corrupted

## Key Points

- Agents return `agentId` for resume
- Resume preserves full conversation context
- Transcripts stored in JSONL format
- Works with sync and background agents
