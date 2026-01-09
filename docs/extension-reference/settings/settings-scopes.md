---
id: settings-scopes
topic: Settings Scopes
category: settings
tags: [scopes, managed, user, project, local]
requires: [settings-overview]
related_to: [settings-permissions, precedence]
official_docs: https://code.claude.com/en/settings
---

# Settings Scopes

Four scope levels with clear precedence rules.

## Scope Details

### Managed Scope

Location: `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS)

- Deployed by IT/admins
- Cannot be overridden by users
- Enforces organizational policy

### User Scope

Location: `~/.claude/settings.json`

- Personal defaults across all projects
- Lowest precedence
- Good for personal preferences

### Project Scope

Location: `.claude/settings.json`

- Committed to git, shared with team
- Defines team-wide conventions
- Overridden by local scope

### Local Scope

Location: `.claude/settings.local.json`

- NOT committed to git
- Personal project overrides
- Test settings before promoting to project

## Override Behavior

- Higher scope always wins
- **Deny always wins**: Any deny blocks regardless of allows elsewhere
- Settings merge, with higher scope taking precedence

## Key Points

- Managed for enterprise policy
- User for personal defaults
- Project for team conventions
- Local for testing
