---
id: marketplaces-schema
topic: Marketplace Schema
category: marketplaces
tags: [schema, marketplace-json, configuration]
requires: [marketplaces-overview]
related_to: [marketplaces-sources]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Schema

The marketplace file `.claude-plugin/marketplace.json` defines the plugin catalog.

## Full Schema

```json
{
  "name": "company-tools",
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@example.com"
  },
  "metadata": {
    "description": "Internal development tools",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting",
      "version": "2.1.0"
    }
  ]
}
```

## Plugin Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Plugin identifier (kebab-case) |
| `source` | string/object | Yes | Where to fetch plugin |
| `description` | string | No | Brief description |
| `version` | string | No | Semver version |
| `author` | object | No | `{name, email}` |
| `strict` | boolean | No | Require plugin.json (default: true) |
| `category` | string | No | For organization |
| `tags` | array | No | For searchability |

## Key Points

- Only `name` and `source` are required per plugin
- `strict: false` allows inline plugin definition
- Marketplace metadata is optional but recommended
