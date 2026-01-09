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

## External Files

Files outside plugin directory aren't copied to cache. If plugin references external files:
- They won't be available after installation
- Use symlinks if needed
- Prefer bundling all files within plugin

## Key Points

- Cache at ~/.claude/plugins/cache/
- Two-step: cache + registration
- Both must exist for plugin to work
- External files not copied
