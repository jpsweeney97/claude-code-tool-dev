# Claude Code Artifact Specifications (Fallback)

> **Last verified:** 2026-01-09
> **Update trigger:** Re-verify when claude-code-guide returns significantly different specs
> **Owner:** Manual update by skill maintainer
> **Source:** Official Anthropic documentation via claude-code-guide agent

---

## Skills

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | `SKILL.md` in skill directory |
| Frontmatter | YAML with `name`, `description` (required) |
| Location | `.claude/skills/<name>/SKILL.md` |
| Body size | Recommended under 500 lines; use progressive disclosure for larger content |

### Valid Frontmatter Fields
| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| name | Yes | string | Max 64 chars. Lowercase, numbers, hyphens only. |
| description | Yes | string | Max 1024 chars. Describes what it does + when to use. |
| allowed-tools | No | string/array | Comma-separated or YAML list |
| model | No | string | Specific Claude model (e.g., `claude-sonnet-4-20250514`) |
| context | No | string | Set to `fork` for isolated subagent execution |
| agent | No | string | Agent type when `context: fork` (e.g., `general-purpose`) |
| hooks | No | object | Component-scoped hooks (PreToolUse, PostToolUse, Stop) |
| user-invocable | No | boolean | Controls visibility in slash menu (default: true) |
| disable-model-invocation | No | boolean | Blocks Skill tool from invoking this skill |

### Anti-patterns
- Reserved words in name ("anthropic", "claude")
- Hardcoded file paths (use relative or ask user)
- Dependencies on external packages (skills run in minimal environment)
- Assuming cross-session memory
- SKILL.md body over 500 lines without progressive disclosure

---

## Hooks

### Hook Types
| Type | Description | Model | Availability |
|------|-------------|-------|--------------|
| `command` | Execute bash script | N/A | All hooks |
| `prompt` | LLM-based evaluation | Haiku | All hooks |
| `agent` | Agentic verifier with tools | Configurable | Plugins only |

### Event Types
| Event | Runs When | Can Block |
|-------|-----------|-----------|
| PreToolUse | Before tool call | Yes |
| PostToolUse | Tool completes | No |
| UserPromptSubmit | User submits prompt | Yes |
| Stop | Main agent finishes | Yes |
| SubagentStop | Subagent finishes | Yes |
| SessionStart | Session begins | No |
| SessionEnd | Session terminates | No |
| PreCompact | Before compact | No |
| Notification | Notification sent | No |
| PermissionRequest | Permission dialog | Yes |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Allow / success |
| 1 | Error (logged, does NOT block) |
| 2 | Block with message (stderr used) |

### Component-Scoped Hooks
Skills, commands, and agents can define hooks in frontmatter. The `once: true` option is supported for skills and commands only (NOT agents).

### Anti-patterns
- Exit code 1 for blocking (use 2)
- JSON in stdout at exit 2 (ignored; use stderr)
- Not reading stdin JSON
- Synchronous network calls without timeout
- Using `once: true` on agent hooks (not supported)

---

## Commands

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | Markdown file |
| Location | `.claude/commands/<name>.md` |

### Frontmatter Fields
| Field | Required | Type | Notes |
|-------|----------|------|-------|
| description | No | string | Shown in command list (recommended) |
| argument-hint | No | string | Placeholder text for arguments |
| allowed-tools | No | string | Comma-separated list of tools |
| model | No | string | Specific Claude model |
| disable-model-invocation | No | boolean | Blocks Skill tool invocation |
| hooks | No | object | PreToolUse, PostToolUse, or Stop handlers |

### Placeholder
- `$ARGUMENTS` — substituted with user input after command name

---

## Subagents

### Frontmatter Fields
| Field | Required | Type | Notes |
|-------|----------|------|-------|
| name | Yes | string | Lowercase + hyphens only |
| description | Yes | string | Purpose description |
| tools | No | string | Comma-separated tool list |
| model | No | string | sonnet, opus, haiku, or 'inherit' |
| permissionMode | No | string | default, acceptEdits, dontAsk, bypassPermissions, plan, ignore |
| skills | No | string | Comma-separated skills to auto-load |
| hooks | No | object | PreToolUse, PostToolUse, or Stop handlers |

### Configuration via Task Tool
| Field | Type | Notes |
|-------|------|-------|
| subagent_type | string | Agent type identifier |
| prompt | string | Task description |
| model | string | sonnet, opus, haiku |
| max_turns | number | API round-trips limit |

### Built-in Types
| Type | Purpose | Model |
|------|---------|-------|
| general-purpose | Multi-step tasks | sonnet |
| Explore | Fast codebase exploration | haiku |
| Plan | Codebase research in plan mode | sonnet |

---

## Plugins

### Required Structure
| Element | Requirement |
|---------|-------------|
| Manifest | `.claude-plugin/plugin.json` |
| Location | Any directory with manifest |

### Manifest Fields
| Field | Required | Type |
|-------|----------|------|
| name | Yes | string |
| version | No | semver string |
| description | No | string |
| author | No | object with name |
| skills | No | path or array |
| commands | No | path or array |
| agents | No | array of file paths |
| hooks | No | path or inline config |
| mcpServers | No | path to .mcp.json |
| outputStyles | No | path or array |
| lspServers | No | path to .lsp.json |

### Path Conventions
- All paths use `./` prefix for portability
- Skills: `"./skills/"` or `["./skills/one.md"]`

---

## MCP Servers

### Required Structure
| Element | Requirement |
|---------|-------------|
| Config | `.mcp.json` or `~/.claude.json` |
| Transport | stdio (local) or http (remote) |

### Tool Output Limits
- Warning at 10K tokens
- Max 25K tokens per tool response

---

## Settings

### Configuration Files
| Scope | Location |
|-------|----------|
| Managed | System directories (IT/enterprise) |
| Local project | `.claude/settings.local.json` |
| Shared project | `.claude/settings.json` |
| User | `~/.claude/settings.json` |

### Permission Modes
| Mode | Behavior |
|------|----------|
| default | Prompts for permission on first use |
| acceptEdits | Auto-accepts file edits |
| plan | Analyze only, no modifications |
| dontAsk | Auto-denies unless pre-approved |
| bypassPermissions | Skips all prompts |
| ignore | No permissions enforced |

---

## Common Behavioral Patterns

### Claude Limitations
- No cross-session memory without explicit persistence (CLAUDE.md files)
- Context window 200K tokens; attention quality degrades in very long contexts
- Multi-step reasoning reliability decreases with complexity
- Proactive behavior requires explicit triggers in prompts

### Model Selection
| Task | Recommended |
|------|-------------|
| Simple queries, doc lookup | haiku |
| Standard development | sonnet |
| Complex architecture | opus |

### Tool Behaviors
| Tool | Behavior |
|------|----------|
| Task | Subagents run in separate context; cannot nest |
| Read | Max 2000 lines default; truncates long lines at 2000 chars |
| Bash | 60-second timeout default; env vars don't persist |
| WebFetch | 25K token cap; 10K warning threshold |
