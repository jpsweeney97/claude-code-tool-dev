---
date: 2026-01-05T01:19:12.891530
version: 1
git_commit: 9c8d4be
branch: main
repository: claude-code-tool-dev
tags: ["plugins", "marketplace", "architecture", "migration"]
---

# Handoff: Plugin architecture migration to tool-dev marketplace

## Goal
Reorganize plugin management to use monorepo as single source of truth via tool-dev marketplace, eliminating duplicate jp-local and superserum sources

## Key Decisions
- Created tool-dev marketplace: Monorepo .claude-plugin/marketplace.json indexes packages/plugins/* - plugins deployed via marketplace install, not promote script
- Removed jp-local and superserum: Eliminated duplicate plugins, consolidated to single tool-dev source
- Fixed brainstorm name collision: Renamed plugin-dev:brainstorm.md to brainstorm-plugins.md to avoid fuzzy-match conflict with superpowers:brainstorming skill
- Plugin manifest requirements: author must be object not string, paths must start with ./, use mcpServers not mcp

## Recent Changes
- .claude-plugin/marketplace.json - Created marketplace manifest indexing 7 plugins
- ~/.claude/settings.json - Migrated enabledPlugins from jp-local/superserum to tool-dev
- packages/plugins/persistent-tasks/.claude-plugin/plugin.json - Fixed manifest validation errors
- CLAUDE.md - Added Plugin Workflow section documenting tool-dev marketplace usage

## Learnings
- Plugins are cached when installed - editing settings.json to enable uncached plugins causes them to be auto-disabled
- disable-model-invocation on commands can block similarly-named skills via fuzzy matching
- Plugin install copies source to cache - monorepo changes require marketplace update + reinstall

## Next Steps
1. Restart Claude Code to load the 7 newly installed tool-dev plugins
2. Verify plugins work: test deep-analysis, plugin-dev, doc-auditor commands/skills
3. Audit remaining plugin manifests in packages/plugins/ for similar validation issues
4. Consider adding plugin validation to promote script or pre-commit hook

## Uncommitted Files
```
LAUDE.md
docs/plans/2026-01-04-promote-script-test-plan.md
packages/plugins/persistent-tasks/.claude-plugin/plugin.json
.claude-plugin/
.claude/handoffs/
```
