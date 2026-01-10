---
id: settings-sandbox
topic: Sandbox Configuration
category: settings
tags: [sandbox, security, isolation, network]
requires: [settings-overview]
related_to: [settings-permissions, security-managed]
official_docs: https://code.claude.com/en/settings
---

# Sandbox Configuration

Sandbox isolates Claude Code from the system for security.

## Sandbox Schema

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker", "git"],
    "allowUnsandboxedCommands": false,
    "network": {
      "allowUnixSockets": ["/var/run/docker.sock"],
      "allowLocalBinding": true,
      "httpProxyPort": 8080,
      "socksProxyPort": 1080
    },
    "enableWeakerNestedSandbox": true
  }
}
```

## Important Note

**Filesystem and network restrictions** are configured via Read, Edit, and WebFetch permission rules, not via sandbox settings.

Use:
- `Read` deny rules to block file/directory reading
- `Edit` allow/deny rules to control write access
- `WebFetch` allow/deny rules to control network domains

## Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Enable sandboxing (macOS/Linux only). Default: false |
| `autoAllowBashIfSandboxed` | boolean | Auto-allow Bash when sandboxed |
| `excludedCommands` | array | Commands to run outside sandbox |
| `allowUnsandboxedCommands` | boolean | Allow `dangerouslyDisableSandbox` escape hatch. When `false`, all commands must run sandboxed or be in `excludedCommands`. Useful for enterprise policies. |
| `network.allowUnixSockets` | array | Unix sockets to allow (for SSH agents, etc.) |
| `network.allowLocalBinding` | boolean | Allow local port binding (macOS only) |
| `network.httpProxyPort` | number | HTTP proxy port (bring your own proxy) |
| `network.socksProxyPort` | number | SOCKS5 proxy port (bring your own proxy) |
| `enableWeakerNestedSandbox` | boolean | Enable weaker sandbox for unprivileged Docker (Linux only). **Reduces security.** |

## Key Points

- Sandbox provides security isolation
- Some commands can be excluded
- Network access is configurable
- Nested sandboxing for containers
