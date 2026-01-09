---
id: plugins-paths
topic: Plugin Path Resolution
category: plugins
tags: [paths, resolution, plugin-root, variables]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-caching]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Path Resolution

How paths are resolved in plugin configurations.

## Path Rules

- All paths use `./` prefix for plugin-relative resolution
- `${CLAUDE_PLUGIN_ROOT}` expands to plugin installation directory
- Path traversal (`../`) doesn't work (files aren't copied)

## ./  Prefix

Paths starting with `./` resolve relative to plugin root:

```json
{
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
```

## ${CLAUDE_PLUGIN_ROOT}

Use in scripts and configurations:

```json
{
  "mcpServers": {
    "api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

```bash
#!/bin/bash
# In hook script
source "${CLAUDE_PLUGIN_ROOT}/lib/utils.sh"
```

## Path Traversal Limitation

Parent directory traversal doesn't work:

```json
{
  "commands": "../shared/commands/"
}
```

Files outside plugin directory aren't copied during installation. Use symlinks if needed.

## Key Points

- Always use `./` prefix for paths
- `${CLAUDE_PLUGIN_ROOT}` for runtime resolution
- No `../` traversal (external files not copied)
- Symlink external resources if needed
