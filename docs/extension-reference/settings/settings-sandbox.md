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

## Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Enable sandboxing |
| `autoAllowBashIfSandboxed` | boolean | Auto-allow Bash when sandboxed |
| `excludedCommands` | array | Commands to run outside sandbox |
| `allowUnsandboxedCommands` | boolean | Allow non-sandboxed execution |
| `network.allowUnixSockets` | array | Unix sockets to allow |
| `network.allowLocalBinding` | boolean | Allow local port binding |
| `network.httpProxyPort` | number | HTTP proxy port |
| `network.socksProxyPort` | number | SOCKS proxy port |
| `enableWeakerNestedSandbox` | boolean | Allow weaker nested sandboxing |

## Key Points

- Sandbox provides security isolation
- Some commands can be excluded
- Network access is configurable
- Nested sandboxing for containers
