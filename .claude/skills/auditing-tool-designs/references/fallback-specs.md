# Claude Code Artifact Specifications (Fallback)

> **Last verified:** 2026-01-11
> **Version:** Based on Claude Code documentation as of 2026-01-09
> **Update trigger:** Re-verify monthly or when claude-code-guide returns significantly different specs
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
| license | No | string | License type (e.g., MIT) |
| metadata | No | object | Contains version, model, timelessness_score |
| allowed-tools | No | string/array | Comma-separated or YAML list |
| model | No | string | Specific Claude model (e.g., `claude-sonnet-4-20250514`) |
| context | No | string | Set to `fork` for isolated subagent execution |
| agent | No | string | Agent type when `context: fork` (e.g., `general-purpose`) |
| hooks | No | object | Component-scoped hooks (PreToolUse, PostToolUse, Stop) |
| user-invocable | No | boolean | Controls visibility in slash menu (default: true) |
| disable-model-invocation | No | boolean | Blocks Skill tool from invoking this skill |

### Pattern Matching
`allowed-tools` supports pattern matching: `ToolName(prefix:*)` matches commands starting with prefix.
Example: `Bash(python:*)` allows `python script.py` but blocks `rm -rf`.

### Anti-patterns
- Reserved words in name ("anthropic", "claude")
- Hardcoded file paths (use relative or ask user)
- Dependencies on external packages (skills run in minimal environment)
- Assuming cross-session memory
- SKILL.md body over 500 lines without progressive disclosure

### Required Body Sections
Skills MUST contain these 8 content areas (equivalent headings allowed):

| Section | Purpose |
|---------|---------|
| When to use | Triggers and conditions for invocation |
| When NOT to use | Explicit boundaries and exclusions |
| Inputs | What the skill needs to operate |
| Outputs / Definition of Done | Artifacts produced and completion criteria |
| Procedure | Step-by-step workflow |
| Decision points | ≥2 explicit "If...then...otherwise" with observable triggers |
| Verification | How to confirm the skill worked |
| Troubleshooting | ≥1 common failure mode with cause and fix |

### Risk Tiering
| Tier | Criteria | Minimum Requirements |
|------|----------|---------------------|
| Low | Read-only, no external calls, reversible | Basic 8 sections |
| Medium | Writes files, calls external services | + explicit rollback guidance |
| High | Destructive operations, irreversible changes | + confirmation gates, dry-run option |

### Definition of Done Requirements
- **Objective DoD:** Completion must be verifiable without human judgment (file exists, command exits 0, grep matches)
- **Subjective guidance is NOT DoD:** "looks good", "user satisfied", "seems complete" are anti-patterns

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
| PostToolUseFailure | After tool execution fails | No |
| UserPromptSubmit | User submits prompt | Yes |
| Stop | Main agent finishes | Yes |
| SubagentStart | Subagent begins | Yes |
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
Skills, commands, and agents can define hooks in frontmatter:
- **Skills/Commands:** Full support including `once: true` option
- **Agents:** Can use hooks, but `once: true` is NOT supported

| Component | `once: true` Support |
|-----------|---------------------|
| Skills | Yes |
| Commands | Yes |
| Agents | No |

### Component-Scoped Hook Events
Component-scoped hooks (in skills, commands, agents) support only 3 events:
- `PreToolUse`
- `PostToolUse`
- `Stop`

Other events require settings.json configuration.

### Hook Timeout
Default hook timeout is 60 seconds. Configure per-hook with `timeout` field (milliseconds).

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
| hooks | No | object | PreToolUse, PostToolUse, or Stop handlers (supports `once: true`) |

### Argument Substitution
| Placeholder | Substitution |
|-------------|--------------|
| `$ARGUMENTS` | All user input after command name |
| `$1`, `$2`, ... | Positional arguments (space-separated) |

### Special Syntax
| Prefix | Behavior |
|--------|----------|
| `!` | Execute as bash command (e.g., `!npm run build`) |
| `@` | Include file contents (e.g., `@./README.md`) |

---

## Subagents

### Frontmatter Fields
| Field | Required | Type | Notes |
|-------|----------|------|-------|
| name | Yes | string | Lowercase + hyphens only |
| description | Yes | string | Purpose description |
| tools | No | string | Comma-separated tool list |
| disallowedTools | No | string | Comma-separated denylist (removed from inherited/specified tools) |
| model | No | string | sonnet, opus, haiku, or 'inherit' |
| permissionMode | No | string | default, acceptEdits, dontAsk, bypassPermissions, plan |
| skills | No | string | Comma-separated skills to auto-load |
| hooks | No | object | PreToolUse, PostToolUse, or Stop handlers |

**Note:** When `model` is omitted, agents default to `sonnet`.

**Note:** `Stop` hooks defined in agent frontmatter are internally converted to `SubagentStop` events.

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
| general-purpose | Multi-step tasks | inherit |
| Explore | Fast codebase exploration | haiku |
| Plan | Codebase research in plan mode | inherit |

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
| license | No | string |
| keywords | No | array (searchable keywords) |
| homepage | No | string (project URL) |
| repository | No | string (source URL) |
| skills | No | path or array |
| commands | No | path or array |
| agents | No | array of file paths |
| hooks | No | path or inline config |
| mcpServers | No | path to .mcp.json |
| outputStyles | No | path/array (custom output style markdown files) |
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
| Transport | stdio (local), http (remote), sse (deprecated) |

### Tool Output Limits
- Warning at 10K tokens
- Max 25K tokens per tool response

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `MCP_TIMEOUT` | Server startup timeout in ms |
| `MAX_MCP_OUTPUT_TOKENS` | Maximum output tokens (default: 25000) |

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

### Managed Settings
| Field | Purpose |
|-------|---------|
| `disableBypassPermissionsMode` | Prevent `bypassPermissions` mode activation |
| `additionalDirectories` | Directories outside project Claude can access |

---

## Common Behavioral Patterns

> **Note:** These patterns are observed behaviors and general Claude capabilities,
> not formally specified in extension-reference documentation.

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

---

## Context-Appropriate Severity

Security findings require **exploitability assessment** based on input trust level.

### Exploitability by Input Source

| Input Source | Exploitability Standard |
|--------------|------------------------|
| Developer-controlled (env vars, config files) | Admin already has access; not externally exploitable |
| Version-controlled files | Attacker needs commit access; not externally exploitable |
| User input (forms, API parameters) | Externally exploitable; full security review required |
| External data (APIs, uploads) | High risk; assume hostile input |

### Common False Positives

These patterns are often flagged incorrectly for trusted-input tools:

| Finding | Why It's Often Invalid |
|---------|----------------------|
| "Path traversal in DOCS_PATH env var" | Admin-configured; attacker can't control |
| "YAML bomb vulnerability" | Version-controlled docs; attacker can't inject |
| "SQL injection in config" | Developer-written config; not user input |
| "Command injection in build script" | Developer runs it; not exposed to users |

### Severity Assignment Rules

1. **Critical requires external exploitability** — If an attacker needs admin/commit access, it's not Critical
2. **Major requires realistic scenario** — "Attacker modifies your config file" isn't realistic for most threat models
3. **Minor for defense-in-depth** — Valid hardening suggestions that don't address real threats

### Anti-Pattern

**DON'T:** Flag every theoretical vulnerability as Critical regardless of who controls the input.

**DO:** Ask "Who can trigger this?" before assigning severity. If the answer is "only the developer/admin," it's not externally exploitable.
