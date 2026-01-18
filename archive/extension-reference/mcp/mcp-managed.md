---
id: mcp-managed
topic: Managed MCP Configuration
category: mcp
tags: [managed, enterprise, restrictions, security, allowlist, denylist]
requires: [mcp-overview]
related_to: [security-mcp-restrictions, settings-scopes]
official_docs: https://code.claude.com/en/mcp
---

# Managed MCP Configuration

Enterprise deployments can control MCP server access via two options:
1. **Exclusive control** with `managed-mcp.json` — Fixed servers, no user customization
2. **Policy-based control** with allowlists/denylists — User servers within policy constraints

**Choosing between options:** Use Option 1 when you want to deploy a fixed set of servers with no user customization. Use Option 2 when you want to allow users to add their own servers within policy constraints.

## Option 1: Exclusive Control with managed-mcp.json

Deploy to system-wide directory (requires admin privileges):

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-mcp.json` |
| Linux/WSL | `/etc/claude-code/managed-mcp.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-mcp.json` |

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    },
    "company-internal": {
      "type": "stdio",
      "command": "/usr/local/bin/company-mcp-server",
      "args": ["--config", "/etc/company/mcp-config.json"],
      "env": {
        "COMPANY_API_URL": "https://internal.company.com"
      }
    }
  }
}
```

When deployed, users cannot add, modify, or use any other MCP servers.

## Option 2: Policy-Based Control

Use `allowedMcpServers` and `deniedMcpServers` in managed settings file.

### Restriction Types

Each entry must have **exactly one** of:

| Type | Matches | Example |
|------|---------|---------|
| `serverName` | Configured server name | `{"serverName": "github"}` |
| `serverCommand` | Exact command array | `{"serverCommand": ["npx", "-y", "pkg"]}` |
| `serverUrl` | URL pattern (wildcards) | `{"serverUrl": "https://*.company.com/*"}` |

### Command Matching (stdio servers)

- Command arrays must match **exactly** — command and all arguments in order
- `["npx", "-y", "server"]` does NOT match `["npx", "server"]`
- When allowlist has `serverCommand` entries, stdio servers must match one

### Non-stdio Server Behavior

- Remote servers (HTTP, SSE, WebSocket) use URL-based matching when `serverUrl` entries exist
- If no URL entries exist, remote servers fall back to name-based matching
- Command restrictions do not apply to remote servers

### URL Matching (remote servers)

Wildcards supported:
- `https://mcp.company.com/*` — All paths on domain
- `https://*.example.com/*` — Any subdomain
- `http://localhost:*/*` — Any port on localhost

When allowlist has `serverUrl` entries, remote servers must match one.

### Example Configuration

```json
{
  "allowedMcpServers": [
    {"serverName": "github"},
    {"serverCommand": ["npx", "-y", "@modelcontextprotocol/server-filesystem"]},
    {"serverUrl": "https://mcp.company.com/*"}
  ],
  "deniedMcpServers": [
    {"serverName": "dangerous-server"},
    {"serverUrl": "https://*.untrusted.com/*"}
  ]
}
```

### Allowlist Behavior

| Value | Result |
|-------|--------|
| `undefined` | No restrictions (default) |
| `[]` | Complete lockdown — no servers allowed |
| List of entries | Only matching servers allowed |

### Denylist Behavior

| Value | Result |
|-------|--------|
| `undefined` | No servers blocked (default) |
| `[]` | No servers blocked |
| List of entries | Matching servers blocked |

### Outcome Examples

**URL-only allowlist:**
```json
{"allowedMcpServers": [
  {"serverUrl": "https://mcp.company.com/*"},
  {"serverUrl": "https://*.internal.corp/*"}
]}
```
- HTTP at `https://mcp.company.com/api`: ✅ Allowed (matches URL)
- HTTP at `https://api.internal.corp/mcp`: ✅ Allowed (wildcard subdomain)
- HTTP at `https://external.com/mcp`: ❌ Blocked (no URL match)
- Stdio with any command: ❌ Blocked (no name/command entries)

**Command-only allowlist:**
```json
{"allowedMcpServers": [
  {"serverCommand": ["npx", "-y", "approved-package"]}
]}
```
- Stdio with `["npx", "-y", "approved-package"]`: ✅ Allowed
- Stdio with `["node", "server.js"]`: ❌ Blocked (no command match)
- HTTP named "my-api": ❌ Blocked (no name entries)

**Mixed name + command allowlist:**
```json
{"allowedMcpServers": [
  {"serverName": "github"},
  {"serverCommand": ["npx", "-y", "approved-package"]}
]}
```
- Stdio named "local-tool" with `["npx", "-y", "approved-package"]`: ✅ Allowed (command match)
- Stdio named "local-tool" with `["node", "server.js"]`: ❌ Blocked (command entries exist, no match)
- Stdio named "github" with `["node", "server.js"]`: ❌ Blocked (stdio must match commands when command entries exist)
- HTTP named "github": ✅ Allowed (name match)
- HTTP named "other-api": ❌ Blocked (no name match)

**Name-only allowlist:**
```json
{"allowedMcpServers": [
  {"serverName": "github"},
  {"serverName": "internal-tool"}
]}
```
- Stdio named "github" with any command: ✅ Allowed (no command restrictions)
- HTTP named "github": ✅ Allowed (name match)
- Any server named "other": ❌ Blocked (no name match)

## Precedence Rules

- **Denylist takes absolute precedence** — Blocked even if on allowlist
- Options 1 and 2 can combine — managed-mcp.json provides servers, allowlists/denylists filter them
- A server passes if it matches name OR command OR URL pattern (unless denied)

## managed-mcp.json Interaction

When `managed-mcp.json` exists:
- Users cannot add MCP servers through `claude mcp add` or configuration files
- The `allowedMcpServers` and `deniedMcpServers` settings still apply to filter which managed servers are actually loaded

## Key Points

- Option 1: managed-mcp.json for exclusive control (admin-deployed)
- Option 2: allowlists/denylists for policy-based control
- System paths require admin privileges
- Command matching is exact (array order matters)
- URL patterns support wildcards
- Deny always overrides allow
