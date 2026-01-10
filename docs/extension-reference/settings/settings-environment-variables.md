---
id: settings-environment-variables
topic: Environment Variables
category: settings
tags: [environment, variables, configuration, env]
requires: [settings-overview]
related_to: [settings-schema, settings-authentication]
official_docs: https://code.claude.com/en/settings#environment-variables
---

# Environment Variables

Control Claude Code behavior via environment variables.

## Alternative: settings.json

All environment variables can also be set in `settings.json` via the `env` field:

```json
{
  "env": {
    "DISABLE_TELEMETRY": "1",
    "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929"
  }
}
```

## Authentication Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for Claude SDK |
| `ANTHROPIC_AUTH_TOKEN` | Custom Authorization header value (prefixed with `Bearer `) |
| `ANTHROPIC_CUSTOM_HEADERS` | Custom headers in `Name: Value` format |
| `ANTHROPIC_FOUNDRY_API_KEY` | Microsoft Foundry API key |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API key |

## Model Configuration

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_MODEL` | Model setting to use |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Override default Haiku model |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Override default Opus model |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Override default Sonnet model |
| `ANTHROPIC_SMALL_FAST_MODEL` | (Deprecated) Haiku-class model for background tasks |
| `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION` | AWS region for Haiku-class model on Bedrock |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for subagents |

## Provider Configuration

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_USE_BEDROCK` | Use Amazon Bedrock |
| `CLAUDE_CODE_USE_VERTEX` | Use Google Vertex AI |
| `CLAUDE_CODE_USE_FOUNDRY` | Use Microsoft Foundry |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` | Skip AWS auth (for LLM gateways) |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` | Skip Google auth (for LLM gateways) |
| `CLAUDE_CODE_SKIP_FOUNDRY_AUTH` | Skip Azure auth (for LLM gateways) |

## Vertex AI Region Overrides

| Variable | Purpose |
|----------|---------|
| `VERTEX_REGION_CLAUDE_3_5_HAIKU` | Region for Claude 3.5 Haiku |
| `VERTEX_REGION_CLAUDE_3_7_SONNET` | Region for Claude 3.7 Sonnet |
| `VERTEX_REGION_CLAUDE_4_0_OPUS` | Region for Claude 4.0 Opus |
| `VERTEX_REGION_CLAUDE_4_0_SONNET` | Region for Claude 4.0 Sonnet |
| `VERTEX_REGION_CLAUDE_4_1_OPUS` | Region for Claude 4.1 Opus |

## Bash Tool Configuration

| Variable | Purpose |
|----------|---------|
| `BASH_DEFAULT_TIMEOUT_MS` | Default timeout for bash commands |
| `BASH_MAX_TIMEOUT_MS` | Maximum timeout model can set |
| `BASH_MAX_OUTPUT_LENGTH` | Max characters before middle-truncation |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Reset to project dir after each command |
| `CLAUDE_CODE_SHELL` | Override shell detection |
| `CLAUDE_CODE_SHELL_PREFIX` | Command prefix for all bash commands |
| `CLAUDE_ENV_FILE` | Path to shell script sourced before each Bash command |

## Output and Display

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Max output tokens for requests |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Token limit for file reads |
| `CLAUDE_CODE_HIDE_ACCOUNT_INFO` | Hide email/org in UI (for streaming) |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` | Disable automatic terminal title updates |
| `MAX_THINKING_TOKENS` | Token budget for extended thinking |

## MCP Configuration

| Variable | Purpose |
|----------|---------|
| `MCP_TIMEOUT` | Timeout for MCP server startup (ms) |
| `MCP_TOOL_TIMEOUT` | Timeout for MCP tool execution (ms) |
| `MAX_MCP_OUTPUT_TOKENS` | Max tokens in MCP responses (default: 25000) |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Max chars for skill metadata (default: 15000) |

## Proxy Configuration

| Variable | Purpose |
|----------|---------|
| `HTTP_PROXY` | HTTP proxy server |
| `HTTPS_PROXY` | HTTPS proxy server |
| `NO_PROXY` | Domains/IPs to bypass proxy |

## mTLS Configuration

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_CLIENT_CERT` | Path to client certificate |
| `CLAUDE_CODE_CLIENT_KEY` | Path to client private key |
| `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE` | Passphrase for encrypted key |

## Telemetry and Debugging

| Variable | Purpose |
|----------|---------|
| `DISABLE_TELEMETRY` | Opt out of Statsig telemetry |
| `DISABLE_ERROR_REPORTING` | Opt out of Sentry error reporting |
| `DISABLE_AUTOUPDATER` | Disable automatic updates |
| `DISABLE_BUG_COMMAND` | Disable `/bug` command |
| `DISABLE_COST_WARNINGS` | Disable cost warning messages |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS` | Disable non-critical model calls |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disable all non-essential traffic |

## Prompt Caching

| Variable | Purpose |
|----------|---------|
| `DISABLE_PROMPT_CACHING` | Disable for all models |
| `DISABLE_PROMPT_CACHING_HAIKU` | Disable for Haiku models |
| `DISABLE_PROMPT_CACHING_OPUS` | Disable for Opus models |
| `DISABLE_PROMPT_CACHING_SONNET` | Disable for Sonnet models |

## Other Configuration

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CONFIG_DIR` | Custom config/data directory |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | Credential refresh interval |
| `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` | OpenTelemetry header refresh interval |
| `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL` | Skip IDE extension auto-install |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | Disable anthropic-beta headers |
| `USE_BUILTIN_RIPGREP` | Set to `0` to use system ripgrep |

## Key Points

- Environment variables override settings.json values
- Use `env` field in settings.json for team-shared configuration
- Most variables set to `1` to enable, `0` to disable
- Provider variables (`USE_BEDROCK`, etc.) are mutually exclusive
