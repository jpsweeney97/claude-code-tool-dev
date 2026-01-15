---
name: deploying-plugins
description: "Package, document, and distribute plugins for marketplace or manual sharing. Use after optimization passes, when ready to publish, share, or release a plugin. Triggers: deploy plugin, publish plugin, package for distribution, prepare release, share this plugin."
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  domains: [plugin-development, distribution, packaging]
  type: process
---

# Plugin Deployer v1.0

Package, document, and distribute plugins for sharing.

**Announce at start:** "I'm using the deploying-plugins skill to prepare this plugin for distribution."

## Overview

The deployer guides plugins from "working" to "published" through 5 phases: pre-flight validation, documentation, versioning, packaging, and distribution.

| Aspect | Optimizer | Deployer |
|--------|-----------|----------|
| Purpose | Improve quality | Package and share |
| Input | Working plugin | Optimized plugin |
| Output | Design document | Published plugin |
| Goal | "Good → great" | "Great → shared" |

## Triggers

- `deploy plugin` - Ready to publish
- `publish plugin` - Share on marketplace
- `package for distribution` - Prepare for sharing
- `prepare release` - Version and document
- `share this plugin` - Distribute manually or via marketplace

## Prerequisites

| Prerequisite | Source | Required? |
|--------------|--------|-----------|
| Working plugin | implementing-{component} | Yes |
| All tests passing | Component-level testing | Yes |
| Optimization complete | optimizing-plugins | Recommended |

## Pipeline Context

This skill is **Stage 5: Deploy** - the final stage.

| Aspect | Value |
|--------|-------|
| This stage | Package and distribute |
| Prerequisite | `/optimizing-plugins` or `/implementing-{component}` |
| Hands off to | Done (published plugin) |

---

## The Process

### Phase 1: Pre-flight Checks

Run validation to ensure plugin is deployment-ready:

```bash
./scripts/preflight.sh <plugin-path>
```

| Check | Tool | Pass Criteria |
|-------|------|---------------|
| Structure valid | `claude plugin validate` | No errors |
| No hardcoded secrets | Pattern grep | None found |
| Tests pass | Component tests | All green |
| Paths portable | Path scan | Uses `${CLAUDE_PLUGIN_ROOT}` |

**If any check fails:** Stop and fix before proceeding. Use `/implementing-{component}` skills if code changes needed.

**Present results:**
```
Pre-flight Results:
✓ Structure valid (claude plugin validate passed)
✓ No secrets detected
✓ Portable paths verified
⚠ No tests found (optional but recommended)

Ready to proceed? [Y/n]
```

### Phase 2: Documentation

Ensure README.md and CHANGELOG.md exist and are complete.

**README.md** (required):

Use template: `references/readme-template.md`

| Section | Auto-fill | User provides |
|---------|-----------|---------------|
| Title + version | From plugin.json | — |
| Installation | Generated | — |
| Features list | Scanned from dirs | — |
| Description | — | What it does, who it's for |
| Quick Start | — | Usage example |
| Configuration | — | Required setup (if any) |

**CHANGELOG.md** (required):

Use template: `references/changelog-template.md`
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

**Present:**
```
Documentation Review:

README.md:
  ✓ Title and version present
  ✓ Installation instructions
  ⚠ Missing: Quick Start example (required)
  ⚠ Missing: Description paragraph (required)

CHANGELOG.md:
  ✓ Exists with proper format
  ⚠ No entry for current version

Please provide:
1. A 2-3 sentence description of what this plugin does
2. A Quick Start usage example
3. What changed in this version?
```

### Phase 3: Versioning

Apply semantic versioning based on changes.

| Change Type | Bump | Example |
|-------------|------|---------|
| Breaking changes | MAJOR | 1.0.0 → 2.0.0 |
| New features | MINOR | 1.0.0 → 1.1.0 |
| Bug fixes | PATCH | 1.0.0 → 1.0.1 |

**Steps:**
1. Ask: "What type of changes are in this release?"
2. Suggest version bump based on response
3. Update version in plugin.json
4. Add changelog entry for new version
5. Commit: `chore: bump version to X.Y.Z`

**Present:**
```
Current version: 1.2.3

Changes described:
- Added new command for X (feature)
- Fixed bug in Y (bugfix)

Suggested bump: MINOR → 1.3.0

Proceed with version 1.3.0? [Y/n/custom]
```

### Phase 4: Packaging Validation

Test that the plugin installs and loads correctly:

```bash
./scripts/validate-package.sh <plugin-path>
```

| Check | Method | Purpose |
|-------|--------|---------|
| Clean install | `claude --plugin-dir` | Verify loading works |
| Components load | Check output | Commands/agents visible |
| No errors | Exit code | Clean load |

**Present:**
```
Package Validation:
✓ Plugin loads successfully
✓ 3 commands registered
✓ 2 skills loaded
✓ 1 agent available

Ready for distribution.
```

### Phase 5: Distribution

Ask: "Where will you distribute this plugin?"

| Target | Workflow |
|--------|----------|
| **Marketplace** | Git tag → Push → Add to marketplace → Share install command |
| **Manual** | Push to git → Share clone URL |

#### Marketplace Path

See: `references/marketplace-checklist.md`

1. Ensure git repo is clean (all changes committed)
2. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push: `git push origin main --tags`
4. Add to marketplace registry (if not already)
5. Provide install command:
   ```
   /plugin marketplace add <git-url>
   /plugin install <name>@<marketplace>
   ```

#### Manual Path

1. Ensure repo is accessible (public or shared)
2. Push to git host
3. Provide usage instructions:
   ```
   git clone <repo-url>
   claude --plugin-dir ./plugin-name
   ```

---

## Error Handling

| Phase | Failure | Resolution |
|-------|---------|------------|
| Pre-flight | Structure errors | Fix per error messages, rerun |
| Pre-flight | Secrets detected | Remove credentials, use env vars |
| Documentation | README incomplete | Fill required sections |
| Versioning | Conflict | Choose appropriate bump |
| Packaging | Load failure | Check structure, use `claude --debug` |
| Distribution | Push failure | Resolve git issues |

---

## Verification Checklist

**Pre-flight:**
- [ ] `claude plugin validate` passes
- [ ] No hardcoded secrets
- [ ] Paths use `${CLAUDE_PLUGIN_ROOT}`

**Documentation:**
- [ ] README.md complete with install/usage
- [ ] CHANGELOG.md updated for version

**Versioning:**
- [ ] Version bumped (semver)
- [ ] Changelog entry added
- [ ] Version commit created

**Distribution:**
- [ ] Git tag created (marketplace)
- [ ] Pushed to git host
- [ ] Install command tested

---

## Handoff

"Plugin deployed. What's next?"

| Status | Next Step |
|--------|-----------|
| Published successfully | Done — monitor feedback |
| Issues found | Fix and re-run deploying-plugins |
| Add more features | Back to `/brainstorming-{component}` |

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Deploy without validation | Preventable errors | Run pre-flight first |
| Skip README | Users can't use it | Template + fill gaps |
| Hardcoded paths | Breaks on install | Use `${CLAUDE_PLUGIN_ROOT}` |
| No version bump | Can't track releases | Semver every release |
| Skip changelog | Users don't know changes | Update each version |

---

## Key Principles

- **Validate before deploy** — Pre-flight catches issues early
- **Document for users** — README + CHANGELOG required
- **Semantic versioning** — Users depend on version meaning
- **Test installation** — Verify actual install works
- **Branch late** — Paths diverge only at distribution

---

## References

**Pipeline skills:**
- `optimizing-plugins` — Previous stage
- `implementing-{component}` — If fixes needed

**Templates:**
- `references/readme-template.md` — README scaffold
- `references/changelog-template.md` — Changelog format
- `references/marketplace-checklist.md` — Marketplace requirements

**Examples:**
- `examples/sample-marketplace.json` — Marketplace entry

**Official docs:**
- `docs/claude-code-documentation/plugins-overview.md`
- `docs/claude-code-documentation/plugin-marketplace-overview.md`
