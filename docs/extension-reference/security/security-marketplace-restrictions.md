---
id: security-marketplace-restrictions
topic: Marketplace Restrictions
category: security
tags: [marketplaces, restrictions, strictKnownMarketplaces]
requires: [security-managed]
related_to: [marketplaces-overview]
official_docs: https://code.claude.com/en/iam
---

# Marketplace Restrictions

Control which marketplaces users can access.

## strictKnownMarketplaces

In `managed-settings.json`:

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/plugins" },
    { "source": "github", "repo": "acme-corp/security", "ref": "v2.0" },
    { "source": "url", "url": "https://plugins.example.com/marketplace.json" },
    { "source": "npm", "package": "@acme/plugins" }
  ]
}
```

## Behavior Reference

| Value | Behavior |
|-------|----------|
| `undefined` | No restrictions |
| `[]` | Users cannot add marketplaces |
| `[sources...]` | Only exact matches allowed |

## Source Types

- **github**: `{ "source": "github", "repo": "owner/repo" }`
- **url**: `{ "source": "url", "url": "https://..." }`
- **npm**: `{ "source": "npm", "package": "@scope/pkg" }`

## Version Pinning

Pin to specific version:

```json
{
  "source": "github",
  "repo": "acme-corp/plugins",
  "ref": "v2.0.0"
}
```

## Key Points

- undefined = no restrictions
- [] = all additions blocked
- Array = only listed marketplaces
- Supports github, url, npm sources
- Can pin to specific versions
