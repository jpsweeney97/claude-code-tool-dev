# Known Claims

Pre-verified claims sourced from official Claude Code documentation.

**Last verified:** 2026-01-06
**Method:** Queried via claude-code-guide agent against official docs

---

## How to Use

1. Check if incoming claim matches an entry below
2. If found → return verdict immediately (no query needed)
3. If not found → query claude-code-guide for fresh verification

---

## Skills

**Source:** https://code.claude.com/docs/en/skills.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| `name` field is required in frontmatter | ✓ Verified | "must include a `name` and `description`" | 2026-01-05 |
| `description` field is required in frontmatter | ✓ Verified | "must include a `name` and `description`" | 2026-01-05 |
| `license` field is required in frontmatter | ✗ False | Not listed as required; only `name` and `description` are required | 2026-01-05 |
| `allowed-tools` field is optional | ✓ Verified | Listed as "No" under Required column | 2026-01-05 |
| `model` field is optional | ✓ Verified | Listed as "No" under Required column | 2026-01-05 |
| Skill names max 64 characters | ✓ Verified | "max 64 characters" | 2026-01-05 |
| Skill descriptions max 1024 characters | ✓ Verified | "max 1024 characters" | 2026-01-05 |
| Skill descriptions max 500 characters | ✗ False | Limit is 1024, not 500 | 2026-01-05 |
| Skill names must use hyphen-case | ✓ Verified | "lowercase letters, numbers, and hyphens only" | 2026-01-05 |
| Skills require SKILL.md filename | ✓ Verified | "exact filename `SKILL.md` (case-sensitive)" | 2026-01-05 |
| Personal skills override project skills | ✓ Verified | "enterprise > personal > project > plugin" precedence | 2026-01-05 |
| SKILL.md should be under 500 lines | ✓ Verified | "Keep `SKILL.md` under 500 lines for optimal performance" | 2026-01-05 |
| Frontmatter must start on line 1 | ✓ Verified | "must start with `---` on line 1 (no blank lines before it)" | 2026-01-05 |
| Frontmatter uses spaces not tabs | ✓ Verified | "use spaces for indentation (not tabs)" | 2026-01-05 |
| allowed-tools field enforces permitted operations | ✓ Verified | "limit which tools Claude can use when a Skill is active" | 2026-01-05 |

---

## Hooks

**Source:** https://code.claude.com/docs/en/hooks.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Exit code 0 means success/allow | ✓ Verified | "Exit code 0: Success" | 2026-01-05 |
| Exit code 1 means block | ✗ False | Exit code 1 is non-blocking error, execution continues | 2026-01-05 |
| Exit code 1 means non-blocking error | ✓ Verified | "Other exit codes: Non-blocking error... Execution continues" | 2026-01-05 |
| Exit code 2 means block | ✓ Verified | "Exit code 2: Blocking error" | 2026-01-05 |
| Hooks only support exit codes 0 and 2 | ✗ False | 0, 1, and 2 are all valid (1 = non-blocking error) | 2026-01-05 |
| Hooks use YAML frontmatter | ✗ False | Hooks are configured in settings.json, not YAML frontmatter | 2026-01-05 |
| Default timeout is 60 seconds | ✓ Verified | "60-second execution limit by default" | 2026-01-05 |
| Timeout is configurable per hook | ✓ Verified | "configurable per command" | 2026-01-05 |
| Matchers are case-sensitive | ✓ Verified | "Pattern to match tool names, case-sensitive" | 2026-01-05 |
| Multiple matching hooks run in parallel | ✓ Verified | "All matching hooks run in parallel" | 2026-01-05 |
| PreToolUse runs before tool calls | ✓ Verified | "Runs after Claude creates tool parameters and before processing" | 2026-01-05 |
| PostToolUse runs after tool completion | ✓ Verified | "Runs immediately after a tool completes successfully" | 2026-01-05 |
| JSON output requires exit code 0 | ✓ Verified | "JSON output is only processed when the hook exits with code 0" | 2026-01-05 |
| CLAUDE_PROJECT_DIR available for all hooks | ✓ Verified | "CLAUDE_PROJECT_DIR environment variable is available" | 2026-01-05 |
| CLAUDE_ENV_FILE only for SessionStart | ✓ Verified | "CLAUDE_ENV_FILE is only available for SessionStart hooks" | 2026-01-05 |
| MCP tools use mcp__server__tool pattern | ✓ Verified | "MCP tools follow the pattern mcp__<server>__<tool>" | 2026-01-05 |
| Hooks support a timeout field in frontmatter | ✗ Contradicted | "hooks use JSON configuration format, not frontmatter" | 2026-01-05 |
| Hooks run in current directory with Claude Code environment | ✓ Verified | "Runs in current directory with Claude Code's environment" | 2026-01-05 |
| SessionStart has exclusive access to CLAUDE_ENV_FILE | ✓ Verified | "CLAUDE_ENV_FILE is only available for SessionStart hooks" | 2026-01-05 |
| Prompt hooks send input to Haiku for evaluation | ✓ Verified | "Send the hook input and your prompt to a fast LLM (Haiku)" | 2026-01-05 |
| Command hooks execute bash commands or scripts | ✓ Verified | "type: command for bash commands" | 2026-01-05 |
| Hook modification requires /hooks menu review | ✓ Verified | "Requires review in /hooks menu for changes to apply" | 2026-01-05 |
| Exit code 2 stderr returned to Claude for most hooks | ~ Partial | "stderr is used as error message and fed back to Claude" (varies by hook type) | 2026-01-05 |
| Exit code 0 stdout injected for UserPromptSubmit/SessionStart | ✓ Verified | "stdout is added to the context" for these hooks | 2026-01-05 |

---

## Commands

**Source:** https://code.claude.com/docs/en/slash-commands.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Commands use $ARGUMENTS for user input | ✓ Verified | "`$ARGUMENTS` placeholder captures all arguments" | 2026-01-05 |
| Commands support positional args ($1, $2) | ✓ Verified | "Access specific arguments individually using positional parameters" | 2026-01-05 |
| `description` field is required | ✗ False | Optional, "Uses the first line from the prompt" if missing | 2026-01-05 |
| `description` field is optional | ✓ Verified | Default provided if missing | 2026-01-05 |
| Commands use Markdown format | ✓ Verified | "Command files support frontmatter" in .md files | 2026-01-05 |
| Project commands override personal commands | ✓ Verified | "project command takes precedence and the user command is silently ignored" | 2026-01-05 |
| Subdirectories affect command name | ✗ False | "Subdirectories appear in the command description but don't affect the command name" | 2026-01-05 |
| Commands support `!` for bash execution | ✓ Verified | "Execute bash commands... using the `!` prefix" | 2026-01-05 |
| Commands support `@` for file references | ✓ Verified | "Include file contents... using the `@` prefix" | 2026-01-05 |
| SlashCommand tool has 15000 char budget | ✓ Verified | "Default limit: 15,000 characters" | 2026-01-05 |
| Commands use YAML frontmatter in markdown files | ✓ Verified | "commands do use YAML frontmatter in markdown files" | 2026-01-05 |

---

## MCP

**Source:** https://code.claude.com/docs/en/mcp.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Project config is in .mcp.json | ✓ Verified | "configurations in a `.mcp.json` file at your project's root" | 2026-01-05 |
| User config is in ~/.claude.json | ✓ Verified | "User and local scope: `~/.claude.json`" | 2026-01-05 |
| MCP uses YAML configuration | ✗ False | Uses JSON (.mcp.json or ~/.claude.json) | 2026-01-05 |
| Three scopes: local, project, user | ✓ Verified | "three different scope levels" | 2026-01-05 |
| Local scope is the default | ✓ Verified | "Local-scoped servers represent the default configuration level" | 2026-01-05 |
| Scope precedence: local > project > user | ✓ Verified | "prioritizing local-scoped servers first, followed by project-scoped servers, and finally user-scoped servers" | 2026-01-05 |
| Project scope requires approval | ✓ Verified | "prompts for approval before using project-scoped servers" | 2026-01-05 |
| Default output limit is 25000 tokens | ✓ Verified | "default maximum is 25,000 tokens" | 2026-01-05 |
| Warning at 10000 tokens | ✓ Verified | "warning when any MCP tool output exceeds 10,000 tokens" | 2026-01-05 |
| Environment variables expand in .mcp.json | ✓ Verified | "supports environment variable expansion in `.mcp.json` files" | 2026-01-05 |
| Supports ${VAR} and ${VAR:-default} syntax | ✓ Verified | Documented expansion syntax | 2026-01-05 |

---

## Agents

**Source:** https://code.claude.com/docs/en/agents.md (via claude-code-guide general knowledge)

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Agents invoked via Task tool | ✓ Verified | subagent_type parameter in Task tool | 2026-01-05 |
| Agents use markdown format | ✓ Verified | .md files in agents directory | 2026-01-05 |
| run_in_background parameter launches agent without waiting | ~ Partial | Exists in Task tool schema but not in public docs | 2026-01-05 |
| Users can request specific subagent by name | ✓ Verified | "Request a specific subagent by mentioning it in your command" | 2026-01-05 |
| Claude delegates based on agent descriptions | ✓ Verified | "Claude Code proactively delegates tasks based on description field" | 2026-01-05 |
| Each agent runs in isolated context | ✓ Verified | "Each subagent operates in its own context" | 2026-01-05 |
| Multiple Task calls in one message run in parallel | ✓ Verified | "Claude can call multiple tools in parallel within a single response" | 2026-01-05 |
| Agents support sequential and parallel execution | ✓ Verified | "Multiple subagents can run concurrently" | 2026-01-05 |
| Agents use .md file format | ✓ Verified | "stored as Markdown files with YAML frontmatter" | 2026-01-05 |

---

## Settings

**Source:** https://code.claude.com/docs/en/interactive-mode.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Claude Code supports custom keyboard shortcuts through the settings.json file | ✗ False | "Keyboard shortcuts vary by platform and terminal" - customization handled at terminal level | 2026-01-05 |
| Output styles configured at ~/.claude/output-styles/ | ✓ Verified | "save these files at user level (~/.claude/output-styles)" | 2026-01-05 |
| Settings changes load on session start not immediately | ✓ Verified | "captures a snapshot of hooks at startup" | 2026-01-05 |

---

## CLI

**Source:** (pending verification)

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Claude Code CLI supports --version flag | ✓ Verified | "claude --version" returns version info | 2026-01-05 |
| /compact accepts optional focus instructions | ✓ Verified | "/compact [instructions] - Compact conversation with optional focus" | 2026-01-05 |

---

## Features

**Source:** (pending verification)

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Claude Code supports real-time collaboration features | ✗ Contradicted | "designed as a personal AI development tool" | 2026-01-05 |

---

## Maintenance

- Re-verify when Claude Code releases major updates
- Add new claims only after querying official documentation
- Include source URL for each section
