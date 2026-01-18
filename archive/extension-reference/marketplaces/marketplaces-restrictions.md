---
id: marketplaces-restrictions
topic: Managed Marketplace Restrictions
category: marketplaces
tags: [security, restrictions, managed-settings, strictKnownMarketplaces]
requires: [marketplaces-overview]
related_to: [marketplaces-sources, security-managed]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Managed Marketplace Restrictions

Organizations can restrict which plugin marketplaces users are allowed to add using the `strictKnownMarketplaces` setting in managed settings.

## Configuration Behavior

| Value | Behavior |
|-------|----------|
| Undefined (default) | No restrictions. Users can add any marketplace |
| Empty array `[]` | Complete lockdown. Users cannot add any new marketplaces |
| List of sources | Users can only add marketplaces that match the allowlist exactly |

## Common Configurations

### Disable All Marketplace Additions

```json
{
  "strictKnownMarketplaces": []
}
```

### Allow Specific Marketplaces Only

```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "acme-corp/approved-plugins"
    },
    {
      "source": "github",
      "repo": "acme-corp/security-tools",
      "ref": "v2.0"
    },
    {
      "source": "url",
      "url": "https://plugins.example.com/marketplace.json"
    }
  ]
}
```

## How Restrictions Work

Restrictions are validated early in the plugin installation process, before any network requests or filesystem operations occur. This prevents unauthorized marketplace access attempts.

### Exact Matching

The allowlist uses exact matching. For a marketplace to be allowed, all specified fields must match exactly.

**GitHub sources:**

| Field | Matching Rule |
|-------|---------------|
| `repo` | Required; must match exactly |
| `ref` | If specified in allowlist, must match exactly |
| `path` | If specified in allowlist, must match exactly |

**URL sources:**

| Field | Matching Rule |
|-------|---------------|
| `url` | Must match the full URL exactly |

### Allowlist Entry Examples

```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "company/plugins"
    },
    {
      "source": "github",
      "repo": "company/plugins",
      "ref": "v2.0"
    },
    {
      "source": "github",
      "repo": "company/monorepo",
      "path": "tools/claude-plugins"
    },
    {
      "source": "url",
      "url": "https://internal.example.com/marketplace.json"
    }
  ]
}
```

## Managed Settings Enforcement

Because `strictKnownMarketplaces` is set in managed settings, individual users and project configurations cannot override these restrictions.

**Settings precedence:**

1. Managed settings (highest priority, cannot be overridden)
2. User settings
3. Project settings

## Comparison with extraKnownMarketplaces

| Setting | Purpose | Location | Override Behavior |
|---------|---------|----------|-------------------|
| `strictKnownMarketplaces` | Restrict allowed sources | Managed settings only | Cannot be overridden |
| `extraKnownMarketplaces` | Add known marketplaces | Any settings level | Can be extended |

## Key Points

- `strictKnownMarketplaces` controls which marketplaces can be added
- Empty array `[]` blocks all new marketplace additions
- Matching is exact (all specified fields must match)
- Set in managed settings; users cannot override
- Different from `extraKnownMarketplaces` which adds known sources
