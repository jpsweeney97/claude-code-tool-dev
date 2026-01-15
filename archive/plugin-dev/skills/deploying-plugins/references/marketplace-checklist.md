# Marketplace Publishing Checklist

Use this checklist when publishing a plugin to a marketplace.

## Pre-Publish

- [ ] **Plugin validates** — `claude plugin validate <path>` passes
- [ ] **README complete** — Description, installation, usage, examples
- [ ] **CHANGELOG updated** — Entry for current version
- [ ] **Version bumped** — Semantic versioning in plugin.json
- [ ] **No secrets** — No hardcoded API keys, tokens, passwords
- [ ] **Portable paths** — Uses `${CLAUDE_PLUGIN_ROOT}` not absolute paths

## Git Preparation

- [ ] **Clean working tree** — All changes committed
- [ ] **On main/master branch** — Publishing from primary branch
- [ ] **Tests passing** — If tests exist, they pass

## Tagging

```bash
# Create annotated tag
git tag -a v{VERSION} -m "Release v{VERSION}"

# Push with tags
git push origin main --tags
```

## Marketplace Entry

For `marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "{PLUGIN_NAME}",
      "description": "{DESCRIPTION}",
      "author": "{AUTHOR}",
      "repository": "{GIT_URL}",
      "version": "{VERSION}"
    }
  ]
}
```

## Post-Publish

- [ ] **Test installation** — `/plugin install {name}@{marketplace}`
- [ ] **Verify components load** — Commands, skills, agents visible
- [ ] **Share install command** — Provide users with install instructions

## Installation Commands

```bash
# Add marketplace (one-time)
/plugin marketplace add {MARKETPLACE_GIT_URL}

# Install plugin
/plugin install {PLUGIN_NAME}@{MARKETPLACE_NAME}

# Pin to specific version
/plugin install {PLUGIN_NAME}@{MARKETPLACE_NAME}#v{VERSION}
```

## Updating Published Plugins

1. Make changes in development
2. Update CHANGELOG.md
3. Bump version in plugin.json
4. Commit: `chore: bump version to X.Y.Z`
5. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. Push: `git push origin main --tags`

Users can update with: `/plugin update {PLUGIN_NAME}`
