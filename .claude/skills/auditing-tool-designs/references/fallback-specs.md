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
| name | Yes | string | Max 64 chars. Lowercase, numbers, hyphens only. **Cannot contain reserved words: "anthropic", "claude"**. Gerund form recommended (e.g., `processing-pdfs`). |
| description | Yes | string | Max 1024 chars. **Must use third-person** (e.g., "Processes files..." not "Process files..."). Describes what it does + when to use. |
| model | No | string | Specific Claude model for this skill |
| allowed-tools | No | array | Restrict which tools Claude can use |
| user-invocable | No | boolean | Hide from slash menu if false |

### Anti-patterns
- Reserved words in name ("anthropic", "claude")
- Imperative or second-person descriptions ("Use this to...", "You can...")
- Hardcoded file paths (use relative or ask user)
- Dependencies on external packages (skills run in minimal environment)
- Assuming cross-session memory
- SKILL.md body over 500 lines without progressive disclosure

---

## Hooks

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | Script with settings.json entry |
| Location | Configured in settings.json hooks section |

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

### Anti-patterns
- Exit code 1 for blocking (use 2)
- JSON in stdout at exit 2 (ignored; use stderr)
- Not reading stdin JSON
- Synchronous network calls without timeout

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
| mcpServers | No | path to .mcp.json |

### Path Conventions
- All paths use `./` prefix for portability
- Skills: `"./skills/"` or `["./skills/one.md"]`

---

## Commands

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | Markdown file |
| Location | `.claude/commands/<name>.md` |

### Frontmatter Fields
| Field | Required | Notes |
|-------|----------|-------|
| description | No | Shown in command list (recommended) |
| argument-hint | No | Placeholder text for arguments |

### Placeholder
- `$ARGUMENTS` — substituted with user input after command name

---

## Subagents

### Configuration via Task Tool
| Field | Type | Notes |
|-------|------|-------|
| subagent_type | string | Agent type identifier |
| prompt | string | Task description |
| model | string | sonnet, opus, haiku |
| max_turns | number | API round-trips limit |

### Built-in Types
- general-purpose: Multi-step tasks with all tools
- Explore: Fast codebase exploration
- Plan: Architecture planning
- claude-code-guide: Documentation queries (uses haiku)

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
