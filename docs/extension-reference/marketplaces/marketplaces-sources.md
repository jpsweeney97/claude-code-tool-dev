---
id: marketplaces-sources
topic: Marketplace Source Types
category: marketplaces
tags: [sources, github, npm, git, local]
requires: [marketplaces-overview, marketplaces-schema]
related_to: [marketplaces-examples]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Source Types

Plugins can be sourced from various locations.

## Source Type Reference

| Type | Format | Example |
|------|--------|---------|
| Relative | string | `"./plugins/my-plugin"` |
| GitHub | object | `{"source": "github", "repo": "owner/repo"}` |
| Git URL | object | `{"source": "url", "url": "https://gitlab.com/..."}` |
| NPM | object | `{"source": "npm", "package": "@scope/pkg"}` |
| File | object | `{"source": "file", "path": "/path/to/marketplace.json"}` |
| Directory | object | `{"source": "directory", "path": "/path/to/dir"}` |

## Relative Source

Simple path relative to marketplace root:

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin"
}
```

## GitHub Source

```json
{
  "name": "community-tool",
  "source": {
    "source": "github",
    "repo": "owner/repo"
  }
}
```

## Git URL Source

For non-GitHub repositories:

```json
{
  "name": "gitlab-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

## NPM Source

```json
{
  "name": "npm-plugin",
  "source": {
    "source": "npm",
    "package": "@scope/claude-plugin"
  }
}
```

## Key Points

- Relative paths simplest for bundled plugins
- GitHub for community distribution
- URL for GitLab/Bitbucket/self-hosted
- NPM for JavaScript ecosystem
