---
id: agents-getting-started
topic: Creating Your First Agent
category: agents
tags: [tutorial, getting-started, example]
related_to: [agents-overview, agents-task-tool, agents-examples]
official_docs: https://code.claude.com/en/agents
---

# Creating Your First Agent

This tutorial creates a project agent that explores codebases to answer architectural questions.

## Prerequisites

- Claude Code installed and configured
- A codebase to explore

## Step 1: Check Available Agents

Before creating an agent, see what agents Claude already has access to:

```
What agents are available?
```

Claude lists any currently loaded agents from plugins or your organization.

## Step 2: Create the Agent Directory

Create a directory for the agent in your project:

```bash
mkdir -p .claude/agents
```

For personal agents available across projects, use `~/.claude/agents/` instead.

## Step 3: Write the Agent Definition

Create `.claude/agents/architecture-explorer.md`:

```markdown
---
name: architecture-explorer
description: Explores codebase architecture. Use for questions about structure, patterns, dependencies, or "how is this organized?"
tools: [Read, Glob, Grep, LS]
---

When exploring architecture:

1. **Map the structure**: Use Glob to find key directories and file patterns
2. **Identify entry points**: Find main files, index files, configuration
3. **Trace dependencies**: Use Grep to follow imports and references
4. **Summarize patterns**: Note naming conventions, file organization, layering

Report findings as:
- Directory structure overview
- Key architectural decisions observed
- Notable patterns or conventions
- Potential areas of concern
```

## Step 4: Verify the Agent Loads

Agents load automatically. Verify:

```
What agents are available?
```

You should see `architecture-explorer` with its description.

## Step 5: Test the Agent

Ask a question that matches the agent's description:

```
How is this codebase organized?
```

Claude should invoke the architecture-explorer agent via the Task tool.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not listed | Check path: `.claude/agents/architecture-explorer.md` |
| Agent doesn't trigger | Make description more specific |
| Permission errors | Verify `tools` list includes needed tools |

See [agents-troubleshooting](agents-troubleshooting.md) for detailed diagnostics.

## Next Steps

- [agents-task-tool](agents-task-tool.md) — How Claude invokes agents
- [agents-examples](agents-examples.md) — More agent patterns
- [agents-tools](agents-tools.md) — Available tools for agents

## Key Points

- Agents live in `.claude/agents/<name>.md` (project) or `~/.claude/agents/` (personal)
- `name`, `description`, and `tools` are key frontmatter fields
- Description quality determines when Claude delegates to the agent
- Changes take effect immediately
