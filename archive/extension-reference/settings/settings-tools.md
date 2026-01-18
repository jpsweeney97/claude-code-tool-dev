---
id: settings-tools
topic: Tools Available to Claude
category: settings
tags: [tools, bash, permissions, capabilities]
requires: [settings-overview, settings-permissions]
related_to: [settings-environment-variables, hooks-overview, settings-sandbox]
official_docs: https://code.claude.com/en/settings#tools-available-to-claude
---

# Tools Available to Claude

Claude Code has access to built-in tools for understanding and modifying codebases.

## Tool Reference

| Tool | Description | Permission |
|------|-------------|------------|
| `AskUserQuestion` | Ask multiple choice questions | No |
| `Bash` | Execute shell commands | Yes |
| `BashOutput` | Retrieve background shell output | No |
| `Edit` | Make targeted file edits | Yes |
| `ExitPlanMode` | Prompt user to exit plan mode | Yes |
| `Glob` | Find files by pattern | No |
| `Grep` | Search file contents | No |
| `KillShell` | Kill background shell by ID | No |
| `NotebookEdit` | Modify Jupyter notebook cells | Yes |
| `Read` | Read file contents | No |
| `Skill` | Execute a skill or slash command | Yes |
| `Task` | Run a subagent | No |
| `TodoWrite` | Manage task lists | No |
| `WebFetch` | Fetch URL content | Yes |
| `WebSearch` | Perform web searches | Yes |
| `Write` | Create or overwrite files | Yes |

## Permission Configuration

Configure tool permissions via `/allowed-tools` or in settings.json:

```json
{
  "permissions": {
    "allow": ["Bash(npm run:*)"],
    "deny": ["WebFetch", "Bash(curl:*)"]
  }
}
```

## Bash Tool Behavior

### Working Directory Persistence

Working directory **persists** between commands:

```bash
cd /path/to/dir  # Changes directory
ls               # Runs in /path/to/dir
```

To reset after each command, set:

```
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1
```

### Environment Variable Non-Persistence

Environment variables **do NOT persist**:

```bash
export MY_VAR=value  # Set in command 1
echo $MY_VAR         # NOT available in command 2
```

Each Bash command runs in a fresh shell environment.

### Making Environment Variables Persist

**Option 1: Activate before starting Claude Code**

```bash
conda activate myenv
claude
```

**Option 2: Use CLAUDE_ENV_FILE**

```bash
export CLAUDE_ENV_FILE=/path/to/env-setup.sh
claude
```

Where `env-setup.sh` contains:

```bash
conda activate myenv
export MY_VAR=value
```

Claude Code sources this file before each Bash command.

**Option 3: SessionStart hook**

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "once": true,
      "hooks": [{
        "type": "command",
        "command": "echo 'source ~/.venv/bin/activate' >> \"$CLAUDE_ENV_FILE\""
      }]
    }]
  }
}
```

The hook appends to `$CLAUDE_ENV_FILE`, which is sourced before each Bash command.

## Extending Tools with Hooks

Run custom commands before or after any tool:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit",
      "hooks": [{
        "type": "command",
        "command": "ruff format $CLAUDE_FILE_PATHS"
      }]
    }]
  }
}
```

## Key Points

- Tools marked "Permission: Yes" require explicit allow or user approval
- Bash working directory persists, environment variables do not
- Use `CLAUDE_ENV_FILE` or SessionStart hooks for persistent environment
- Extend tool behavior with PreToolUse/PostToolUse hooks
