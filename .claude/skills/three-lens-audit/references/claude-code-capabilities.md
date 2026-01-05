# Claude Code Capabilities Reference

**Source:** Official Anthropic Claude Code Documentation
**Last Verified:** 2025-01-04
**Documentation URLs:** code.claude.com/docs/

This reference contains ONLY information verified against official Anthropic documentation. Claims are cited with their source. Items not officially documented are explicitly marked.

---

## Artifact Type Quick Reference

| Artifact | Location | Key Files | Official Documentation |
|----------|----------|-----------|----------------------|
| **Skill** | `~/.claude/skills/` or `.claude/skills/` | `SKILL.md` | [Skills Guide](https://code.claude.com/docs/en/skills.md) |
| **Hook** | Settings or `.claude/hooks/` | `*.py`, `*.sh` | [Hooks Reference](https://code.claude.com/docs/en/hooks.md) |
| **Plugin** | `.claude-plugin/` | `plugin.json` | [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) |
| **MCP Server** | `.mcp.json` or `~/.claude.json` | JSON config | [MCP Documentation](https://code.claude.com/docs/en/mcp.md) |
| **Command** | `~/.claude/commands/` or `.claude/commands/` | `*.md` files | [Commands Reference](https://code.claude.com/docs/en/slash-commands.md) |
| **Subagent** | `.claude/agents/` | `*.md` files | [Subagents Guide](https://code.claude.com/docs/en/sub-agents.md) |

---

## 1. Skills

### Official YAML Frontmatter Properties

Source: [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices.md)

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | **Yes** | Max 64 chars, lowercase letters/numbers/hyphens only, no XML tags, cannot contain "anthropic" or "claude" |
| `description` | **Yes** | Max 1024 chars, cannot contain XML tags |
| `allowed-tools` | No | Tools Claude can use without permission prompts |
| `model` | No | Model to use when Skill is active |

**WARNING:** Only these four properties are officially documented. Using other properties (like `license` or `metadata`) is not officially supported.

### Skill Discovery

Skills are matched semantically by Claude analyzing the description. There is no separate "trigger phrases" field. From official docs:

> "Be specific and include key terms. Include both what the Skill does and specific triggers/contexts for when to use it."

### Official Troubleshooting (Common Failures)

Source: [Skills Best Practices](https://code.claude.com/docs/en/best-practices.md)

| Issue | Cause |
|-------|-------|
| Skill not loading | Invalid YAML syntax |
| Skill not found | Incorrect path (must be `.claude/skills/my-skill/SKILL.md`, case-sensitive) |
| Script errors | Missing dependencies or permissions (need `chmod +x`) |
| Windows issues | Backslashes in paths (use forward slashes) |

### Quality Checklist (Based on Official Docs)

- [ ] `name` is lowercase with hyphens, ≤64 chars
- [ ] `name` does not contain "anthropic" or "claude"
- [ ] `description` is ≤1024 chars, no XML tags
- [ ] SKILL.md body under 500 lines (official recommendation)
- [ ] Description includes when/why to use the skill (for semantic matching)

---

## 2. Hooks

### Official Hook Events

Source: [Hooks Reference](https://code.claude.com/docs/en/hooks.md)

| Event | When Triggered | Supports Matcher |
|-------|---------------|------------------|
| `PreToolUse` | Before tool execution | Yes |
| `PostToolUse` | After tool completion | Yes |
| `PermissionRequest` | When permission dialog shown | Yes |
| `Notification` | When Claude sends notifications | No |
| `UserPromptSubmit` | When user submits prompt | No |
| `Stop` | When Claude finishes responding | No |
| `SubagentStop` | When subagent finishes | No |
| `PreCompact` | Before compact operation | No |
| `SessionStart` | When session starts/resumes | No |
| `SessionEnd` | When session ends | No |

### Official Exit Code Semantics

Source: [Hooks Reference](https://code.claude.com/docs/en/hooks.md)

| Exit Code | Behavior |
|-----------|----------|
| **0** | Success. stdout shown in verbose mode (ctrl+o) |
| **2** | Blocking error. stderr used as error message, fed back to Claude |
| **Other (1, etc.)** | Non-blocking error. stderr shown in verbose mode. Execution continues. |

**CRITICAL:** Exit 2 behavior varies by event type:
- `PreToolUse`: Blocks tool, shows stderr **to Claude** (not user)
- `UserPromptSubmit`: Blocks prompt, shows stderr **to user only**

### Official Input Format (PreToolUse)

Source: [Hooks Reference](https://code.claude.com/docs/en/hooks.md)

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### Official Matcher Syntax

Source: [Hooks Reference](https://code.claude.com/docs/en/hooks.md)

- Simple strings match exactly: `Write` matches only Write tool
- Regex supported: `Edit|Write` or `Notebook.*`
- `*` or empty string matches all tools
- **Case-sensitive**

### Quality Checklist (Based on Official Docs)

- [ ] Exit code 0 for allow, 2 for block
- [ ] Stderr message explains why (for exit 2)
- [ ] Matcher specified for PreToolUse/PostToolUse/PermissionRequest
- [ ] Handles JSON input gracefully

---

## 3. Plugins

### Official Manifest Location

Source: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md)

- Manifest: `.claude-plugin/plugin.json`
- **Only `plugin.json` belongs in `.claude-plugin/`**
- All components (commands/, agents/, skills/, hooks/) at plugin root

### Official Required vs Optional Fields

Source: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md)

**Required:**
- `name` (string, kebab-case, unique identifier)

**Optional Metadata:**
- `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`

**Optional Component Paths:**
- `commands`, `agents`, `skills`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`

Minimal valid plugin.json:
```json
{
  "name": "my-plugin"
}
```

### Official Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # ONLY file here
├── commands/                # Default location
├── agents/                  # Default location
├── skills/                  # Default location
├── hooks/                   # Default location
├── .mcp.json               # Optional
└── .lsp.json               # Optional
```

### Quality Checklist (Based on Official Docs)

- [ ] `name` field present and kebab-case
- [ ] Only `plugin.json` inside `.claude-plugin/`
- [ ] Component directories at plugin root (not inside `.claude-plugin/`)
- [ ] Skills referenced via `components.skills` or `skills` field

---

## 4. MCP Servers

### Official Configuration Locations

Source: [MCP Documentation](https://code.claude.com/docs/en/mcp.md)

| Scope | Location |
|-------|----------|
| Project | `.mcp.json` at project root |
| User | `~/.claude.json` |

**WARNING:** User scope is `~/.claude.json`, NOT `~/.claude/.mcp.json`

### Official Configuration Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "/path/to/server",
      "args": [],
      "env": {}
    }
  }
}
```

### Official Supported Transports

Source: [MCP Documentation](https://code.claude.com/docs/en/mcp.md)

| Transport | Status |
|-----------|--------|
| HTTP | Recommended (`--transport http`) |
| SSE | **Deprecated** (`--transport sse`) |
| Stdio | Local development (`--transport stdio`) |

### Official Timeout Configuration

> "Configure MCP server startup timeout using the `MCP_TIMEOUT` environment variable (for example, `MCP_TIMEOUT=10000 claude` sets a 10-second timeout)"

**NOTE:** No specific startup time requirement is documented. Default timeout is configurable.

### Quality Checklist (Based on Official Docs)

- [ ] Configuration in correct location (`.mcp.json` or `~/.claude.json`)
- [ ] Uses `mcpServers` key with server name
- [ ] Has `command` field
- [ ] Uses HTTP transport (not deprecated SSE)

---

## 5. Commands (Slash Commands)

### Official Locations

Source: [Slash Commands Reference](https://code.claude.com/docs/en/slash-commands.md)

| Scope | Location |
|-------|----------|
| Project | `.claude/commands/` |
| User | `~/.claude/commands/` |

### Official Frontmatter Fields

| Field | Purpose | Default |
|-------|---------|---------|
| `description` | Brief description | First line of prompt |
| `argument-hint` | Expected arguments | None |
| `allowed-tools` | Tools command can use | Inherits from conversation |
| `model` | Specific model string | Inherits from conversation |
| `disable-model-invocation` | Prevent SlashCommand tool invocation | false |

### Quality Checklist (Based on Official Docs)

- [ ] `description` field present
- [ ] `allowed-tools` follows least privilege
- [ ] Filename is command name (kebab-case.md)

---

## 6. Subagents

### Official Configuration

Source: [Subagents Guide](https://code.claude.com/docs/en/sub-agents.md)

Subagents use `name` field for identification (NOT `subagent_type`):

```markdown
---
name: your-sub-agent-name
description: Description of when this subagent should be invoked
tools: tool1, tool2, tool3
model: sonnet
permissionMode: default
skills: skill1, skill2
---

Your subagent's system prompt goes here.
```

### Official Model Options

| Value | Behavior |
|-------|----------|
| `opus` | Use Claude Opus |
| `sonnet` | Use Claude Sonnet (default) |
| `haiku` | Use Claude Haiku |
| `inherit` | Use same model as main conversation |

### Official Tool Access

> "When the `tools` field is omitted, subagents inherit all MCP tools available to the main thread."

### NOT DOCUMENTED

The following are **NOT in official Claude Code documentation**:
- `subagent_type` field (official docs use `name`)
- Background execution options
- Specific parallelism limits for Task tool

### Quality Checklist (Based on Official Docs)

- [ ] `name` field present and descriptive
- [ ] `description` explains when to invoke
- [ ] `model` appropriate for task complexity
- [ ] `tools` field limits access appropriately (or inherits)

---

## 7. Behavioral Characteristics

### Context Window

Source: [Claude Context Windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)

- **Standard:** 200K tokens (all models, all paid plans)
- **Exception:** Claude Sonnet 4 has 500K tokens on Enterprise plans
- **Extended:** 1M tokens available on API, Bedrock, Vertex AI (requires tier 4)

### Session Memory

Source: [Memory Documentation](https://code.claude.com/docs/en/memory.md)

**Cross-session persistence exists via:**
- `CLAUDE.md` in project root - loaded every session in that directory
- `~/.claude/CLAUDE.md` - personal memory loaded across all projects
- `.claude/rules/` directory - multiple rule files automatically loaded
- `/memory` command - manage persistent memory files

**Session-only (does NOT persist):**
- Conversation history
- Granted permissions (except "Yes, don't ask again")
- Working directory changes
- Environment variables set in shell

### Permission Patterns

Source: [IAM Documentation](https://code.claude.com/docs/en/iam.md)

**Verified syntax patterns:**

```
Bash(npm run build)           # Exact command
Bash(npm run test:*)          # Prefix match with wildcard
Read(~/.zshrc)                # Home directory
Read(//Users/alice/secrets/**) # Absolute path (note //)
Read(src/**)                  # Relative to working directory
WebFetch(domain:example.com)  # Domain matching
mcp__puppeteer                # MCP server wildcard
mcp__puppeteer__navigate      # Specific MCP tool
```

**Official warning about Bash patterns:**
> "This tool uses **prefix matches**, not regex or glob patterns. The wildcard `:*` only works at the end of a pattern."

Bypassable patterns include:
- Options before URL: `curl -X GET http://site.com/...`
- Different protocol: `curl https://site.com/...`
- Variable indirection: `URL=http://site.com && curl $URL`

### Sandbox

Source: [Sandboxing Documentation](https://code.claude.com/docs/en/sandboxing.md)

- **Disabled by default**
- Filesystem and network access restricted when enabled
- `excludedCommands` array for incompatible tools (docker, podman, etc.)
- `dangerouslyDisableSandbox` can be blocked via `allowUnsandboxedCommands: false`

### NOT DOCUMENTED

The following claims have **no official documentation**:
- "Edit requires prior Read" - Not stated; they're independent permissions
- Specific parallel tool call limits
- Single response token limits

---

## Using This Reference

When auditing Claude Code artifacts:

1. **Identify artifact type** from the table above
2. **Apply the quality checklist** for that type
3. **Cite this reference** when identifying issues
4. **Flag anything not in this document** as unverified

**If a claim is not in this document, it is not officially documented.** The Implementation lens should only assert failures for officially documented requirements.

---

## Document Provenance

| Verification Date | Sources Checked |
|-------------------|-----------------|
| 2025-01-04 | code.claude.com/docs/en/* |

**Methodology:** Each claim verified via claude-code-guide agent searching official Anthropic documentation. Unverified claims removed. This document will require periodic re-verification as Claude Code evolves.
