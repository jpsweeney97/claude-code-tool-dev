---
paths:
  - ".claude/settings.json"
  - "~/.claude/settings.json"
  - ".claude/settings.local.json"
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

### Available Tools

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

Tools marked "Permission: Yes" require explicit allow rules or user approval.

#### Bash Tool Behavior

**Working directory persists** between commands:
```bash
cd /path/to/dir  # Changes directory
ls               # Runs in /path/to/dir
```

**Environment variables do NOT persist** — each command runs in a fresh shell:
```bash
export MY_VAR=value  # Set in command 1
echo $MY_VAR         # NOT available in command 2
```

**Making environment variables persist:**

1. **Activate before starting Claude Code:**
   ```bash
   conda activate myenv && claude
   ```

2. **Use CLAUDE_ENV_FILE:**
   ```bash
   export CLAUDE_ENV_FILE=/path/to/env-setup.sh
   claude
   ```
   Claude Code sources this file before each Bash command.

3. **Use SessionStart hook:**
   ```json
   {
     "hooks": {
       "SessionStart": [{
         "hooks": [{
           "type": "command",
           "command": "echo 'source ~/.venv/bin/activate' >> \"$CLAUDE_ENV_FILE\""
         }]
       }]
     }
   }
   ```

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

Set via environment or in settings.json `env` field:

```json
{
  "env": {
    "ANTHROPIC_MODEL": "claude-opus-4-5-20251101",
    "DISABLE_TELEMETRY": "1"
  }
}
```

#### Authentication

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for Claude SDK |
| `ANTHROPIC_AUTH_TOKEN` | Custom Authorization header value |
| `ANTHROPIC_CUSTOM_HEADERS` | Custom headers in `Name: Value` format |
| `ANTHROPIC_FOUNDRY_API_KEY` | Microsoft Foundry API key |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API key |

#### Model Configuration

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_MODEL` | Model setting to use |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Override default Haiku model |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Override default Opus model |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Override default Sonnet model |
| `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION` | AWS region for Haiku on Bedrock |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for subagents |

#### Provider Configuration

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_USE_BEDROCK` | Use Amazon Bedrock |
| `CLAUDE_CODE_USE_VERTEX` | Use Google Vertex AI |
| `CLAUDE_CODE_USE_FOUNDRY` | Use Microsoft Foundry |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` | Skip AWS auth (for LLM gateways) |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` | Skip Google auth (for LLM gateways) |

#### Bash Tool Configuration

| Variable | Purpose |
|----------|---------|
| `BASH_DEFAULT_TIMEOUT_MS` | Default timeout for bash commands |
| `BASH_MAX_TIMEOUT_MS` | Maximum timeout model can set |
| `BASH_MAX_OUTPUT_LENGTH` | Max characters before truncation |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Reset to project dir after each command |
| `CLAUDE_CODE_SHELL` | Override shell detection |
| `CLAUDE_CODE_SHELL_PREFIX` | Command prefix for all bash commands |
| `CLAUDE_ENV_FILE` | Script sourced before each Bash command |

#### Output and Display

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Max output tokens for requests |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Token limit for file reads |
| `CLAUDE_CODE_HIDE_ACCOUNT_INFO` | Hide email/org in UI |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` | Disable terminal title updates |
| `MAX_THINKING_TOKENS` | Token budget for extended thinking |

#### MCP Configuration

| Variable | Purpose |
|----------|---------|
| `MCP_TIMEOUT` | Timeout for MCP server startup (ms) |
| `MCP_TOOL_TIMEOUT` | Timeout for MCP tool execution (ms) |
| `MAX_MCP_OUTPUT_TOKENS` | Max tokens in MCP responses (default: 25000) |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Max chars for skill metadata |

#### Proxy and mTLS

| Variable | Purpose |
|----------|---------|
| `HTTP_PROXY` | HTTP proxy server |
| `HTTPS_PROXY` | HTTPS proxy server |
| `NO_PROXY` | Domains/IPs to bypass proxy |
| `CLAUDE_CODE_CLIENT_CERT` | Path to client certificate |
| `CLAUDE_CODE_CLIENT_KEY` | Path to client private key |

#### Telemetry and Debugging

| Variable | Purpose |
|----------|---------|
| `DISABLE_TELEMETRY` | Opt out of telemetry |
| `DISABLE_ERROR_REPORTING` | Opt out of error reporting |
| `DISABLE_AUTOUPDATER` | Disable automatic updates |
| `DISABLE_BUG_COMMAND` | Disable `/bug` command |
| `DISABLE_COST_WARNINGS` | Disable cost warnings |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disable non-essential traffic |

#### Prompt Caching

| Variable | Purpose |
|----------|---------|
| `DISABLE_PROMPT_CACHING` | Disable for all models |
| `DISABLE_PROMPT_CACHING_HAIKU` | Disable for Haiku models |
| `DISABLE_PROMPT_CACHING_OPUS` | Disable for Opus models |
| `DISABLE_PROMPT_CACHING_SONNET` | Disable for Sonnet models |

#### Other

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CONFIG_DIR` | Custom config/data directory |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | Credential refresh interval |
| `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL` | Skip IDE extension auto-install |
| `USE_BUILTIN_RIPGREP` | Set to `0` to use system ripgrep |

Environment variables override settings.json values. Provider variables (`USE_BEDROCK`, etc.) are mutually exclusive.

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

#### strictKnownMarketplaces (Managed Only)

Allowlist of marketplaces users can add. Only in `managed-settings.json`.

| Value | Result |
|-------|--------|
| `undefined` | No restrictions (default) |
| `[]` | Complete lockdown — no marketplaces |
| List of sources | Only matching marketplaces allowed |

**Supported source types:**

```json
// GitHub
{ "source": "github", "repo": "acme-corp/plugins" }
{ "source": "github", "repo": "acme-corp/plugins", "ref": "v2.0" }

// Git
{ "source": "git", "url": "https://gitlab.example.com/plugins.git" }
{ "source": "git", "url": "ssh://git@git.example.com/plugins.git", "ref": "v3.1" }

// URL
{ "source": "url", "url": "https://plugins.example.com/marketplace.json" }
{ "source": "url", "url": "https://cdn.example.com/marketplace.json", "headers": { "Authorization": "Bearer ${TOKEN}" } }

// NPM
{ "source": "npm", "package": "@acme-corp/claude-plugins" }

// File
{ "source": "file", "path": "/usr/local/share/claude/marketplace.json" }

// Directory
{ "source": "directory", "path": "/opt/acme-corp/approved-marketplaces" }
```

**Sources must match exactly** including optional fields like `ref` and `path`.

#### extra vs strict Marketplaces

| Aspect | `extraKnownMarketplaces` | `strictKnownMarketplaces` |
|--------|--------------------------|---------------------------|
| Purpose | Team convenience | Policy enforcement |
| Settings file | Any | Managed only |
| Behavior | Auto-install missing | Block non-allowlisted |
| Can override | Yes | No (highest precedence) |
| Use case | Onboarding | Compliance, security |

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

## Schema Reference

Quick reference for all settings fields, organized by group.

### Permissions Group

| Field | Type | Description |
|-------|------|-------------|
| `permissions.allow` | array | Auto-allowed patterns |
| `permissions.ask` | array | Prompt-required patterns |
| `permissions.deny` | array | Blocked patterns |
| `permissions.defaultMode` | string | Default permission mode |
| `permissions.additionalDirectories` | array | Extra allowed directories |
| `permissions.disableBypassPermissionsMode` | string | Set to `"disable"` to prevent bypass |

### Hooks Group

| Field | Type | Description |
|-------|------|-------------|
| `hooks` | object | Hook configurations by event type |
| `disableAllHooks` | boolean | Disable all hooks |
| `allowManagedHooksOnly` | boolean | Only managed/SDK hooks (managed only) |

### MCP Group

| Field | Type | Description |
|-------|------|-------------|
| `enableAllProjectMcpServers` | boolean | Enable project .mcp.json |
| `enabledMcpjsonServers` | array | Enabled MCP servers |
| `disabledMcpjsonServers` | array | Disabled MCP servers |
| `allowedMcpServers` | array | MCP server allowlist (managed only) |
| `deniedMcpServers` | array | MCP server denylist (managed only) |

### Plugins Group

| Field | Type | Description |
|-------|------|-------------|
| `enabledPlugins` | object | Plugin enable/disable map |
| `extraKnownMarketplaces` | object | Additional marketplaces |
| `strictKnownMarketplaces` | array | Marketplace allowlist (managed only) |

### Display Group

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model override |
| `language` | string | Response language |
| `outputStyle` | string | Output verbosity |
| `alwaysThinkingEnabled` | boolean | Enable extended thinking |
| `respectGitignore` | boolean | Filter .gitignore in picker |
| `statusLine` | object | Status line config |
| `fileSuggestion` | object | Custom file autocomplete |

### Authentication Group

| Field | Type | Description |
|-------|------|-------------|
| `apiKeyHelper` | string | Script to generate auth value |
| `otelHeadersHelper` | string | Script for OTEL headers |
| `forceLoginMethod` | string | Restrict login method |
| `forceLoginOrgUUID` | string | Auto-select organization |
| `awsAuthRefresh` | string | AWS auth refresh script |
| `awsCredentialExport` | string | AWS credential export script |

### Other Group

| Field | Type | Description |
|-------|------|-------------|
| `env` | object | Environment variables for sessions |
| `attribution` | object | Git commit/PR attribution |
| `sandbox` | object | Sandbox configuration |
| `companyAnnouncements` | array | Startup announcements |
| `cleanupPeriodDays` | number | Session cleanup period (default: 30) |

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
