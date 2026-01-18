---
id: plugins-distribution
topic: Plugin Distribution and Versioning
category: plugins
tags: [distribution, versioning, semver, changelog, releases, publishing, checklist]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-cli]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Distribution and Versioning

Version management and distribution best practices for plugins.

## Version Format

Use semantic versioning (`MAJOR.MINOR.PATCH`):

```json
{
  "name": "my-plugin",
  "version": "2.1.0"
}
```

## Semver Components

| Component | When to Increment | Example |
|-----------|-------------------|---------|
| **MAJOR** | Breaking changes (incompatible API changes) | `1.0.0` -> `2.0.0` |
| **MINOR** | New features (backward-compatible additions) | `2.0.0` -> `2.1.0` |
| **PATCH** | Bug fixes (backward-compatible fixes) | `2.1.0` -> `2.1.1` |

## Best Practices

1. **Start at `1.0.0`** for your first stable release
2. **Update version** in `plugin.json` before distributing changes
3. **Document changes** in a `CHANGELOG.md` file
4. **Use pre-release versions** like `2.0.0-beta.1` for testing

## Changelog Format

```markdown
# Changelog

## [2.1.0] - 2024-01-15

### Added
- New `/deploy` command

### Fixed
- Hook timing issue on Windows

## [2.0.0] - 2024-01-01

### Changed
- BREAKING: Renamed `/status` to `/check-status`
```

## Pre-release Versions

For testing before stable release:

```json
{
  "version": "2.0.0-beta.1"
}
```

Pre-release version patterns:
- `2.0.0-alpha.1` - Early testing
- `2.0.0-beta.1` - Feature complete, testing stability
- `2.0.0-rc.1` - Release candidate

## Publishing Workflow

1. Validate: `claude plugin validate <path>`
2. Update version in `plugin.json`
3. Update `CHANGELOG.md`
4. Commit changes
5. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
6. Push: `git push origin main --tags`
7. Update `marketplace.json` with new version
8. Users run: `claude plugin marketplace update <name>`

## Compliance Checklist

Before publishing, verify:

- [ ] `plugin.json` has `name` field (kebab-case)
- [ ] `plugin.json` has `version` field (semver)
- [ ] `README.md` exists with installation instructions
- [ ] `CHANGELOG.md` exists with version history
- [ ] All paths are relative and start with `./`
- [ ] Hook/MCP/LSP configs use `${CLAUDE_PLUGIN_ROOT}`
- [ ] No hardcoded secrets or absolute paths
- [ ] Scripts are executable (`chmod +x`)
- [ ] `claude plugin validate` passes
- [ ] Tested via local marketplace installation
- [ ] Git tag matches version in plugin.json

## Key Points

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Maintain CHANGELOG.md for release history
- Use pre-release versions for testing
- Run `claude plugin validate` before publishing
- Git tags must match version in plugin.json
- README.md and CHANGELOG.md required for publishing
