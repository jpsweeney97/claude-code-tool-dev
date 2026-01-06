# Known Claims

Pre-verified claims sourced from official Claude Code documentation.

**Last verified:** 2026-01-05
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

---

## Maintenance

- Re-verify when Claude Code releases major updates
- Add new claims only after querying official documentation
- Include source URL for each section
