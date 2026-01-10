---
id: settings-plugins-advanced
topic: Plugin Settings (Advanced)
category: settings
tags: [plugins, marketplaces, enabledPlugins, strictKnownMarketplaces]
requires: [settings-overview, settings-scopes]
related_to: [plugins-overview, marketplaces-overview]
official_docs: https://code.claude.com/en/settings#plugin-configuration
---

# Plugin Settings (Advanced)

Advanced configuration for plugins and marketplace restrictions.

## enabledPlugins

Controls which plugins are enabled. Format: `"plugin-name@marketplace-name": true/false`

```json
{
  "enabledPlugins": {
    "formatter@acme-tools": true,
    "deployer@acme-tools": true,
    "analyzer@security-plugins": false
  }
}
```

**Scopes:**
- User settings: Personal plugin preferences
- Project settings: Team-shared plugins
- Local settings: Per-machine overrides (not committed)

## extraKnownMarketplaces

Defines additional marketplaces for the repository. Used in project settings to ensure team access.

```json
{
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-plugins"
      }
    },
    "security-plugins": {
      "source": {
        "source": "git",
        "url": "https://git.example.com/security/plugins.git"
      }
    }
  }
}
```

**Behavior when present:**
1. Team members prompted to install marketplace when trusting folder
2. Prompted to install plugins from marketplace
3. Users can skip unwanted marketplaces/plugins
4. Installation requires explicit consent

## strictKnownMarketplaces (Managed Only)

Allowlist of marketplaces users can add. Only available in `managed-settings.json`.

**Managed settings locations:**
- macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
- Linux/WSL: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json`

**Allowlist behavior:**
- `undefined`: No restrictions (default)
- `[]`: Complete lockdown—no marketplaces can be added
- List of sources: Only matching marketplaces allowed

### Supported Source Types

**1. GitHub repositories:**

```json
{ "source": "github", "repo": "acme-corp/plugins" }
{ "source": "github", "repo": "acme-corp/plugins", "ref": "v2.0" }
{ "source": "github", "repo": "acme-corp/plugins", "ref": "main", "path": "marketplace" }
```

**2. Git repositories:**

```json
{ "source": "git", "url": "https://gitlab.example.com/plugins.git" }
{ "source": "git", "url": "ssh://git@git.example.com/plugins.git", "ref": "v3.1" }
```

**3. URL-based:**

```json
{ "source": "url", "url": "https://plugins.example.com/marketplace.json" }
{ "source": "url", "url": "https://cdn.example.com/marketplace.json", "headers": { "Authorization": "Bearer ${TOKEN}" } }
```

**4. NPM packages:**

```json
{ "source": "npm", "package": "@acme-corp/claude-plugins" }
```

**5. File paths:**

```json
{ "source": "file", "path": "/usr/local/share/claude/marketplace.json" }
```

**6. Directory paths:**

```json
{ "source": "directory", "path": "/opt/acme-corp/approved-marketplaces" }
```

### Exact Matching

Sources must match **exactly**, including optional fields:

```json
// These are DIFFERENT sources:
{ "source": "github", "repo": "acme/plugins" }
{ "source": "github", "repo": "acme/plugins", "ref": "main" }

// These are also DIFFERENT:
{ "source": "github", "repo": "acme/plugins", "path": "marketplace" }
{ "source": "github", "repo": "acme/plugins" }
```

### Example: Allow Specific Marketplaces

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/approved-plugins" },
    { "source": "github", "repo": "acme-corp/security-tools", "ref": "v2.0" },
    { "source": "npm", "package": "@acme-corp/compliance-plugins" }
  ]
}
```

### Example: Disable All Marketplace Additions

```json
{
  "strictKnownMarketplaces": []
}
```

## Comparison: extra vs strict

| Aspect | `extraKnownMarketplaces` | `strictKnownMarketplaces` |
|--------|--------------------------|---------------------------|
| Purpose | Team convenience | Policy enforcement |
| Settings file | Any | Managed only |
| Behavior | Auto-install missing | Block non-allowlisted |
| When enforced | After trust prompt | Before network ops |
| Can override | Yes | No (highest precedence) |
| Format | Named with nested source | Direct source object |
| Use case | Onboarding | Compliance, security |

## Managing Plugins

Use the `/plugin` command for interactive management:

- Browse available plugins from marketplaces
- Install/uninstall plugins
- Enable/disable plugins
- View plugin details (commands, agents, hooks)
- Add/remove marketplaces

## Key Points

- `enabledPlugins` controls which installed plugins are active
- `extraKnownMarketplaces` helps teams share marketplace sources
- `strictKnownMarketplaces` is managed-only for organizational control
- Restrictions checked before any network/filesystem operations
- Previously installed marketplaces remain accessible when restricted
