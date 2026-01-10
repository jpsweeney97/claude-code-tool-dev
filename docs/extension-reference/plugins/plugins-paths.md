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
- **Custom paths supplement defaults** - they don't replace them

## Supplement Behavior

Custom paths add to default directories, not replace them:

- If `commands/` exists, it's loaded **in addition to** custom command paths
- All paths must be relative to plugin root and start with `./`
- Commands from custom paths use the same naming and namespacing rules
- Multiple paths can be specified as arrays

```json
{
  "commands": ["./specialized/deploy.md", "./utilities/batch-process.md"],
  "agents": ["./custom-agents/reviewer.md", "./custom-agents/tester.md"]
}
```

In this example, if `commands/` also exists at the plugin root, those commands are loaded too.

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

**Why this fails**: During installation, only files within the plugin root are copied to the cache. External files reached via `../` paths aren't included, so those paths break post-installation.

**Solution**: Use symlinks instead — symlinked content is copied into the cache during installation. See `plugins-caching` for details.

## Key Points

- Always use `./` prefix for paths
- `${CLAUDE_PLUGIN_ROOT}` for runtime resolution
- No `../` traversal (external files not copied)
- Custom paths supplement defaults, not replace them
- Symlink external resources if needed
