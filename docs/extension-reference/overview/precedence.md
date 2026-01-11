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

## Scope Interactions

When settings exist at multiple scopes, they interact based on type:

| Setting Type | Behavior |
|--------------|----------|
| Scalar (string, number, boolean) | Higher scope wins |
| Array | Merged (higher scope items first) |
| Object | Deep merged (higher scope wins conflicts) |

### Scalar Example

```
Managed: { "theme": "dark" }
User:    { "theme": "light" }
Result:  { "theme": "dark" }  # Managed wins
```

### Array Merge Example

```
Managed: { "blockedTools": ["dangerous"] }
User:    { "blockedTools": ["risky"] }
Result:  { "blockedTools": ["dangerous", "risky"] }  # Merged
```

### Object Merge Example

```
User:    { "hooks": { "PreToolUse": [...] } }
Project: { "hooks": { "SessionStart": [...] } }
Result:  { "hooks": { "PreToolUse": [...], "SessionStart": [...] } }
```

## Common Scenarios

### Organization Lockdown

Managed settings enforce security; project customizes workflow:

```
Managed: { "disableWebSearch": true }
Project: { "defaultModel": "sonnet" }
User:    { "theme": "dark" }
Result:  All three apply (no conflicts)
```

### Setting Override Attempts

User cannot override managed settings:

```
Managed: { "maxTokens": 1000 }
User:    { "maxTokens": 5000 }
Result:  { "maxTokens": 1000 }  # Managed wins
```

### Local Development

Local settings override project for personal testing:

```
Project: { "apiEndpoint": "https://prod.api.com" }
Local:   { "apiEndpoint": "http://localhost:3000" }
Result:  { "apiEndpoint": "http://localhost:3000" }  # Local wins
```

## Key Points

- Managed settings enforce organizational policy
- Local settings for personal project overrides
- Project settings for team-shared configuration
- Test in local before promoting to project
