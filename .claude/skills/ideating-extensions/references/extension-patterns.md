# Extension Pattern Guide

Reference for matching problems to Claude Code extension types.

## Quick Reference

| Problem Pattern | Extension | Core Value |
|-----------------|-----------|------------|
| Deterministic control (must always happen) | Hook | Turns suggestions into app-level code |
| Extend Claude's capabilities | Skill | Adds to Claude's toolkit |
| Context isolation / parallel work | Agent | Separate context window, returns summary |
| External tools, data, APIs | MCP Server | Standardized integration protocol |
| Share across projects/teams | Plugin | Distributable bundles |

**Note:** Commands have been merged into Skills. Use Skills for new work.

## Extension Types

### Hooks

> "Hooks provide deterministic control over Claude Code's behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them."

**The key distinction:** By encoding rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time.

**Problem patterns:**
- Policy must apply unconditionally (not "Claude should try to...")
- Validation/enforcement that Claude can't maintain across sessions
- Automatic formatting, logging, notifications

**Capabilities:**
- 13 event types:
  - Session lifecycle: SessionStart, SessionEnd
  - User input: UserPromptSubmit
  - Tool events: PreToolUse, PostToolUse (success), PostToolUseFailure (failure), PermissionRequest
  - Subagent events: SubagentStart, SubagentStop
  - Other: Stop, PreCompact, Setup, Notification
- Can block, warn, modify inputs (`updatedInput`), inject context (`additionalContext`)
- Two hook types:
  - **Bash command** (`type: "command"`): Deterministic rules, fast local execution
  - **Prompt-based** (`type: "prompt"`): Context-aware decisions via LLM, slower but more flexible

**Constraints:**
- Should be fast, especially SessionStart
- Execute automatically — consider security implications

**Examples:** Auto-format files after edit, block modifications to .env, log all bash commands, custom notifications.

---

### Skills

> "Skills extend what Claude can do. Create a SKILL.md file with instructions, and Claude adds it to its toolkit."

**Two types of content:**
- **Reference content:** Conventions, patterns, style guides, domain knowledge — runs inline
- **Task content:** Step-by-step instructions for specific actions (deployments, commits, code generation)

**Problem patterns:**
- Claude needs reusable instructions (knowledge OR tasks)
- Methodology should be consistent across invocations
- Capability requires bundled scripts or templates

**Capabilities:**
- Invoked by user (`/skill-name`) OR Claude (configurable via `disable-model-invocation` frontmatter)
- Can include supporting files: templates, examples, executable scripts, reference docs
- Can bundle and run scripts in any language — enables capabilities beyond a single prompt (e.g., generate interactive HTML visualizations)
- Supports dynamic context injection (`!`command``) — run shell commands before Claude sees content
- Can run in isolated subagent context (`context: fork`) with a specified agent type

**Constraints:**
- Skill descriptions compete for 15,000 char context budget
- Not automatic — requires invocation (use hooks for unconditional execution)

**Examples:** TDD workflow, code review process, API design patterns, codebase visualization scripts.

---

### Agents (Subagents)

> "Subagents are specialized AI assistants that handle specific types of tasks. Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions."

**Five value propositions:**
1. **Preserve context** — keep verbose output out of main conversation
2. **Enforce constraints** — limit which tools a subagent can use
3. **Reuse configurations** — user-level subagents across projects
4. **Specialize behavior** — focused system prompts for domains
5. **Control costs** — route to cheaper models (Haiku)

**Problem patterns:**
- Task produces too much output for main context
- Need parallel independent research streams
- Want tool restrictions for specific tasks
- Work is self-contained and can return a summary

**Capabilities:**
- Custom system prompt, tool allowlist/denylist
- Model selection (sonnet, opus, haiku, inherit)
- Foreground (blocking) or background (concurrent) execution
- Resumable with full context preserved
- Can preload skills into subagent context (`skills` field)
- Can have Edit/Write tools — only the built-in Explore agent is read-only by design

**Built-in agents:**
- **Explore**: Haiku, read-only, fast codebase search
- **Plan**: Read-only research for plan mode
- **general-purpose**: All tools, complex multi-step tasks

**Constraints:**
- Cannot spawn nested subagents (chain from main conversation instead)
- Latency: subagents start fresh and gather context

**Examples:** Test runner (isolates verbose output), parallel codebase exploration, code review with restricted tools, domain-specific reviewer with preloaded conventions.

---

### MCP Servers

> "Claude Code can connect to hundreds of external tools and data sources through the Model Context Protocol (MCP), an open source standard for AI-tool integrations. MCP servers give Claude Code access to your tools, databases, and APIs."

**Problem patterns:**
- Claude needs data from external systems
- Integration with issue trackers, monitoring, databases, design tools
- Cross-system workflows (JIRA → GitHub → Sentry → Slack)

**Capabilities:**
- Provides three types of capabilities:
  - **Tools**: Functions Claude can call to interact with external systems
  - **Resources**: Data referenced via @ mentions (e.g., `@github:issue://123`)
  - **Prompts**: Pre-defined prompts that become `/mcp__server__prompt` commands
- Three transports: HTTP (recommended for remote), SSE (deprecated), stdio (local processes)
- Can be bundled in plugins for easier distribution
- Supports OAuth 2.0 for authenticated services

**Constraints:**
- Requires server implementation (use MCP SDK)
- Remote servers need network access; stdio servers run locally

**Examples:** GitHub API, PostgreSQL queries, Sentry monitoring, Figma designs, Slack messages.

---

### Plugins

> "Plugins let you extend Claude Code with custom functionality that can be shared across projects and teams."

**Problem patterns:**
- Need same extensions across multiple projects
- Want to share with team or community
- Distributing through a marketplace
- Bundling related extensions together

**Capabilities:**
- Contains skills, agents, hooks, MCP servers, LSP servers
- **LSP servers**: Provide code intelligence (go to definition, find references, diagnostics) — Claude sees errors instantly after edits
- Namespace prevents conflicts (`/plugin:skill`)
- Semantic versioning for updates
- Marketplace distribution via `/plugin install`

**Constraints:**
- Skills are always namespaced (can't have short names like `/hello`)
- Packaging overhead vs standalone `.claude/` configuration

**When to use standalone instead:**
- Personal workflows, project-specific customizations
- Quick experiments before packaging
- Want short skill names

**Examples:** Language-specific toolkits, team workflow bundles, community extension packs.

## Decision Heuristics

| Signal | Extension | Why |
|--------|-----------|-----|
| "This must happen every time" | Hook | Deterministic, not LLM-dependent |
| "Claude should know/do this" | Skill | Extends toolkit with reusable instructions |
| "Too much output for main context" | Agent | Isolated context, returns summary |
| "Route simple tasks to cheaper model" | Agent | Model selection (Haiku) reduces cost |
| "Need data from external system" | MCP Server | Standardized integration |
| "Claude needs code intelligence" | Plugin (LSP) | Real-time diagnostics, go to definition |
| "Share across projects/teams" | Plugin | Distributable bundle |

## Hybrid Patterns

Some problems benefit from multiple extension types:

| Combination | Pattern | Example |
|-------------|---------|---------|
| Hook + Skill | Hook detects, skill resolves | Hook warns "tests missing", suggests `/add-tests` skill |
| Skill + Agent | Skill orchestrates, agent analyzes | Code review skill delegates "find all usages" to explorer |
| MCP + Skill | MCP provides data, skill guides use | Database MCP fetches schema, migration skill guides changes |
| Plugin + MCP | Plugin bundles MCP for distribution | GitHub plugin includes pre-configured MCP server |

## Tradeoffs

| Type | Invocation | Context Impact | Implementation |
|------|------------|----------------|----------------|
| Hook | Automatic (event-driven) | Minimal | Bash/Python script |
| Skill | User or Claude | Competes for budget | Markdown + optional files |
| Agent | Delegated by Claude | Isolated (separate window) | Markdown definition |
| MCP Server | Tool calls | Minimal | Server implementation |
| Plugin | Install command | Varies by contents | Package with manifest |
