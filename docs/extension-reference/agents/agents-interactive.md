---
id: agents-interactive
topic: Interactive Agent Management
category: agents
tags: [agents, commands, interactive, ui]
requires: [agents-overview]
related_to: [agents-frontmatter, agents-builtin]
official_docs: https://code.claude.com/en/sub-agents
---

# Interactive Agent Management

The `/agents` command provides an interactive interface for creating and managing agents.

## Command Overview

Run `/agents` to:
- View all available agents (built-in, user, project, plugin)
- Create new agents with guided setup or Claude generation
- Edit existing agent configuration and tool access
- Delete custom agents
- See which agents are active when duplicates exist

Plugin agents from installed plugins appear alongside your custom agents in this interface. See [plugin components reference](/en/plugins-reference#agents) for creating plugin agents.

## Creating Agents

### Step 1: Choose Scope

Select **Create new agent**, then choose scope:

| Scope | Location | When to Use |
|-------|----------|-------------|
| Project-level | `.claude/agents/` | Codebase-specific, version controlled |
| User-level | `~/.claude/agents/` | Personal, available in all projects |

### Step 2: Define Agent

Two options:

**Generate with Claude** — Describe what you want:
```
A code improvement agent that scans files and suggests improvements
for readability, performance, and best practices.
```

Claude generates the system prompt and configuration. Press `e` to edit in your editor.

**Write manually** — Create the file yourself (see agents-frontmatter).

### Step 3: Select Tools

Choose which tools the agent can access:
- **All tools** — Agent inherits all tools from main conversation
- **Read-only tools** — Agent cannot modify files
- **Custom selection** — Pick specific tools

### Step 4: Select Model

Choose the agent's model:
- **Sonnet** — Balanced capability and speed
- **Opus** — Most capable, higher cost
- **Haiku** — Fastest, most economical
- **Inherit** — Use main conversation's model

### Step 5: Choose Color

Pick a background color for the agent. Colors help identify which agent is running in the UI.

### Step 6: Save

Save the agent. It's available immediately (no restart needed).

## Testing Agents

After creating, test by asking Claude:

```
Use the code-improver agent to suggest improvements in this project
```

Claude delegates to your agent, which works independently and returns results.

## Managing Existing Agents

Use `/agents` to:
- **Edit** — Modify configuration, tools, or system prompt
- **Delete** — Remove custom agents (cannot delete built-ins or plugin agents)
- **View active** — See which agent wins when names conflict

## Key Points

- `/agents` command provides interactive creation and management
- "Generate with Claude" creates agent config from natural language
- Color selection helps identify agents in UI
- Agents are available immediately after save (no restart)
- Project agents go in `.claude/agents/`, user agents in `~/.claude/agents/`
