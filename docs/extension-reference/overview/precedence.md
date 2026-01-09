---
id: precedence
topic: Configuration Precedence
category: overview
tags: [scope, priority, settings, override]
requires: [extension-types]
related_to: [settings-scopes]
official_docs: https://code.claude.com/en/settings
---

# Configuration Precedence

How configurations override each other across scopes.

## Precedence Order (Highest to Lowest)

1. **Managed** — `managed-settings.json` (cannot be overridden)
2. **Command line** — Flags passed to `claude`
3. **Local** — `.claude/settings.local.json`
4. **Project** — `.claude/settings.json`
5. **User** — `~/.claude/settings.json`

## File Locations

| Scope | Path | Shared |
|-------|------|--------|
| Managed | `/Library/Application Support/ClaudeCode/` | By IT |
| User | `~/.claude/` | No |
| Project | `.claude/` | Yes (git) |
| Local | `.claude/*.local.*` | No |

## Override Rules

- Higher scope always wins
- **Deny always wins**: Any deny blocks regardless of allows elsewhere
- Same-scope conflicts: More specific wins
- User extensions override project with same name

## Key Points

- Managed settings enforce organizational policy
- Local settings for personal project overrides
- Project settings for team-shared configuration
- Test in local before promoting to project
