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

## Giving Subagents Access to Skills

Subagents do not automatically inherit skills from the main conversation. To give a custom subagent access to specific skills, list them in the subagent's `skills` field:

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
description: Review code for quality and best practices
skills: pr-review, security-check
---
```

Listed skills are loaded into the subagent's context when it starts. If `skills` field is omitted, no skills are preloaded.

**Important**: Built-in agents (Explore, Plan, general-purpose) do not have access to your skills. Only custom subagents you define in `.claude/agents/` with an explicit `skills` field can use skills.

## Key Points

- `context: fork` runs skill in separate subagent
- `agent` field specifies which subagent type
- Forked skills don't pollute main context
- Results summarized back to main conversation
- Built-in agents cannot access skills; only custom subagents can
