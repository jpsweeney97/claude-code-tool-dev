---
id: agents-patterns
topic: Agent Usage Patterns
category: agents
tags: [patterns, best-practices, context-management]
requires: [agents-overview, agents-task-tool]
related_to: [agents-resumable, skills-overview]
official_docs: https://code.claude.com/en/sub-agents
---

# Agent Usage Patterns

Common patterns for effective agent usage and when to choose agents vs main conversation.

## Automatic Delegation

Claude automatically delegates tasks based on:
- Task description in your request
- `description` field in agent configurations
- Current conversation context

To encourage proactive delegation, include phrases like "use proactively" in your agent's description:

```yaml
description: Code review specialist. Use proactively after writing or modifying code.
```

You can also request a specific agent explicitly:

```
Use the test-runner agent to fix failing tests
Have the code-reviewer agent look at my recent changes
```

## Pattern: Isolate High-Volume Operations

Delegate operations that produce large output to keep your main context clean.

```
Use a subagent to run the test suite and report only the failing tests with their error messages
```

Good for:
- Running test suites
- Fetching documentation
- Processing log files
- Large codebase searches

The verbose output stays in the agent's context; only the summary returns.

## Pattern: Parallel Research

Spawn multiple agents to investigate independent areas simultaneously.

```
Research the authentication, database, and API modules in parallel using separate subagents
```

Each agent explores its area independently, then Claude synthesizes findings. Works best when research paths don't depend on each other.

**Warning:** When agents complete, results return to main conversation. Many agents returning detailed results consume significant context.

## Pattern: Chain Agents

Use agents in sequence for multi-step workflows.

```
Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them
```

Each agent completes its task and returns results to Claude, which passes relevant context to the next agent.

## When to Use Agents vs Main Conversation

### Use Main Conversation

- Task needs frequent back-and-forth or iterative refinement
- Multiple phases share significant context (planning → implementation → testing)
- Making a quick, targeted change
- Latency matters (agents start fresh and may need time to gather context)

### Use Agents

- Task produces verbose output you don't need in main context
- You want to enforce specific tool restrictions or permissions
- Work is self-contained and can return a summary
- Parallel execution of independent tasks needed

### Consider Skills Instead

When you want reusable prompts or workflows that run in the main conversation context rather than isolated agent context.

## Best Practices

- **Design focused agents** — Each agent should excel at one specific task
- **Write detailed descriptions** — Claude uses the description to decide when to delegate
- **Limit tool access** — Grant only necessary permissions for security and focus
- **Check into version control** — Share project agents with your team in `.claude/agents/`

## Key Points

- Automatic delegation based on task + description + context
- "Use proactively" in description encourages automatic delegation
- Isolate verbose operations to preserve main context
- Parallel agents work best for independent investigations
- Chain agents for multi-step workflows
- Agents add latency (fresh context gathering)
- Skills stay in main context; agents are isolated
