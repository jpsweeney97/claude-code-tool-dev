---
id: marketplaces-examples
topic: Marketplace Examples
category: marketplaces
tags: [examples, templates, patterns]
requires: [marketplaces-overview, marketplaces-schema, marketplaces-sources]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Examples

Complete working marketplace configurations.

## Simple Team Marketplace

```json
{
  "name": "team-tools",
  "plugins": [
    {
      "name": "review-helper",
      "source": "./plugins/review-helper"
    },
    {
      "name": "test-generator",
      "source": "./plugins/test-generator"
    }
  ]
}
```

## Full-Featured Marketplace

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
      "version": "2.1.0",
      "category": "formatting",
      "tags": ["code", "style"]
    },
    {
      "name": "deployment-tools",
      "source": {
        "source": "github",
        "repo": "company/deploy-plugin"
      },
      "description": "Deployment automation"
    }
  ]
}
```

## Inline Plugin Definition

Use `strict: false` to define plugins entirely in marketplace:

```json
{
  "plugins": [{
    "name": "quick-review",
    "source": "./plugins/review",
    "strict": false,
    "commands": ["./commands/"],
    "hooks": {
      "PostToolUse": [{
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/validate.sh"
        }]
      }]
    }
  }]
}
```

## Team Configuration

In `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "formatter@company-tools": true,
    "deployer@company-tools": true
  }
}
```

## Key Points

- Start simple with relative paths
- Add metadata for larger marketplaces
- Use `strict: false` for quick inline plugins
- Configure team marketplaces in settings.json
