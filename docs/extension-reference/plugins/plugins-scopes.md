---
id: plugins-scopes
topic: Plugin Installation Scopes
category: plugins
tags: [installation, scopes, settings, user, project, local, managed]
requires: [plugins-overview]
related_to: [plugins-cli, plugins-caching]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Installation Scopes

Where plugins are installed and who can use them.

## Scope Reference

| Scope | Settings File | Use Case |
|-------|--------------|----------|
| `user` | `~/.claude/settings.json` | Personal plugins across all projects (default) |
| `project` | `.claude/settings.json` | Team plugins shared via version control |
| `local` | `.claude/settings.local.json` | Project-specific plugins, gitignored |
| `managed` | `managed-settings.json` | Managed plugins (read-only, update only) |

## Default Scope

When no scope is specified, plugins install to `user` scope:

```bash
claude plugin install my-plugin@marketplace
# Installs to ~/.claude/settings.json
```

## Scope Selection

Specify scope with the `--scope` flag:

```bash
# User scope - personal, all projects
claude plugin install my-plugin@marketplace --scope user

# Project scope - shared with team via git
claude plugin install my-plugin@marketplace --scope project

# Local scope - project-specific, gitignored
claude plugin install my-plugin@marketplace --scope local
```

## When to Use Each Scope

**User scope (`user`)**: Personal productivity plugins, developer tools, utilities you want everywhere.

**Project scope (`project`)**: Team standards, project-specific workflows. Committed to version control so all team members get the same plugins.

**Local scope (`local`)**: Personal project configurations you don't want to share. The `.claude/settings.local.json` file is typically gitignored.

**Managed scope (`managed`)**: Organization-managed plugins. Read-only for users, can only be updated (not installed/uninstalled directly).

## Key Points

- Default installation scope is `user`
- Project scope enables team plugin sharing
- Local scope keeps plugins private per-project
- Scopes affect where settings are stored, not functionality
