---
id: plugins-examples
topic: Plugin Examples
category: plugins
tags: [examples, templates, patterns]
requires: [plugins-overview, plugins-manifest, plugins-components]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Examples

Complete working plugin configurations.

## Minimal Plugin

```json
{
  "name": "my-simple-plugin"
}
```

With directory structure:
```
my-simple-plugin/
├── .claude-plugin/
│   └── plugin.json
└── commands/
    └── hello.md
```

## Full-Featured Plugin

```json
{
  "name": "enterprise-tools",
  "version": "2.1.0",
  "description": "Enterprise workflow automation",
  "author": {
    "name": "Enterprise Team",
    "email": "enterprise@example.com"
  },
  "license": "MIT",
  "keywords": ["enterprise", "workflow"],
  "commands": "./commands/",
  "agents": ["./agents/security-reviewer.md"],
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
      }]
    }]
  },
  "mcpServers": {
    "enterprise-db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

## Plugin with All Components

```
full-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── review.md
│   └── test.md
├── skills/
│   └── analysis/
│       └── SKILL.md
├── agents/
│   └── reviewer.md
├── hooks/
│   └── hooks.json
├── .mcp.json
├── .lsp.json
└── scripts/
    └── validate.sh
```

## Key Points

- Start minimal, add components as needed
- Use inline hooks for simple cases
- Reference files for complex configurations
- Bundle supporting scripts in plugin
