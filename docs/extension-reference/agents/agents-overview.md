---
id: agents-overview
topic: Subagents Overview
category: agents
tags: [agents, subagents, autonomous, task-tool]
related_to: [agents-frontmatter, agents-task-tool, skills-overview]
official_docs: https://code.claude.com/en/sub-agents
---

# Subagents Overview

Subagents are autonomous AI workers that run in separate conversation contexts. They're ideal for complex multi-step tasks, parallel work streams, and specialized operations.

## Purpose

- Complex multi-step tasks requiring separate context
- Parallel work streams
- Specialized autonomous workers
- Long-running background analysis

## Location

| Scope | Path |
|-------|------|
| Project | `.claude/agents/<name>.md` |
| User | `~/.claude/agents/<name>.md` |

User agents override project agents with the same name.

## When to Use

Use agents when:
- Task requires separate conversation context
- Long-running analysis that shouldn't pollute main context
- Parallel execution of independent tasks
- Specialized worker with different tool permissions

Use skills instead when:
- Task should stay in main context
- Interactive workflow with user
- Quick operation that doesn't need isolation

## Key Points

- Agents run in separate conversation contexts
- Invoked via Task tool, not slash commands
- Can be resumed to continue work
- Support 6 permission modes
