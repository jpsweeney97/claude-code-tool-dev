---
id: plugins-caching
topic: Plugin Caching and Installation
category: plugins
tags: [caching, installation, registration, cache]
requires: [plugins-overview]
related_to: [plugins-paths, marketplaces-overview]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Caching and Installation

When installed, plugins are copied to a cache directory.

## Cache Location

```
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
```

Example:
```
~/.claude/plugins/cache/official/pyright-lsp/1.2.0/
```

## Two-Step Installation

Plugin installation is two-step:

1. **Cache creation**: Files copied to cache directory
2. **Registration**: Entry added to `installed_plugins.json`

Both steps must succeed for plugin to work.

## Verification Commands

```bash
# Check registration
cat ~/.claude/plugins/installed_plugins.json | jq '.["plugin@marketplace"]'

# Check cache
ls ~/.claude/plugins/cache/<marketplace>/<plugin>/

# Fix: reinstall
claude plugin install <plugin>@<marketplace>
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Plugin not loading | Missing registration | Reinstall plugin |
| Skills not found | Cache missing | Reinstall plugin |
| Old version running | Stale cache | Remove and reinstall |

## What Gets Copied

**For plugins with `.claude-plugin/plugin.json`**: The directory containing `.claude-plugin/plugin.json` (the implicit plugin root) is copied recursively.

**For marketplace plugins**: The path specified in the `source` field is copied recursively. For example, if your marketplace entry specifies `"source": "./plugins/my-plugin"`, the entire `./plugins/my-plugin` directory is copied.

## Symlink Behavior

Symlinks within the plugin directory are **honored during copying** — the symlinked content is copied into the cache (resolved, not preserved as symlinks):

```bash
# Inside your plugin directory
ln -s /path/to/shared-utils ./shared-utils
```

The content at `/path/to/shared-utils` will be copied into the plugin cache.

### Symlink Security

Symlinks pointing to locations outside the plugin's logical root are followed during copying. The symlinked content is resolved and copied into the cache (not preserved as symlinks). This provides flexibility while maintaining the security benefits of the caching system.

## External Files

Files outside the plugin directory (reached via `../` paths, not symlinks) aren't copied to cache. If plugin references external files via path traversal:
- They won't be available after installation
- Use symlinks instead (content will be copied)
- Prefer bundling all files within plugin

## Key Points

- Cache at ~/.claude/plugins/cache/
- Two-step: cache + registration
- Both must exist for plugin to work
- Symlinks are resolved and content is copied
- Path traversal (`../`) doesn't work — use symlinks instead
