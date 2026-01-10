---
id: agents-overview
topic: Subagents Overview
category: agents
tags: [agents, subagents, autonomous, task-tool]
related_to: [agents-frontmatter, agents-task-tool, agents-patterns, skills-overview]
official_docs: https://code.claude.com/en/sub-agents
---

# Subagents Overview

Subagents are autonomous AI workers that run in separate conversation contexts. They're ideal for complex multi-step tasks, parallel work streams, and specialized operations.

## Purpose

- Complex multi-step tasks requiring separate context
- Parallel work streams
- Specialized autonomous workers
- Long-running background analysis
- Control costs by routing tasks to faster, cheaper models (e.g., Haiku for exploration)

## Location

| Priority | Scope | Path |
|----------|-------|------|
| 1 (highest) | Session | `--agents` CLI flag (JSON) |
| 2 | Project | `.claude/agents/<name>.md` |
| 3 | User | `~/.claude/agents/<name>.md` |
| 4 (lowest) | Plugin | Plugin's `agents/` directory |

When multiple agents share the same name, higher priority wins. Use `/agents` command to see which agent is active.

Agents load at session start. If you create an agent by adding a file, restart your session or use `/agents` to load it immediately.

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
- Support 5 permission modes
- **Cannot spawn other agents** — use skills or chain from main conversation

## See Also

- [Agent SDK](/en/agent-sdk/subagents) — programmatic agent usage
- [Plugin components](/en/plugins-reference#agents) — creating plugin agents
