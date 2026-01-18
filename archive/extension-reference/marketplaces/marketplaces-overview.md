---
id: marketplaces-overview
topic: Marketplaces Overview
category: marketplaces
tags: [marketplaces, distribution, catalog, plugins]
related_to: [marketplaces-schema, marketplaces-sources, marketplaces-walkthrough, marketplaces-troubleshooting, marketplaces-restrictions, marketplaces-examples, plugins-overview]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplaces Overview

Marketplaces are catalogs that distribute plugins. They enable discovery, version tracking, and team-wide deployment.

## Purpose

- Distribute plugins to teams
- Track plugin versions
- Enable discovery
- Centralize plugin management

> Looking to install plugins from an existing marketplace? See the user documentation for discovering and installing plugins.

## Marketplace Commands

```bash
# Add marketplace
/plugin marketplace add owner/repo
/plugin marketplace add https://gitlab.com/team/plugins.git
/plugin marketplace add ./local-marketplace

# Update marketplace
/plugin marketplace update <name>

# Install plugin
/plugin install my-plugin@marketplace-name

# Validate
/plugin validate .
```

## Marketplace File Location

`.claude-plugin/marketplace.json` at repository root.

## Reserved Names

Cannot use these marketplace names:
- `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`
- `anthropic-marketplace`, `anthropic-plugins`
- `agent-skills`, `life-sciences`
- Names impersonating official marketplaces

## Hosting Options

| Method | Command | Best For |
|--------|---------|----------|
| GitHub | `/plugin marketplace add owner/repo` | Public distribution, team sharing |
| GitLab/Bitbucket | `/plugin marketplace add https://gitlab.com/...` | Enterprise, self-hosted git |
| Remote URL | `/plugin marketplace add https://example.com/marketplace.json` | Static hosting, CDN distribution |
| Local path | `/plugin marketplace add ./my-marketplace` | Development, testing |

### GitHub (Recommended)

GitHub provides built-in version control, issue tracking, and team collaboration:

1. Create a repository for your marketplace
2. Add `.claude-plugin/marketplace.json` with plugin definitions
3. Share with teams: `/plugin marketplace add owner/repo`

### Other Git Services

Any git hosting service works (GitLab, Bitbucket, self-hosted):

```bash
/plugin marketplace add https://gitlab.com/company/plugins.git
```

### Local Testing

Test your marketplace locally before distribution:

```bash
/plugin marketplace add ./my-local-marketplace
/plugin install test-plugin@my-local-marketplace
```

### Remote URL

For static hosting or CDN distribution, host your `marketplace.json` at a URL:

```bash
/plugin marketplace add https://plugins.example.com/marketplace.json
```

This fetches the marketplace definition directly without git clone.

## Team Configuration

Configure your repository so team members are automatically prompted to install your marketplace. See [marketplaces-examples](marketplaces-examples.md) for `extraKnownMarketplaces` and `enabledPlugins` settings.

For organization-wide restrictions, see [marketplaces-restrictions](marketplaces-restrictions.md).

For details on plugin capabilities (commands, hooks, agents, MCP servers), see [plugins-overview](../plugins/plugins-overview.md).

## Key Points

- Marketplace = plugin catalog
- Distributed via Git repos
- marketplace.json defines available plugins
- Reserved names cannot be used
- GitHub recommended for distribution
- Test locally before sharing
