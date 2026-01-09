---
id: marketplaces-sources
topic: Marketplace Source Types
category: marketplaces
tags: [sources, github, npm, git, local, file, directory]
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

## File Source

Reference a specific marketplace JSON file.

```json
{
  "name": "local-marketplace",
  "source": {
    "source": "file",
    "path": "/absolute/path/to/marketplace.json"
  }
}
```

**Use cases:**
- Testing marketplace definitions before publishing
- Local-only marketplaces not suitable for version control
- Temporary marketplace configurations

## Directory Source

Reference a directory containing a plugin.

```json
{
  "name": "dev-plugin",
  "source": {
    "source": "directory",
    "path": "/path/to/plugin-directory"
  }
}
```

**Use cases:**
- Local plugin development workflows
- Directory-based plugin distribution
- Development environments with multiple local plugins

## Key Points

- Relative paths simplest for bundled plugins
- GitHub for community distribution
- URL for GitLab/Bitbucket/self-hosted
- NPM for JavaScript ecosystem
- File/Directory for local development
