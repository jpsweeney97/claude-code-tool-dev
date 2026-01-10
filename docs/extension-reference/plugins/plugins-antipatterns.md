---
id: plugins-antipatterns
topic: Plugin Anti-patterns
category: plugins
tags: [antipatterns, mistakes, best-practices, prevention]
requires: [plugins-overview]
related_to: [plugins-troubleshooting, plugins-paths, plugins-distribution]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Anti-patterns

Common mistakes to avoid when developing plugins.

## Anti-patterns Reference

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Components in `.claude-plugin/` | Won't be discovered | Put at plugin root (`commands/`, `skills/`) |
| Absolute paths | Break on other machines | Use `${CLAUDE_PLUGIN_ROOT}` |
| Path traversal (`../`) | Files not copied | Keep everything self-contained |
| Hardcoded secrets | Security risk | Use environment variables |
| Missing README/CHANGELOG | Can't publish | Add documentation |
| Non-executable scripts | Hooks fail | `chmod +x` scripts |
| Wrong event name case | Hook doesn't fire | Use exact case: `PostToolUse` |
| Backslashes in paths | Fails on Unix | Use forward slashes only |

## Key Points

- Place components at plugin root, not in `.claude-plugin/`
- Use `${CLAUDE_PLUGIN_ROOT}` for all internal paths
- Keep plugins self-contained (no external file references)
- Scripts must be executable
- Event names are case-sensitive
