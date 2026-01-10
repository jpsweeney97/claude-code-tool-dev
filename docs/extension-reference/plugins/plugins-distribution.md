---
id: plugins-distribution
topic: Plugin Distribution and Versioning
category: plugins
tags: [distribution, versioning, semver, changelog, releases]
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

## Key Points

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Maintain CHANGELOG.md for release history
- Use pre-release versions for testing
