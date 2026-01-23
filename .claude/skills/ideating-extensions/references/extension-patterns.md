# Extension Pattern Guide

Reference for matching problems to Claude Code extension types.

## Problem Archetypes

| Archetype | Description | Best Fit |
|-----------|-------------|----------|
| **Enforcement** | Must happen every time, no discipline required | Hook |
| **Guidance** | Step-by-step process, explicit invocation | Skill |
| **Shortcut** | Quick action, few parameters | Command |
| **Delegation** | Complex analysis, many files, autonomous | Agent |
| **Integration** | External API, tool, or data source | MCP Server |
| **Bundle** | Multiple related extensions as a package | Plugin |

## Extension Type Capabilities

### Hooks
**What they do:** Run automatically before/after tool use or at session events.
**Good for:** Validation, enforcement, automatic checks, silent guards.
**Examples:** Block commits without tests, warn on protected branches, validate file formats.
**Constraints:** Must be fast (blocking), can't require user input during execution.

### Skills
**What they do:** Provide guided workflows invoked explicitly by user.
**Good for:** Multi-step processes, methodology enforcement, quality guidance.
**Examples:** TDD workflow, code review process, documentation standards.
**Constraints:** Require user to invoke, compete for context budget.

### Commands
**What they do:** Slash-invoked shortcuts with optional arguments.
**Good for:** Quick actions, parameterized operations, aliases.
**Examples:** `/commit`, `/review-pr 123`, `/format`.
**Constraints:** Should be simple; complex logic belongs in skills.

### Agents
**What they do:** Autonomous subprocesses that handle complex tasks.
**Good for:** Multi-file analysis, research, parallel work, context-heavy tasks.
**Examples:** Codebase exploration, PR review, test coverage analysis.
**Constraints:** Run separately, return summary only; can't edit in same session.

### MCP Servers
**What they do:** External tool integrations via Model Context Protocol.
**Good for:** APIs, databases, external services, custom tooling.
**Examples:** GitHub API, database queries, documentation fetching.
**Constraints:** Require server implementation, network access.

### Plugins
**What they do:** Package multiple extensions together for distribution.
**Good for:** Related functionality bundles, shareable extension sets.
**Examples:** Language-specific toolkits, domain-specific workflows.
**Constraints:** Packaging overhead, versioning concerns.

## Decision Heuristics

**"I keep forgetting to..."** → Hook
The problem is discipline. Automate it so forgetting isn't possible.

**"I need to follow a process..."** → Skill
The problem is consistency. Guide the workflow explicitly.

**"I want a quick way to..."** → Command
The problem is friction. Create a shortcut.

**"I need to analyze a lot of..."** → Agent
The problem is scale. Delegate to a subprocess.

**"I need to access external..."** → MCP Server
The problem is integration. Bridge to the external system.

**"I have several related..."** → Plugin
The problem is organization. Bundle them together.

## Tradeoffs by Type

| Type | Visibility | User Control | Complexity | Learning Curve |
|------|------------|--------------|------------|----------------|
| Hook | Low (silent) | Low (automatic) | Low | Low |
| Skill | High (explicit) | High (step-by-step) | Medium | Medium |
| Command | Medium (invoked) | Medium (parameterized) | Low | Low |
| Agent | Medium (delegated) | Medium (task-scoped) | High | Medium |
| MCP Server | Low (tool calls) | Medium (tool selection) | High | High |
| Plugin | Varies | Varies | High | Medium |

## Hybrid Patterns

Some problems benefit from multiple extension types working together:

**Hook + Skill:** Hook detects condition, suggests invoking skill for resolution.
Example: Hook warns "tests missing", suggests `/add-tests` skill.

**Skill + Agent:** Skill orchestrates workflow, delegates heavy analysis to agent.
Example: Code review skill delegates "find all usages" to exploration agent.

**Command + Skill:** Command is quick entry point, skill handles complex cases.
Example: `/commit` command for simple commits, `committing-changes` skill for complex.

**MCP Server + Skill:** MCP provides data, skill guides interpretation.
Example: Database MCP fetches schema, migration skill guides changes.
