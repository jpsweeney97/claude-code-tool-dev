---
id: marketplaces-overview
topic: Marketplaces Overview
category: marketplaces
tags: [marketplaces, distribution, catalog, plugins]
related_to: [marketplaces-schema, marketplaces-sources, plugins-overview]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplaces Overview

Marketplaces are catalogs that distribute plugins. They enable discovery, version tracking, and team-wide deployment.

## Purpose

- Distribute plugins to teams
- Track plugin versions
- Enable discovery
- Centralize plugin management

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

## Key Points

- Marketplace = plugin catalog
- Distributed via Git repos
- marketplace.json defines available plugins
- Reserved names cannot be used
