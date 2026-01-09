# Claude Code Extension System

> Comprehensive reference for extending Claude Code with commands, skills, agents, hooks, MCP servers, LSP servers, and plugins.

**Official Documentation**: [code.claude.com/docs](https://code.claude.com/docs/llms.txt)

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference](#quick-reference)
3. [Commands](#commands)
4. [Skills](#skills)
5. [Subagents](#subagents)
6. [Hooks](#hooks)
7. [MCP Servers](#mcp-servers)
8. [LSP Servers](#lsp-servers)
9. [Plugins](#plugins)
10. [Marketplaces](#marketplaces)
11. [Settings & Configuration](#settings--configuration)
12. [Security & Managed Deployment](#security--managed-deployment)
13. [Appendices](#appendices)

---

## Overview

The Claude Code extension system provides a layered architecture for customizing and extending Claude Code's capabilities. Extensions range from simple prompt templates (commands) to full-featured autonomous agents and external tool integrations.

### Design Philosophy

**Progressive Complexity**: Start simple, grow as needed. Commands are one-line prompt templates. Skills add structure and verification. Plugins bundle everything for distribution.

**Composability**: Extensions build on each other. Plugins bundle skills, commands, agents, hooks, and servers. Skills can define component-scoped hooks. Agents can load skills.

**Fail-Safe Defaults**: Hooks fail open (exit code 1 proceeds). Deny rules always override allow rules. Managed settings take precedence over everything.

### When to Use Each Extension Type

```
Need to extend Claude Code?
│
├─ Simple prompt injection? ──────────────────────► Command
│   (no logic, just template)
│
├─ Complex workflow with verification? ───────────► Skill
│   (conditional logic, multi-step, quality gates)
│
├─ Autonomous background task? ───────────────────► Subagent
│   (separate context, parallel work)
│
├─ React to events automatically? ────────────────► Hook
│   (validate, log, transform, block)
│
├─ Integrate external tools/APIs? ────────────────► MCP Server
│   (databases, services, custom tools)
│
├─ Add code intelligence? ────────────────────────► LSP Server
│   (diagnostics, go-to-definition, types)
│
└─ Distribute to others? ─────────────────────────► Plugin
    (bundle any of the above)
```

---

## Quick Reference

### Extension Type Comparison

| Extension | Complexity | Isolation | Invocation | Event-Driven | Bundleable |
|-----------|------------|-----------|------------|--------------|------------|
| **Commands** | Lowest | None | `/command` | No | Yes |
| **Skills** | Medium | Optional fork | `/skill` or auto | No | Yes |
| **Subagents** | Medium-High | Full context | Task tool | No | Yes |
| **Hooks** | Medium | Process-level | Automatic | Yes | Yes |
| **MCP Servers** | High | Separate process | Tool calls | No | Yes |
| **LSP Servers** | High | Separate process | Automatic | No | Yes (plugins only) |
| **Plugins** | Highest | N/A (container) | Mixed | Mixed | Root |

### File Locations

| Extension | Project Scope | User Scope |
|-----------|---------------|------------|
| Commands | `.claude/commands/` | `~/.claude/commands/` |
| Skills | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` |
| Subagents | `.claude/agents/` | `~/.claude/agents/` |
| Hooks | `.claude/settings.json` | `~/.claude/settings.json` |
| MCP Servers | `.mcp.json` | `~/.claude.json` |
| Plugins | N/A | `~/.claude/plugins/` |
| Settings | `.claude/settings.json` | `~/.claude/settings.json` |
| CLAUDE.md | `CLAUDE.md` or `.claude/CLAUDE.md` | `~/.claude/CLAUDE.md` |

### Precedence Hierarchy

Settings and configurations follow this precedence (highest to lowest):

1. **Managed** — System-level `managed-settings.json` (cannot be overridden)
2. **Command line** — Flags passed to `claude` command
3. **Local** — `.claude/settings.local.json` (not committed)
4. **Project** — `.claude/settings.json` (shared with team)
5. **User** — `~/.claude/settings.json` (personal defaults)

**Deny always wins**: If any level denies a permission, it's blocked regardless of allow rules elsewhere.

---

## Commands

**Official Docs**: [code.claude.com/en/slash-commands](https://code.claude.com/en/slash-commands)

Commands are the simplest extension type—markdown files that inject prompts into the conversation. They're ideal for repetitive prompts, standardized workflows, and team conventions.

### Location

- **Project**: `.claude/commands/<name>.md`
- **User**: `~/.claude/commands/<name>.md`

User commands override project commands with the same name.

### Frontmatter Schema

```yaml
---
# Required: Shown in slash menu and Skill tool
description: Brief description of what this command does

# Optional: Hint shown to user for expected arguments
argument-hint: <file> [options]

# Optional: Override model for this command
model: claude-sonnet-4-20250514

# Optional: Tools this command is allowed to use
allowed-tools: Read, Glob, Grep, Bash

# Optional: Component-scoped hooks
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh "$TOOL_INPUT"
---

Command content here. This is injected into the conversation.
```

### Argument Substitution

| Pattern | Description | Example |
|---------|-------------|---------|
| `$ARGUMENTS` | All arguments as single string | `Review $ARGUMENTS` |
| `$1`, `$2`, etc. | Individual positional arguments | `Compare $1 with $2` |

### Dynamic Content

**Bash execution** — Use backticks with `!` prefix:

```markdown
Current branch: `!git branch --show-current`
Recent commits: `!git log --oneline -5`
```

**File references** — Include file contents:

```markdown
Review this file: @src/main.ts

Consider these patterns: @src/patterns/
```

### Example: Code Review Command

```markdown
---
description: Perform a thorough code review
argument-hint: <file-or-directory>
allowed-tools: Read, Glob, Grep
---

Review the following code for:
- Potential bugs and edge cases
- Security vulnerabilities
- Performance issues
- Code style and readability

Files to review: $ARGUMENTS

Use the project's existing patterns as reference.
```

### When to Use Commands vs Skills

| Use Commands When | Use Skills When |
|-------------------|-----------------|
| Simple prompt injection | Complex multi-step workflow |
| No conditional logic needed | "If X then Y otherwise Z" logic |
| One-shot execution | Verification and quality gates |
| Quick team standardization | Reusable across projects |

### Built-in Commands

Claude Code includes 54+ built-in commands. Key ones:

| Command | Purpose |
|---------|---------|
| `/help` | Show available commands |
| `/config` | Open settings interface |
| `/model` | Change model |
| `/mcp` | Manage MCP connections |
| `/plugin` | Manage plugins |
| `/agents` | Manage subagents |
| `/hooks` | Manage hooks |
| `/compact` | Compress conversation context |
| `/clear` | Clear conversation |

---

## Skills

**Official Docs**: [code.claude.com/en/skills](https://code.claude.com/en/skills)

Skills are structured workflows with verification steps. Unlike commands (simple prompt templates), skills guide Claude through complex procedures with decision points, quality gates, and explicit success criteria.

### Location

```
.claude/skills/<skill-name>/
└── SKILL.md           # Required: Main skill definition
└── references/        # Optional: Deep documentation
└── scripts/           # Optional: Automation (stdlib only)
└── templates/         # Optional: Output templates
└── assets/            # Optional: Images, prompts
```

User location: `~/.claude/skills/<skill-name>/SKILL.md`

### Frontmatter Schema

```yaml
---
# Required
name: skill-name                    # Kebab-case identifier
description: One-line description   # Shown in slash menu, used for auto-discovery

# Optional metadata
license: MIT
metadata:
  version: "1.0.0"
  model: claude-opus-4-5-20251101   # Recommended model
  timelessness_score: 8             # Quality indicator 1-10

# Visibility controls
user-invocable: true                # Show in slash menu (default: true)
disable-model-invocation: false     # Prevent Skill tool from invoking (default: false)

# Tool restrictions
allowed-tools: Read, Glob, Grep, Bash, Write, Edit

# Context isolation
context: fork                       # Run in separate subagent context
agent: Explore                      # Which subagent type to use when forked

# Component-scoped hooks
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
  PostToolUse:
    - matcher: Write|Edit
      hooks:
        - type: command
          command: ./format.sh "$TOOL_INPUT"
---
```

### Invocation Paths

Skills can be invoked three ways:

1. **Manual**: User types `/skill-name` or `/skill-name args`
2. **Skill tool**: Claude calls `Skill(skill: "skill-name", args: "...")`
3. **Auto-discovery**: Claude matches task to skill description

**Visibility matrix:**

| Setting | Slash Menu | Skill Tool | Auto-discovery |
|---------|------------|------------|----------------|
| Default | ✓ | ✓ | ✓ |
| `user-invocable: false` | ✗ | ✓ | ✓ |
| `disable-model-invocation: true` | ✓ | ✗ | ✓ |

### Context Isolation

By default, skills run in the main conversation context. Use `context: fork` to run in a separate subagent:

```yaml
---
name: code-analysis
description: Deep code analysis
context: fork
agent: Explore
---
```

**When to fork:**
- Long-running analysis that shouldn't pollute main context
- Parallel execution of multiple skills
- Tasks that need different tool permissions

### Mandatory Content Sections

Well-structured skills include these 8 sections:

1. **When to use** — Clear triggering conditions
2. **When NOT to use** — Explicit exclusions
3. **Inputs** — Required and optional parameters
4. **Outputs** — What the skill produces
5. **Procedure** — Step-by-step instructions
6. **Decision points** — Branching logic
7. **Verification** — Objective success criteria
8. **Troubleshooting** — Common issues and fixes

### Risk Tiering

| Risk Level | Requirements | Examples |
|------------|--------------|----------|
| **Low** | Basic verification | Code formatting, documentation |
| **Medium** | Multiple checks, rollback plan | Refactoring, migrations |
| **High** | Mandatory confirmation, dry-run | Deployments, data changes |

### Example: Database Migration Skill

```yaml
---
name: database-migration
description: Safely execute database migrations with rollback
metadata:
  version: "1.0.0"
  timelessness_score: 7
allowed-tools: Read, Bash, Write
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: |
            if echo "$TOOL_INPUT" | grep -q "DROP\|TRUNCATE\|DELETE"; then
              echo "BLOCKED: Destructive SQL detected" >&2
              exit 2
            fi
---

# Database Migration

## When to Use
- Applying schema changes to development or staging databases
- Running migrations generated by ORM tools

## When NOT to Use
- Production databases (require manual approval)
- Migrations involving data loss without explicit backup

## Inputs
- Migration files or ORM commands
- Target database connection (from environment)

## Procedure

### 1. Pre-flight Checks
1. Verify database connection
2. Check current migration state
3. Backup affected tables

### 2. Execute Migration
1. Run in transaction if supported
2. Apply changes incrementally
3. Verify each step

### 3. Verification
1. Run schema diff
2. Execute smoke tests
3. Check row counts

## Decision Points

If migration fails:
1. Rollback transaction
2. Report specific error
3. Do NOT retry automatically

## Verification Criteria
- [ ] Migration applied without errors
- [ ] Schema matches expected state
- [ ] Smoke tests pass
- [ ] No data loss detected

## Troubleshooting

**Connection refused**: Check DATABASE_URL environment variable
**Lock timeout**: Another process may hold table locks
```

### Skill Tool Mechanics

The Skill tool is how Claude programmatically invokes skills:

```typescript
Skill(skill: "skill-name", args: "optional arguments")
```

- **Lazy loading**: Only name + description loaded at startup
- **Full load**: Complete SKILL.md loaded when skill is activated
- **Character budget**: Default 15,000 chars for metadata (configurable via `SLASH_COMMAND_TOOL_CHAR_BUDGET`)

---

## Subagents

**Official Docs**: [code.claude.com/en/sub-agents](https://code.claude.com/en/sub-agents)

Subagents are autonomous AI workers that run in separate conversation contexts. They're ideal for complex multi-step tasks, parallel work streams, and specialized operations.

### Location

- **Project**: `.claude/agents/<name>.md`
- **User**: `~/.claude/agents/<name>.md`

### Frontmatter Schema

```yaml
---
# Required
description: What this agent does (shown in Task tool)

# Agent behavior
prompt: |
  You are a specialized agent for...

  Your responsibilities:
  - Task 1
  - Task 2

# Tool access
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit

# Model selection
model: sonnet  # sonnet, opus, or haiku

# Skills to auto-load
skills:
  - sql-analysis
  - chart-generation

# Permission behavior
permissionMode: acceptEdits  # See permission modes table

# Component-scoped hooks (no `once: true` support)
hooks:
  PostToolUse:
    - matcher: Write|Edit
      hooks:
        - type: command
          command: ./validate-output.sh
---

Additional context and instructions for the agent...
```

### Built-in Agent Types

| Type | Model | Tools | Use Case |
|------|-------|-------|----------|
| `general-purpose` | sonnet | All | Multi-step modification tasks |
| `Plan` | sonnet | Read, Glob, Grep, Bash | Plan mode architecture |
| `Explore` | haiku | Glob, Grep, Read, Bash (read-only) | Codebase exploration |

**Disabling built-ins**: Add to permissions deny array:
```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(Plan)"]
  }
}
```

### Task Tool Invocation

Agents are invoked via the Task tool:

```typescript
Task(
  description: "Analyze authentication flow",
  prompt: "Trace the authentication flow from login to session creation...",
  subagent_type: "security-analyzer",  // Custom or built-in
  model: "opus",                        // Optional override
  run_in_background: true              // Optional async execution
)
```

### Resumable Agents

Agents can be resumed to continue work with full context:

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

**Technical details:**
- Transcripts stored as `agent-{agentId}.jsonl`
- Recording disabled during resume
- Works with both sync and async agents

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Prompt user on first use of each tool |
| `acceptEdits` | Auto-accept file edits (Read, Write, Edit) |
| `plan` | Analyze only, no modifications |
| `dontAsk` | Auto-deny unless pre-approved in settings |
| `bypassPermissions` | Skip all permission prompts |
| `ignore` | No permissions enforced |

### CLI-Based Agent Definition

Define agents inline via command line:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior engineer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  },
  "test-writer": {
    "description": "Test generation specialist",
    "prompt": "You write comprehensive tests...",
    "tools": ["Read", "Write", "Bash"],
    "model": "haiku"
  }
}'
```

### Example: Security Analyzer Agent

```yaml
---
description: Analyze code for security vulnerabilities
prompt: |
  You are a security-focused code reviewer. Your job is to:

  1. Identify potential security vulnerabilities
  2. Check for OWASP Top 10 issues
  3. Review authentication and authorization logic
  4. Check for injection vulnerabilities
  5. Verify input validation

  Be thorough but avoid false positives. Cite specific line numbers.

tools:
  - Read
  - Glob
  - Grep

model: opus

permissionMode: plan

hooks:
  PostToolUse:
    - matcher: Read
      hooks:
        - type: command
          command: echo "Analyzed: $TOOL_INPUT" >> /tmp/security-audit.log
---

Focus on:
- SQL injection in database queries
- XSS in template rendering
- CSRF in form handling
- Insecure deserialization
- Sensitive data exposure
```

---

## Hooks

**Official Docs**: [code.claude.com/en/hooks](https://code.claude.com/en/hooks)

Hooks are event-driven automations that execute before or after specific actions. They can validate, log, transform, or block operations.

### Event Types

| Event | Trigger | Can Block | Key Use Cases |
|-------|---------|-----------|---------------|
| `PreToolUse` | Before tool execution | Yes | Validate commands, modify inputs |
| `PostToolUse` | After tool execution | No | Log results, capture outputs |
| `UserPromptSubmit` | User sends message | Yes | Inject context, validate requests |
| `Stop` | Claude stops responding | Yes | Final checks, cleanup |
| `SubagentStop` | Subagent completes | Yes | Validate agent output |
| `SessionStart` | Session begins | No | Initialize state, set env vars |
| `SessionEnd` | Session ends | No | Persist state, cleanup |
| `PreCompact` | Before context compression | No | Preserve critical info |
| `Notification` | Notification shown | No | External integrations |
| `PermissionRequest` | Permission prompt | Yes | Auto-approve/deny patterns |

### Hook Types

#### 1. Command Hooks (All events)

Execute shell scripts:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./validate-bash.sh \"$TOOL_INPUT\""
      }]
    }]
  }
}
```

#### 2. Prompt Hooks (All events)

LLM-based evaluation using Haiku:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Evaluate if all tasks are complete based on: $ARGUMENTS"
      }]
    }]
  }
}
```

**LLM response schema:**

```json
{
  "decision": "approve",           // "approve" or "block"
  "reason": "All tasks verified",  // Explanation
  "continue": false,               // Optional: stop Claude entirely
  "stopReason": "Work complete",   // Optional: message when stopping
  "systemMessage": "Note: ..."     // Optional: shown to user
}
```

#### 3. Agent Hooks (Plugins only)

Agentic verifier with tool access:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "agent",
        "agent": "code-quality-checker",
        "prompt": "Verify the changes meet quality standards"
      }]
    }]
  }
}
```

### Configuration Schema

```json
{
  "hooks": {
    "<EventType>": [{
      "matcher": "<pattern>",      // Tool name, glob, or regex
      "once": true,                // Optional: run only once per session
      "hooks": [{
        "type": "command",         // "command", "prompt", or "agent"
        "command": "...",          // For command type
        "prompt": "...",           // For prompt type
        "agent": "...",            // For agent type
        "timeout": 60000           // Optional: milliseconds
      }]
    }]
  }
}
```

### Matcher Patterns

| Pattern | Matches |
|---------|---------|
| `Bash` | All Bash tool uses |
| `Bash(npm run test)` | Exact command |
| `Bash(npm run:*)` | Commands starting with `npm run` |
| `Write\|Edit` | Either Write or Edit |
| `*` | All tools |
| `startup` | SessionStart event |

### Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| `0` | Success/Allow | Proceed with operation |
| `1` | Error (non-blocking) | Log error, proceed anyway |
| `2` | Block | Stop operation, show message |

**Important**: Exit code 1 does NOT block. Use exit code 2 to block.

### Environment Variables

Available in hook commands:

| Variable | Description |
|----------|-------------|
| `CLAUDE_PROJECT_DIR` | Project root directory |
| `CLAUDE_CODE_REMOTE` | `"true"` if running remotely |
| `TOOL_INPUT` | Tool input (PreToolUse/PostToolUse) |
| `TOOL_OUTPUT` | Tool output (PostToolUse only) |
| `CLAUDE_ENV_FILE` | Path for env persistence (SessionStart) |

### Input Modification

PreToolUse hooks can modify tool inputs:

```bash
#!/bin/bash
# Output JSON to modify the input
cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": "npm run lint -- --fix"
    }
  }
}
EOF
```

### Component-Scoped Hooks

Skills, commands, and agents can define their own hooks:

```yaml
---
name: my-skill
description: A skill with scoped hooks
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./skill-specific-validator.sh
---
```

### `once: true` Behavior

Run hook only once per session:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "once": true,
      "hooks": [{
        "type": "command",
        "command": "./setup-environment.sh"
      }]
    }]
  }
}
```

### Example: PreToolUse Validation

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/validate-bash.sh"
      }]
    }]
  }
}
```

```bash
#!/bin/bash
# ~/.claude/hooks/validate-bash.sh

# Block dangerous commands
if echo "$TOOL_INPUT" | grep -qE "(rm -rf|sudo|chmod 777)"; then
  echo "BLOCKED: Dangerous command detected" >&2
  exit 2
fi

# Allow
exit 0
```

### Example: SessionStart Environment Setup

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "echo 'source ~/.venv/bin/activate' >> \"$CLAUDE_ENV_FILE\""
      }]
    }]
  }
}
```

### Example: PostToolUse Logging

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "echo \"$(date): Modified $TOOL_INPUT\" >> ~/.claude/edit-log.txt"
      }]
    }]
  }
}
```

---

## MCP Servers

**Official Docs**: [code.claude.com/en/mcp](https://code.claude.com/en/mcp)

MCP (Model Context Protocol) servers connect Claude Code to external tools, databases, and APIs. They enable Claude to interact with services like GitHub, databases, monitoring systems, and custom tools.

### Transport Types

| Transport | Command | Notes |
|-----------|---------|-------|
| **HTTP** | `claude mcp add --transport http <name> <url>` | Recommended for remote servers |
| **SSE** | `claude mcp add --transport sse <name> <url>` | Deprecated, use HTTP |
| **stdio** | `claude mcp add --transport stdio <name> -- <cmd>` | Local processes |

### Registration Examples

```bash
# HTTP server (recommended)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# HTTP with authentication
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer $TOKEN"

# Local stdio server
claude mcp add --transport stdio airtable \
  --env AIRTABLE_API_KEY=$KEY \
  -- npx -y airtable-mcp-server

# From JSON configuration
claude mcp add-json weather '{"type":"http","url":"https://api.weather.com/mcp"}'

# Import from Claude Desktop
claude mcp add-from-claude-desktop
```

### Scopes

| Scope | Storage | Visibility |
|-------|---------|------------|
| **local** (default) | `~/.claude.json` (per-project) | You, this project only |
| **project** | `.mcp.json` | Team (committed to git) |
| **user** | `~/.claude.json` | You, all projects |

```bash
# Explicit scope
claude mcp add --transport http --scope user hubspot https://mcp.hubspot.com/anthropic
```

### Environment Variable Expansion

In `.mcp.json`:

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

Supported syntax:
- `${VAR}` — Value of VAR
- `${VAR:-default}` — Value of VAR or default

### OAuth Authentication

Many MCP servers require OAuth:

```bash
# Add server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# Authenticate (opens browser)
/mcp
# Select "Authenticate" for the server
```

### MCP Resources

Reference MCP resources with `@` mentions:

```
@github:issue://123
@postgres:schema://users
@docs:file://api/authentication
```

### MCP Prompts as Commands

MCP servers expose prompts as slash commands:

```
/mcp__github__list_prs
/mcp__github__pr_review 456
/mcp__jira__create_issue "Bug in login" high
```

### Output Limits

| Threshold | Behavior |
|-----------|----------|
| 10,000 tokens | Warning displayed |
| 25,000 tokens | Default maximum |

Configure via `MAX_MCP_OUTPUT_TOKENS`:

```bash
export MAX_MCP_OUTPUT_TOKENS=50000
claude
```

### Dynamic Tool Updates

MCP servers can send `list_changed` notifications to dynamically update available tools without reconnecting.

### Claude Code as MCP Server

Expose Claude Code's tools to other applications:

```bash
claude mcp serve
```

Add to Claude Desktop:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Plugin-Provided MCP Servers

Plugins can bundle MCP servers in `.mcp.json`:

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

Or inline in `plugin.json`:

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

### Management Commands

```bash
claude mcp list              # List all servers
claude mcp get github        # Details for specific server
claude mcp remove github     # Remove server
/mcp                         # Status and authentication
```

---

## LSP Servers

**Official Docs**: [code.claude.com/en/plugins-reference#lsp-servers](https://code.claude.com/en/plugins-reference#lsp-servers)

LSP (Language Server Protocol) servers provide code intelligence: diagnostics, go-to-definition, type information, and hover documentation. LSP servers are **plugin-only components**.

### Configuration Schema

In `.lsp.json` at plugin root:

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  },
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact"
    }
  }
}
```

### Features

- **Instant diagnostics**: Errors/warnings after file edits
- **Code navigation**: Go to definition, find references
- **Type information**: Hover for types and docs
- **Symbol search**: Find symbols across project

### Available Official Plugins

| Plugin | Languages |
|--------|-----------|
| `pyright-lsp` | Python |
| `typescript-lsp` | TypeScript, JavaScript |
| `rust-lsp` | Rust |

### Debug Logging

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "loggingConfig": {
      "args": ["--log-level", "4"],
      "env": {
        "TSS_LOG": "-level verbose -file ${CLAUDE_PLUGIN_LSP_LOG_FILE}"
      }
    }
  }
}
```

---

## Plugins

**Official Docs**: [code.claude.com/en/plugins](https://code.claude.com/en/plugins)

Plugins bundle multiple extension types for distribution. A single plugin can contain commands, skills, agents, hooks, MCP servers, and LSP servers.

### Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest (required)
├── commands/                 # Slash commands
│   └── review.md
├── skills/                   # Skills
│   └── analysis/
│       └── SKILL.md
├── agents/                   # Subagents
│   └── reviewer.md
├── hooks/
│   └── hooks.json           # Hook definitions
├── .mcp.json                # MCP servers
├── .lsp.json                # LSP servers
└── scripts/                 # Supporting scripts
    └── validate.sh
```

### Plugin Manifest Schema

`.claude-plugin/plugin.json`:

```json
{
  // Required
  "name": "my-plugin",

  // Recommended
  "version": "1.0.0",
  "description": "What this plugin does",

  // Optional metadata
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "license": "MIT",
  "keywords": ["code-review", "testing"],
  "homepage": "https://github.com/you/my-plugin",
  "repository": "https://github.com/you/my-plugin",

  // Component paths (supplement defaults, don't replace)
  "commands": "./commands/",           // or ["./commands/review.md"]
  "skills": "./skills/",               // or ["./skills/analysis/"]
  "agents": ["./agents/reviewer.md"],
  "hooks": "./hooks/hooks.json",       // or inline object
  "mcpServers": "./.mcp.json",         // or inline object
  "lspServers": "./.lsp.json"          // or inline object
}
```

### Path Resolution

- All paths use `./` prefix for plugin-relative resolution
- `${CLAUDE_PLUGIN_ROOT}` expands to plugin installation directory
- Path traversal (`../`) doesn't work (files aren't copied)

### Plugin Caching

When installed, plugins are copied to:
```
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
```

**Important**: External files (outside plugin directory) aren't copied. Use symlinks if needed.

### Installation Verification

Plugin installation is two-step:

1. **Cache creation**: Files copied to cache directory
2. **Registration**: Entry added to `installed_plugins.json`

```bash
# Check registration
cat ~/.claude/plugins/installed_plugins.json | jq '.["plugin@marketplace"]'

# Check cache
ls ~/.claude/plugins/cache/<marketplace>/<plugin>/

# Fix: reinstall
claude plugin install <plugin>@<marketplace>
```

### Hook Types for Plugins

Plugins support the `agent` hook type (not available elsewhere):

```json
{
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "agent",
      "agent": "quality-checker",
      "prompt": "Verify code quality of: $TOOL_INPUT"
    }]
  }]
}
```

### Example Plugin Manifest

```json
{
  "name": "enterprise-tools",
  "version": "2.1.0",
  "description": "Enterprise workflow automation",
  "author": {
    "name": "Enterprise Team",
    "email": "enterprise@example.com"
  },
  "license": "MIT",
  "keywords": ["enterprise", "workflow"],
  "commands": "./commands/",
  "agents": ["./agents/security-reviewer.md"],
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
      }]
    }]
  },
  "mcpServers": {
    "enterprise-db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

---

## Marketplaces

**Official Docs**: [code.claude.com/en/plugin-marketplaces](https://code.claude.com/en/plugin-marketplaces)

Marketplaces are catalogs that distribute plugins. They enable discovery, version tracking, and team-wide deployment.

### Marketplace File

`.claude-plugin/marketplace.json`:

```json
{
  "name": "company-tools",
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@example.com"
  },
  "metadata": {
    "description": "Internal development tools",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting",
      "version": "2.1.0"
    },
    {
      "name": "deployment-tools",
      "source": {
        "source": "github",
        "repo": "company/deploy-plugin"
      }
    }
  ]
}
```

### Plugin Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | **Required**. Plugin identifier (kebab-case) |
| `source` | string\|object | **Required**. Where to fetch plugin |
| `description` | string | Brief description |
| `version` | string | Semver version |
| `author` | object | `{name, email}` |
| `strict` | boolean | Require plugin.json (default: true) |
| `category` | string | For organization |
| `tags` | array | For searchability |

### Source Types

| Type | Format | Example |
|------|--------|---------|
| Relative | string | `"./plugins/my-plugin"` |
| GitHub | object | `{"source": "github", "repo": "owner/repo"}` |
| Git | object | `{"source": "url", "url": "https://gitlab.com/..."}` |
| NPM | object | `{"source": "npm", "package": "@scope/pkg"}` |
| File | object | `{"source": "file", "path": "/path/to/marketplace.json"}` |
| Directory | object | `{"source": "directory", "path": "/path/to/dir"}` |

### Reserved Names

Cannot use these marketplace names:
- `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`
- `anthropic-marketplace`, `anthropic-plugins`
- `agent-skills`, `life-sciences`
- Names impersonating official marketplaces

### Marketplace Commands

```bash
# Add marketplace
/plugin marketplace add owner/repo
/plugin marketplace add https://gitlab.com/team/plugins.git
/plugin marketplace add ./local-marketplace

# Update marketplace
/plugin marketplace update <name>

# Install plugin
/plugin install my-plugin@marketplace-name

# Validate
/plugin validate .
```

### Team Marketplace Configuration

In `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "formatter@company-tools": true,
    "deployer@company-tools": true
  }
}
```

### Inline Plugin Definition

Use `strict: false` to define plugins entirely in marketplace:

```json
{
  "plugins": [{
    "name": "quick-review",
    "source": "./plugins/review",
    "strict": false,
    "commands": ["./commands/"],
    "hooks": {
      "PostToolUse": [{
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/validate.sh"
        }]
      }]
    }
  }]
}
```

---

## Settings & Configuration

**Official Docs**: [code.claude.com/en/settings](https://code.claude.com/en/settings)

### Scope Levels

| Scope | Location | Purpose |
|-------|----------|---------|
| **Managed** | System `managed-settings.json` | IT/enterprise policies |
| **User** | `~/.claude/settings.json` | Personal defaults |
| **Project** | `.claude/settings.json` | Team-shared settings |
| **Local** | `.claude/settings.local.json` | Personal project overrides |

### Settings Schema

```json
{
  // Permissions
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "acceptEdits",
    "disableBypassPermissionsMode": "disable"
  },

  // Model
  "model": "claude-sonnet-4-5-20250929",

  // Hooks
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./validate.sh"
      }]
    }]
  },
  "disableAllHooks": false,
  "allowManagedHooksOnly": true,

  // Sandbox
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker", "git"],
    "allowUnsandboxedCommands": false,
    "network": {
      "allowUnixSockets": ["/var/run/docker.sock"],
      "allowLocalBinding": true,
      "httpProxyPort": 8080,
      "socksProxyPort": 1080
    },
    "enableWeakerNestedSandbox": true
  },

  // MCP
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"],

  // Plugins
  "enabledPlugins": {
    "formatter@acme-tools": true
  },
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": {
        "source": "github",
        "repo": "acme-corp/plugins"
      }
    }
  },

  // Display
  "outputStyle": "Explanatory",
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  },

  // Other
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1"
  },
  "attribution": {
    "commit": "Generated with AI\n\nCo-Authored-By: AI <ai@example.com>",
    "pr": ""
  },
  "cleanupPeriodDays": 30,
  "language": "japanese",
  "alwaysThinkingEnabled": true
}
```

### Permission Rule Syntax

| Pattern | Matches |
|---------|---------|
| `Bash(npm run test)` | Exact command |
| `Bash(npm run:*)` | Commands starting with prefix |
| `Read(./.env)` | Specific file |
| `Read(./secrets/**)` | Directory recursively |
| `Read(//absolute/path)` | Absolute path (note `//`) |
| `mcp__server__tool` | Specific MCP tool |
| `Task(Explore)` | Specific subagent type |

### File Suggestion Customization

```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  }
}
```

Input: `{"query": "src/comp"}` via stdin
Output: Newline-separated file paths to stdout

### Bash Environment Persistence

Three options:

1. **Activate before Claude**:
   ```bash
   conda activate myenv
   claude
   ```

2. **Set CLAUDE_ENV_FILE**:
   ```bash
   export CLAUDE_ENV_FILE=/path/to/env-setup.sh
   claude
   ```

3. **SessionStart hook**:
   ```json
   {
     "hooks": {
       "SessionStart": [{
         "matcher": "startup",
         "hooks": [{
           "type": "command",
           "command": "echo 'conda activate myenv' >> \"$CLAUDE_ENV_FILE\""
         }]
       }]
     }
   }
   ```

---

## Security & Managed Deployment

**Official Docs**: [code.claude.com/en/iam](https://code.claude.com/en/iam)

### Managed Settings Locations

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Linux/WSL | `/etc/claude-code/managed-settings.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-settings.json` |

### Managed MCP Configuration

**Option 1: Exclusive control** (`managed-mcp.json`):

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "company-internal": {
      "type": "stdio",
      "command": "/usr/local/bin/company-mcp-server"
    }
  }
}
```

Users cannot add any other servers when this file exists.

**Option 2: Allowlist/Denylist**:

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverCommand": ["npx", "-y", "approved-package"] },
    { "serverUrl": "https://mcp.company.com/*" }
  ],
  "deniedMcpServers": [
    { "serverName": "dangerous-server" },
    { "serverUrl": "https://*.untrusted.com/*" }
  ]
}
```

| `allowedMcpServers` Value | Behavior |
|---------------------------|----------|
| `undefined` | No restrictions |
| `[]` | Complete lockdown |
| `[entries...]` | Only matching servers allowed |

**Denylist always wins**: If a server matches denylist, it's blocked even if on allowlist.

### Managed Marketplace Restrictions

`strictKnownMarketplaces` in managed settings:

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/plugins" },
    { "source": "github", "repo": "acme-corp/security", "ref": "v2.0" },
    { "source": "url", "url": "https://plugins.example.com/marketplace.json" },
    { "source": "npm", "package": "@acme/plugins" }
  ]
}
```

| Value | Behavior |
|-------|----------|
| `undefined` | No restrictions |
| `[]` | No marketplaces can be added |
| `[sources...]` | Only exact matches allowed |

### Managed Hooks

```json
{
  "allowManagedHooksOnly": true
}
```

When enabled:
- Managed hooks and SDK hooks run
- User, project, and plugin hooks blocked

### Disable Bypass Mode

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

Prevents `--dangerously-skip-permissions` flag.

---

## Appendices

### A: Frontmatter Fields Reference

#### Command Frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Shown in slash menu |
| `argument-hint` | string | No | Hint for expected arguments |
| `model` | string | No | Model override |
| `allowed-tools` | string | No | Comma-separated tool list |
| `hooks` | object | No | Component-scoped hooks |

#### Skill Frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Kebab-case identifier |
| `description` | string | Yes | One-line description |
| `license` | string | No | SPDX identifier |
| `metadata.version` | string | No | Semver version |
| `metadata.model` | string | No | Recommended model |
| `metadata.timelessness_score` | number | No | Quality indicator 1-10 |
| `user-invocable` | boolean | No | Show in slash menu (default: true) |
| `disable-model-invocation` | boolean | No | Prevent Skill tool (default: false) |
| `allowed-tools` | string | No | Comma-separated tool list |
| `context` | string | No | `fork` for isolation |
| `agent` | string | No | Agent type when forked |
| `hooks` | object | No | Component-scoped hooks |

#### Agent Frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Shown in Task tool |
| `prompt` | string | No | System prompt |
| `tools` | array | No | Allowed tools |
| `model` | string | No | `sonnet`, `opus`, or `haiku` |
| `skills` | array | No | Auto-load skills |
| `permissionMode` | string | No | Permission behavior |
| `hooks` | object | No | Component-scoped hooks |

### B: Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for Claude SDK |
| `ANTHROPIC_MODEL` | Model setting name |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Override Sonnet model |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Override Haiku model |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Override Opus model |
| `CLAUDE_CODE_USE_BEDROCK` | Use Amazon Bedrock |
| `CLAUDE_CODE_USE_VERTEX` | Use Google Vertex |
| `CLAUDE_CODE_USE_FOUNDRY` | Use Microsoft Foundry |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for subagents |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Max output tokens |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Max tokens for file reads |
| `MAX_MCP_OUTPUT_TOKENS` | Max MCP tool output |
| `MAX_THINKING_TOKENS` | Extended thinking budget |
| `MCP_TIMEOUT` | MCP server startup timeout |
| `MCP_TOOL_TIMEOUT` | MCP tool execution timeout |
| `BASH_DEFAULT_TIMEOUT_MS` | Default bash timeout |
| `BASH_MAX_TIMEOUT_MS` | Max bash timeout |
| `BASH_MAX_OUTPUT_LENGTH` | Max bash output chars |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Reset CWD after bash |
| `CLAUDE_CODE_SHELL` | Override shell detection |
| `CLAUDE_ENV_FILE` | Environment setup script |
| `CLAUDE_CONFIG_DIR` | Custom config directory |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Skill tool char limit |
| `DISABLE_TELEMETRY` | Opt out of telemetry |
| `DISABLE_ERROR_REPORTING` | Opt out of Sentry |
| `DISABLE_AUTOUPDATER` | Disable auto-updates |
| `DISABLE_COST_WARNINGS` | Hide cost warnings |

### C: Decision Trees

#### Which Extension Type?

```
Start here
│
├─ Does it need to react to events? ──────────► Hook
│
├─ Does it run in a separate context? ────────► Subagent
│
├─ Does it integrate external APIs/tools? ────► MCP Server
│
├─ Does it provide code intelligence? ────────► LSP Server (plugin only)
│
├─ Is it a simple prompt template?
│   ├─ Yes, one-shot ─────────────────────────► Command
│   └─ No, has logic/verification ────────────► Skill
│
└─ Need to distribute to others? ─────────────► Plugin (bundles above)
```

#### Hook Event Selection

```
What do you want to do?
│
├─ Validate/block tool use ───────────────────► PreToolUse
├─ Log/react to tool results ─────────────────► PostToolUse
├─ Inject context into prompts ───────────────► UserPromptSubmit
├─ Final checks before stopping ──────────────► Stop
├─ Validate subagent output ──────────────────► SubagentStop
├─ Initialize environment ────────────────────► SessionStart
├─ Cleanup at end ────────────────────────────► SessionEnd
├─ Preserve context during compaction ────────► PreCompact
├─ Auto-approve/deny permissions ─────────────► PermissionRequest
└─ React to notifications ────────────────────► Notification
```

### D: Migration Guide

#### Command → Skill

When to migrate:
- Adding conditional logic ("if X then Y")
- Need verification steps
- Multiple decision points
- Reusable across projects

Steps:
1. Create directory: `.claude/skills/<name>/`
2. Create `SKILL.md` with frontmatter
3. Move command content to body
4. Add procedure sections
5. Add verification criteria

#### Skill → Plugin

When to migrate:
- Distributing to others
- Need hooks, MCP servers, or LSP servers
- Multiple related skills/commands
- Version management needed

Steps:
1. Create plugin directory structure
2. Create `.claude-plugin/plugin.json`
3. Move skills to `skills/` directory
4. Add other components as needed
5. Create marketplace for distribution

---

## Additional Resources

- **Official Documentation**: [code.claude.com/docs](https://code.claude.com/docs/llms.txt)
- **Skills Reference**: [code.claude.com/en/skills](https://code.claude.com/en/skills)
- **Hooks Guide**: [code.claude.com/en/hooks](https://code.claude.com/en/hooks)
- **Plugins Reference**: [code.claude.com/en/plugins](https://code.claude.com/en/plugins)
- **MCP Documentation**: [modelcontextprotocol.io](https://modelcontextprotocol.io/introduction)
- **Settings Reference**: [code.claude.com/en/settings](https://code.claude.com/en/settings)
- **IAM Guide**: [code.claude.com/en/iam](https://code.claude.com/en/iam)
