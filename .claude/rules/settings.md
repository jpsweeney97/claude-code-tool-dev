---
paths:
  - .claude/settings.json
  - .claude/settings.local.json
---

# Settings Configuration

Settings control Claude Code behavior: permissions, hooks, sandbox, model selection, and more. Configuration is JSON-based with a strict precedence hierarchy.

## File Locations & Precedence

Settings are loaded in precedence order (highest first):

| Scope | Location | Use Case |
|-------|----------|----------|
| **Managed** | System directories (see below) | IT/enterprise deployment |
| **Command line** | CLI flags (e.g., `--model`) | Temporary session overrides |
| **Local project** | `.claude/settings.local.json` | Personal project settings (gitignored) |
| **Shared project** | `.claude/settings.json` | Team settings (committed to git) |
| **User** | `~/.claude/settings.json` | Personal global settings |

### Managed Settings Locations

- **macOS**: `/Library/Application Support/ClaudeCode/managed-settings.json`
- **Linux/WSL**: `/etc/claude-code/managed-settings.json`
- **Windows**: `C:\Program Files\ClaudeCode\managed-settings.json`

### MCP Server Configuration

MCP servers use separate files:

| Scope | Location |
|-------|----------|
| User | `~/.claude.json` |
| Project | `.mcp.json` |
| Managed | `managed-mcp.json` (system directories) |

## Configuration Fields

### Core Settings

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Override default model (e.g., `"claude-opus-4-5-20251101"`) |
| `language` | string | Preferred response language (`"japanese"`, `"spanish"`) |
| `alwaysThinkingEnabled` | boolean | Enable extended thinking by default |
| `outputStyle` | string | Output style name (e.g., `"Explanatory"`) |
| `cleanupPeriodDays` | number | Delete sessions older than N days (default: 30) |
| `respectGitignore` | boolean | @ file picker respects .gitignore (default: true) |
| `companyAnnouncements` | array | Startup messages (multiple cycle randomly) |

### Permission Settings

```json
{
  "permissions": {
    "allow": ["Rule1", "Rule2"],
    "ask": ["Rule3"],
    "deny": ["Rule4"],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "default",
    "disableBypassPermissionsMode": "disable"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `allow` | array | Rules to auto-approve |
| `ask` | array | Rules requiring confirmation |
| `deny` | array | Rules to block (highest precedence) |
| `additionalDirectories` | array | Extra directories to allow access |
| `defaultMode` | string | Default permission mode |
| `disableBypassPermissionsMode` | string | Set to `"disable"` to prevent bypass mode |

**Note:** The `ignorePatterns` configuration is deprecated. Use `permissions.deny` rules instead for file exclusion.

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Prompts for permission on first use |
| `acceptEdits` | Auto-accepts file edits for session |
| `plan` | Analyze only, no modifications |
| `dontAsk` | Auto-denies unless pre-approved |
| `bypassPermissions` | Skips all prompts (requires safe environment) |
| `ignore` | No permissions enforced |

### Permission Rule Syntax

**Bash commands**:
```json
"Bash(npm run build)"       // Exact match
"Bash(npm run test:*)"      // Prefix match (:* at end only)
"Bash(npm *)"               // Glob-style wildcard
"Bash(git * main)"          // Multiple parts with wildcards
```

**Note:** Bash rules use glob-style matching, not regex. Patterns can be bypassed with shell features (options, env vars, redirects, subshells). Use PreToolUse hooks for robust command validation.

**File operations**:
```json
"Read(src/**)"              // Relative to settings file
"Read(//absolute/path)"     // Absolute path (// prefix)
"Read(~/path)"              // Home directory
"Edit(src/*.ts)"            // Glob patterns
```

**Web access**:
```json
"WebFetch(domain:example.com)"
"WebFetch(domain:*.github.com)"
```

**MCP tools**:
```json
"mcp__servername"           // All tools from server
"mcp__servername__toolname" // Specific tool
```

**Subagents**:
```json
"Task(Explore)"             // Specific subagent
"Task(Plan)"                // Plan subagent
```

### Hook Settings

Configure hooks inline in settings.json:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/validate-bash.py",
            "timeout": 30
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/context-injector.sh"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false,
  "allowManagedHooksOnly": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `disableAllHooks` | boolean | Disable all hooks |
| `allowManagedHooksOnly` | boolean | Only run managed/SDK hooks (managed settings only) |

See `hooks.md` for event types, matchers, and exit codes.

### Sandbox Settings

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker", "git"],
    "allowUnsandboxedCommands": true,
    "network": {
      "allowUnixSockets": ["~/.ssh/agent-socket"],
      "allowLocalBinding": false,
      "httpProxyPort": 8080,
      "socksProxyPort": 1080
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Enable sandbox (macOS/Linux only, default: false) |
| `autoAllowBashIfSandboxed` | boolean | Auto-approve bash when sandboxed (default: true) |
| `excludedCommands` | array | Commands to run outside sandbox |
| `allowUnsandboxedCommands` | boolean | Allow dangerouslyDisableSandbox parameter |
| `enableWeakerNestedSandbox` | boolean | Weaker sandbox for unprivileged Docker (Linux only, reduces security) |
| `network.allowUnixSockets` | array | Unix socket paths accessible |
| `network.allowLocalBinding` | boolean | Allow localhost binding |

### Attribution Settings

```json
{
  "attribution": {
    "commit": "Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
    "pr": ""
  }
}
```

Empty string hides attribution. Set per-type (commit vs PR).

### Environment Variables

```json
{
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "app:*",
    "ANTHROPIC_MODEL": "claude-opus-4-5-20251101"
  }
}
```

Applied to every session. Common variables:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for Claude SDK |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Max output tokens |
| `BASH_DEFAULT_TIMEOUT_MS` | Bash timeout |
| `BASH_MAX_OUTPUT_LENGTH` | Max bash output chars |
| `CLAUDE_ENV_FILE` | Shell script sourced before each Bash command |
| `DISABLE_TELEMETRY` | Opt out of telemetry |

**Note:** `CLAUDE_ENV_FILE` is useful for persistent environment setup (e.g., activating virtual environments). Set it before starting Claude Code or via a SessionStart hook.

### Plugin Settings

```json
{
  "enabledPlugins": {
    "plugin-name@marketplace": true,
    "other-plugin@marketplace": false
  },
  "extraKnownMarketplaces": {
    "acme-tools": { "source": { "source": "github", "repo": "acme/plugins" } }
  },
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": ["server1", "server2"],
  "disabledMcpjsonServers": ["blocked-server"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `enabledPlugins` | object | Map of `"plugin@marketplace": boolean` |
| `extraKnownMarketplaces` | object | Additional marketplaces for team onboarding |
| `strictKnownMarketplaces` | array | Marketplace allowlist (managed settings only) |
| `enableAllProjectMcpServers` | boolean | Auto-approve project .mcp.json servers |
| `enabledMcpjsonServers` | array | MCP servers to enable |
| `disabledMcpjsonServers` | array | MCP servers to disable |
| `allowedMcpServers` | array | MCP server allowlist (managed settings only) |
| `deniedMcpServers` | array | MCP server denylist (managed settings only) |

### Custom Scripts

**Status line**:
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

**File suggestion**:
```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  }
}
```

**API key helper**:
```json
{
  "apiKeyHelper": "~/.claude/get-api-key.sh"
}
```

### Authentication Settings

| Field | Type | Description |
|-------|------|-------------|
| `apiKeyHelper` | string | Script to generate auth value for API requests |
| `otelHeadersHelper` | string | Script to generate OpenTelemetry headers |
| `forceLoginMethod` | string | Restrict to `"claudeai"` or `"console"` accounts |
| `forceLoginOrgUUID` | string | Auto-select organization (requires `forceLoginMethod`) |
| `awsAuthRefresh` | string | Script to refresh AWS credentials |
| `awsCredentialExport` | string | Script to export AWS credentials as JSON |

### Deprecated Settings

| Field | Replacement |
|-------|-------------|
| `includeCoAuthoredBy` | Use `attribution` instead |

## Complete Example

```json
{
  "model": "claude-opus-4-5-20251101",
  "alwaysThinkingEnabled": true,
  "outputStyle": "Explanatory",

  "permissions": {
    "allow": [
      "Read(src/**)",
      "Edit(src/**)",
      "Bash(npm run:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "WebFetch(domain:api.github.com)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git commit:*)"
    ],
    "deny": [
      "Read(.env)",
      "Read(secrets/**)",
      "Bash(rm -rf:*)"
    ],
    "defaultMode": "default"
  },

  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/bash-validator.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "ruff format --stdin-filename $file"
          }
        ]
      }
    ]
  },

  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker"]
  },

  "attribution": {
    "commit": "Co-Authored-By: Claude <noreply@anthropic.com>",
    "pr": ""
  },

  "env": {
    "NODE_ENV": "development"
  }
}
```

## Key Behaviors

### Precedence Rules

1. **Deny always wins**: Deny rules override allow and ask
2. **Managed overrides all**: IT-deployed settings cannot be overridden
3. **Local overrides shared**: `.claude/settings.local.json` beats `.claude/settings.json`

### Hook Execution

- Hooks execute in parallel (don't assume order)
- Identical commands are deduplicated
- Settings captured at startup (changes require reload)
- Default timeout: 60 seconds

### Bash Pattern Limitations

- `:*` prefix matching only works at end
- Patterns can be bypassed with options, env vars, redirects
- Use hooks for robust command validation

## Anti-patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Broad allow rules | Security risk | Be specific (`src/**` not `**`) |
| Relying only on Bash patterns | Bypassable | Add PreToolUse hook validation |
| Committing secrets in settings | Security risk | Use `.claude/settings.local.json` |
| Forgetting deny precedence | Unexpected blocks | Check deny rules first |
| Editing settings mid-session | No effect | Restart Claude Code |

## Compliance Checklist

Before deploying settings, verify:

- [ ] Permission rules use correct syntax for each tool type
- [ ] Deny rules checked for unintended blocks
- [ ] Hook commands are executable and accessible
- [ ] Hook timeouts set appropriately (default 60s)
- [ ] Sandbox settings match security requirements
- [ ] Environment variables don't contain secrets
- [ ] Local settings (.local.json) used for personal config
- [ ] Shared settings (.claude/settings.json) appropriate for team

## See Also

- **skills.md** — Skill development conventions
- **commands.md** — Command development conventions
- **agents.md** — Agent/subagent development and configuration (user: `~/.claude/agents/`, project: `.claude/agents/`)
- **hooks.md** — Hook event types, exit codes, matchers
- **plugins.md** — Plugin enable/disable configuration
- **mcp-servers.md** — MCP server configuration in `.mcp.json`

## References

- [Settings Overview](https://code.claude.com/docs/en/settings)
- [Permissions](https://code.claude.com/docs/en/permissions)
- [Hooks](https://code.claude.com/docs/en/hooks)
- @.claude/skills/auditing-tool-designs/references/fallback-specs.md — Permission modes and configuration file locations
