---
id: skills-context-fork
topic: Skill Context Isolation
category: skills
tags: [context, fork, isolation, subagent]
requires: [skills-overview, skills-frontmatter]
related_to: [agents-overview]
official_docs: https://code.claude.com/en/skills
---

# Skill Context Isolation

By default, skills run in the main conversation context. Use `context: fork` to run in a separate subagent.

## Configuration

```yaml
---
name: code-analysis
description: Deep code analysis
context: fork
agent: Explore
---
```

## Fork Behavior

When `context: fork` is set:
1. Skill runs in a new subagent context
2. Main conversation context is not polluted
3. Skill can use different tool permissions
4. Results are summarized back to main context

## When to Fork

Fork when:
- Long-running analysis that shouldn't pollute main context
- Parallel execution of multiple skills
- Tasks that need different tool permissions
- Large file processing that would bloat context

Don't fork when:
- Quick, simple operations
- Interactive workflows requiring main context
- Skills that need to modify main conversation state

## Agent Types

| Agent | Model | Best For |
|-------|-------|----------|
| `Explore` | haiku | Read-only codebase exploration |
| `Plan` | sonnet | Architecture and planning |
| `general-purpose` | sonnet | Multi-step modifications |

## Key Points

- `context: fork` runs skill in separate subagent
- `agent` field specifies which subagent type
- Forked skills don't pollute main context
- Results summarized back to main conversation
