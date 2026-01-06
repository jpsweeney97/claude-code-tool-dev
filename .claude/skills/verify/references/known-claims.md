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

| Claim | Verdict | Evidence |
|-------|---------|----------|
| `name` field is required in frontmatter | ✓ Verified | "must include a `name` and `description`" |
| `description` field is required in frontmatter | ✓ Verified | "must include a `name` and `description`" |
| `license` field is required in frontmatter | ✗ False | Not listed as required; only `name` and `description` are required |
| `allowed-tools` field is optional | ✓ Verified | Listed as "No" under Required column |
| `model` field is optional | ✓ Verified | Listed as "No" under Required column |
| Skill names max 64 characters | ✓ Verified | "max 64 characters" |
| Skill descriptions max 1024 characters | ✓ Verified | "max 1024 characters" |
| Skill descriptions max 500 characters | ✗ False | Limit is 1024, not 500 |
| Skill names must use hyphen-case | ✓ Verified | "lowercase letters, numbers, and hyphens only" |
| Skills require SKILL.md filename | ✓ Verified | "exact filename `SKILL.md` (case-sensitive)" |
| Personal skills override project skills | ✓ Verified | "enterprise > personal > project > plugin" precedence |
| SKILL.md should be under 500 lines | ✓ Verified | "Keep `SKILL.md` under 500 lines for optimal performance" |
| Frontmatter must start on line 1 | ✓ Verified | "must start with `---` on line 1 (no blank lines before it)" |
| Frontmatter uses spaces not tabs | ✓ Verified | "use spaces for indentation (not tabs)" |
| allowed-tools field enforces permitted operations | ✓ Verified | "limit which tools Claude can use when a Skill is active" |

---

## Hooks

**Source:** https://code.claude.com/docs/en/hooks.md

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Exit code 0 means success/allow | ✓ Verified | "Exit code 0: Success" |
| Exit code 1 means block | ✗ False | Exit code 1 is non-blocking error, execution continues |
| Exit code 1 means non-blocking error | ✓ Verified | "Other exit codes: Non-blocking error... Execution continues" |
| Exit code 2 means block | ✓ Verified | "Exit code 2: Blocking error" |
| Hooks only support exit codes 0 and 2 | ✗ False | 0, 1, and 2 are all valid (1 = non-blocking error) |
| Hooks use YAML frontmatter | ✗ False | Hooks are configured in settings.json, not YAML frontmatter |
| Default timeout is 60 seconds | ✓ Verified | "60-second execution limit by default" |
| Timeout is configurable per hook | ✓ Verified | "configurable per command" |
| Matchers are case-sensitive | ✓ Verified | "Pattern to match tool names, case-sensitive" |
| Multiple matching hooks run in parallel | ✓ Verified | "All matching hooks run in parallel" |
| PreToolUse runs before tool calls | ✓ Verified | "Runs after Claude creates tool parameters and before processing" |
| PostToolUse runs after tool completion | ✓ Verified | "Runs immediately after a tool completes successfully" |
| JSON output requires exit code 0 | ✓ Verified | "JSON output is only processed when the hook exits with code 0" |
| CLAUDE_PROJECT_DIR available for all hooks | ✓ Verified | "CLAUDE_PROJECT_DIR environment variable is available" |
| CLAUDE_ENV_FILE only for SessionStart | ✓ Verified | "CLAUDE_ENV_FILE is only available for SessionStart hooks" |
| MCP tools use mcp__server__tool pattern | ✓ Verified | "MCP tools follow the pattern mcp__<server>__<tool>" |
| Hooks support a timeout field in frontmatter | ✗ Contradicted | "hooks use JSON configuration format, not frontmatter" |
| Hooks run in current directory with Claude Code environment | ✓ Verified | "Runs in current directory with Claude Code's environment" |
| SessionStart has exclusive access to CLAUDE_ENV_FILE | ✓ Verified | "CLAUDE_ENV_FILE is only available for SessionStart hooks" |
| Prompt hooks send input to Haiku for evaluation | ✓ Verified | "Send the hook input and your prompt to a fast LLM (Haiku)" |
| Command hooks execute bash commands or scripts | ✓ Verified | "type: command for bash commands" |
| Hook modification requires /hooks menu review | ✓ Verified | "Requires review in /hooks menu for changes to apply" |
| Exit code 2 stderr returned to Claude for most hooks | ~ Partial | "stderr is used as error message and fed back to Claude" (varies by hook type) |
| Exit code 0 stdout injected for UserPromptSubmit/SessionStart | ✓ Verified | "stdout is added to the context" for these hooks |

---

## Commands

**Source:** https://code.claude.com/docs/en/slash-commands.md

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Commands use $ARGUMENTS for user input | ✓ Verified | "`$ARGUMENTS` placeholder captures all arguments" |
| Commands support positional args ($1, $2) | ✓ Verified | "Access specific arguments individually using positional parameters" |
| `description` field is required | ✗ False | Optional, "Uses the first line from the prompt" if missing |
| `description` field is optional | ✓ Verified | Default provided if missing |
| Commands use Markdown format | ✓ Verified | "Command files support frontmatter" in .md files |
| Project commands override personal commands | ✓ Verified | "project command takes precedence and the user command is silently ignored" |
| Subdirectories affect command name | ✗ False | "Subdirectories appear in the command description but don't affect the command name" |
| Commands support `!` for bash execution | ✓ Verified | "Execute bash commands... using the `!` prefix" |
| Commands support `@` for file references | ✓ Verified | "Include file contents... using the `@` prefix" |
| SlashCommand tool has 15000 char budget | ✓ Verified | "Default limit: 15,000 characters" |
| Commands use YAML frontmatter in markdown files | ✓ Verified | "commands do use YAML frontmatter in markdown files" |

---

## MCP

**Source:** https://code.claude.com/docs/en/mcp.md

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Project config is in .mcp.json | ✓ Verified | "configurations in a `.mcp.json` file at your project's root" |
| User config is in ~/.claude.json | ✓ Verified | "User and local scope: `~/.claude.json`" |
| MCP uses YAML configuration | ✗ False | Uses JSON (.mcp.json or ~/.claude.json) |
| Three scopes: local, project, user | ✓ Verified | "three different scope levels" |
| Local scope is the default | ✓ Verified | "Local-scoped servers represent the default configuration level" |
| Scope precedence: local > project > user | ✓ Verified | "prioritizing local-scoped servers first, followed by project-scoped servers, and finally user-scoped servers" |
| Project scope requires approval | ✓ Verified | "prompts for approval before using project-scoped servers" |
| Default output limit is 25000 tokens | ✓ Verified | "default maximum is 25,000 tokens" |
| Warning at 10000 tokens | ✓ Verified | "warning when any MCP tool output exceeds 10,000 tokens" |
| Environment variables expand in .mcp.json | ✓ Verified | "supports environment variable expansion in `.mcp.json` files" |
| Supports ${VAR} and ${VAR:-default} syntax | ✓ Verified | Documented expansion syntax |

---

## Agents

**Source:** https://code.claude.com/docs/en/agents.md (via claude-code-guide general knowledge)

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Agents invoked via Task tool | ✓ Verified | subagent_type parameter in Task tool |
| Agents use markdown format | ✓ Verified | .md files in agents directory |
| run_in_background parameter launches agent without waiting | ~ Partial | Exists in Task tool schema but not in public docs |
| Users can request specific subagent by name | ✓ Verified | "Request a specific subagent by mentioning it in your command" |
| Claude delegates based on agent descriptions | ✓ Verified | "Claude Code proactively delegates tasks based on description field" |
| Each agent runs in isolated context | ✓ Verified | "Each subagent operates in its own context" |
| Multiple Task calls in one message run in parallel | ✓ Verified | "Claude can call multiple tools in parallel within a single response" |
| Agents support sequential and parallel execution | ✓ Verified | "Multiple subagents can run concurrently" |
| Agents use .md file format | ✓ Verified | "stored as Markdown files with YAML frontmatter" |

---

## Settings

**Source:** https://code.claude.com/docs/en/interactive-mode.md

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Claude Code supports custom keyboard shortcuts through the settings.json file | ✗ False | "Keyboard shortcuts vary by platform and terminal" - customization handled at terminal level |
| Output styles configured at ~/.claude/output-styles/ | ✓ Verified | "save these files at user level (~/.claude/output-styles)" |
| Settings changes load on session start not immediately | ✓ Verified | "captures a snapshot of hooks at startup" |

---

## CLI

**Source:** (pending verification)

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Claude Code CLI supports --version flag | ✓ Verified | "claude --version" returns version info |
| /compact accepts optional focus instructions | ✓ Verified | "/compact [instructions] - Compact conversation with optional focus" |

---

## Features

**Source:** (pending verification)

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Claude Code supports real-time collaboration features | ✗ Contradicted | "designed as a personal AI development tool" |

---

## Maintenance

- Re-verify when Claude Code releases major updates
- Add new claims only after querying official documentation
- Include source URL for each section
