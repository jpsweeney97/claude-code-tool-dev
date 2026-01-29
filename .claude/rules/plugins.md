---
paths:
  - "packages/plugins/**"
  - ".claude/plugins/**"
  - "~/.claude/plugins/**"
---

# Plugin Development

Plugins bundle multiple Claude Code extensions (skills, commands, agents, hooks, MCP servers) into distributable packages with versioning and marketplace support.

## When to Use Plugins

- **Bundling related extensions**: Group skills, commands, agents that work together
- **Team distribution**: Share curated tooling via git-based marketplaces
- **Versioned releases**: Semantic versioning with changelog tracking
- **Cross-project reuse**: Install once, use across multiple projects

## When NOT to Use Plugins

- **Single skill/command**: Just create in `.claude/skills/` or `.claude/commands/`
- **Project-specific tooling**: Use local `.claude/` directory
- **Rapid iteration**: Plugin installation adds overhead; develop locally first
- **Simple hooks**: Use `settings.json` hooks directly

## Structure

```
plugin-name/
├── .claude-plugin/           # Metadata directory (REQUIRED)
│   └── plugin.json          # Plugin manifest (REQUIRED)
├── commands/                 # Simple slash commands (*.md) — legacy; prefer skills/
│   └── *.md
├── agents/                   # Default agent location
│   └── *.md
├── skills/                   # Default skills location
│   └── skill-name/
│       └── SKILL.md
├── hooks/
│   └── hooks.json           # Hook configurations
├── .mcp.json                # MCP server definitions
├── .lsp.json                # LSP server configurations
├── scripts/                 # Hook and utility scripts
├── README.md                # Required for publishing
├── CHANGELOG.md             # Required for publishing
└── LICENSE
```

## plugin.json Manifest

### Required Fields

```json
{
  "name": "plugin-name"
}
```

Only `name` is required. Use kebab-case, no spaces.

### Complete Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": "./custom/commands/",
  "agents": "./custom/agents/",
  "skills": "./custom/skills/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

### Field Reference

| Field          | Type           | Required | Notes                              |
| -------------- | -------------- | -------- | ---------------------------------- |
| `name`         | string         | Yes      | Unique kebab-case identifier       |
| `version`      | string         | No       | Semantic version (e.g., `"1.0.0"`) |
| `description`  | string         | No       | Brief explanation                  |
| `strict`       | boolean        | No       | Marketplace only: when `false`, no `plugin.json` needed in source |
| `author`       | object         | No       | `{name, email?, url?}`             |
| `homepage`     | string         | No       | Documentation URL                  |
| `repository`   | string         | No       | Source code URL                    |
| `license`      | string         | No       | License identifier                 |
| `keywords`     | array          | No       | Discovery tags                     |
| `commands`     | string\|array  | No       | Supplements default `commands/`    |
| `agents`       | string\|array  | No       | Supplements default `agents/`      |
| `skills`       | string\|array  | No       | Supplements default `skills/`      |
| `hooks`        | string\|object | No       | Path or inline config              |
| `mcpServers`   | string\|object | No       | Path or inline config              |
| `lspServers`   | string\|object | No       | Path or inline config              |
| `outputStyles` | string\|array  | No       | Output style files                 |

### Path Behavior

**Critical**: Custom paths **supplement** default directories, they don't replace them.

- If `commands/` exists AND `"commands": "./custom/"` is set, both are loaded
- All paths must be relative and start with `./`
- Forward slashes only (no backslashes)

## Components

### Skills

Skills are directories containing `SKILL.md` with required frontmatter:

```
skills/
├── code-reviewer/
│   ├── SKILL.md
│   ├── references/     # Optional
│   └── scripts/        # Optional
└── pdf-processor/
    └── SKILL.md
```

**Required SKILL.md frontmatter:**

```yaml
---
name: skill-name
description: When this skill should be invoked
---

Skill instructions...
```

See `skills.md` rules for complete SKILL.md requirements.

### Commands (Legacy)

> **Note:** The `commands/` directory is legacy. Prefer `skills/` for new development.

Commands are simple markdown files with optional frontmatter:

```markdown
---
description: What this command does
---

Command content with $ARGUMENTS placeholder.
```

Plugin commands are namespaced: `/plugin-name:command-name`

Plugin prefix is optional unless there are name collisions between plugins.

### Agents

Agents are markdown files with frontmatter:

```markdown
---
name: agent-name
description: When this agent should be invoked
tools: Glob, Grep, Read
---

Agent system prompt...
```

### Hooks

Configure in `hooks/hooks.json` or inline in `plugin.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
          }
        ]
      }
    ]
  }
}
```

**Hook types**:

- `command`: Execute shell commands or scripts
- `prompt`: Evaluate a prompt with an LLM (uses `$ARGUMENTS` placeholder)
- `agent`: Run an agentic verifier with tools (plugins only)

**Available events**: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, UserPromptSubmit, Notification, Stop, SubagentStart, SubagentStop, Setup, SessionStart, SessionEnd, PreCompact

- `Setup`: Fires when `--init`, `--init-only`, or `--maintenance` flags are used

**Execution**: All matching hooks from all sources (user, project, plugins) run in parallel with no guaranteed order. Design hooks for independent execution.

### MCP Servers

Configure in `.mcp.json` or inline in `plugin.json`:

```json
{
  "mcpServers": {
    "plugin-database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    }
  }
}
```

Plugin MCP servers start automatically when plugin is enabled. MCP server changes require Claude Code restart.

### LSP Servers

Configure in `.lsp.json`:

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  }
}
```

**Note**: LSP binary must be installed separately (not bundled).

## Path Conventions

### ${CLAUDE_PLUGIN_ROOT}

Use this variable for all paths in hooks, MCP, LSP configs:

```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
}
```

This resolves to the plugin's installed location regardless of where it's installed.

### No Path Traversal

**Critical limitation**: Plugins cannot reference files outside their directory via `../` paths.

```json
// WRONG - will not work after installation
"../shared-utils/helper.sh"

// CORRECT - self-contained
"${CLAUDE_PLUGIN_ROOT}/utils/helper.sh"
```

Files reached via `../` paths are not copied during installation. **Exception**: Symlinks within the plugin directory are resolved and their content is copied into the cache.

## Installation

### Scopes

| Scope     | Location                      | Use Case                                      |
| --------- | ----------------------------- | --------------------------------------------- |
| `user`    | `~/.claude/settings.json`     | Personal plugins across projects              |
| `project` | `.claude/settings.json`       | Team plugins via git                          |
| `local`   | `.claude/settings.local.json` | Project-specific, gitignored                  |
| `managed` | `managed-settings.json`       | Organization-managed (read-only, update only) |

### CLI Commands

```bash
# Install from marketplace
claude plugin install formatter@my-marketplace
claude plugin install formatter@my-marketplace --scope project

# Install specific version
claude plugin install plugin-name@marketplace#v1.0.0

# Management
claude plugin list
claude plugin enable <plugin>
claude plugin disable <plugin>
claude plugin update <plugin>
claude plugin uninstall <plugin>

# Validation
claude plugin validate <path>
```

### Installation Internals

Installation is two-step:

1. **Cache creation**: Files copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
2. **Registration**: Entry added to `~/.claude/plugins/installed_plugins.json`

**Both must succeed**. If plugin appears installed but doesn't work, reinstall.

**Caching behavior:**
- Plugins are copied (not symlinked) to the cache directory
- Paths referencing files outside the plugin directory (`../`) won't work after installation
- **Exception**: Symlinks within the plugin directory are followed and their content is copied

### Post-Install

**Restart Claude Code** after installing plugins. Skills load at session start.

## Marketplaces

### marketplace.json Format

```json
{
  "name": "marketplace-name",
  "description": "Marketplace description",
  "owner": {
    "name": "Owner Name"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "source": "./packages/plugins/plugin-name",
      "version": "1.0.0"
    }
  ]
}
```

**Plugin entry fields:**

| Field         | Description                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| `name`        | Plugin identifier (required)                                                 |
| `source`      | Path to plugin directory (required)                                          |
| `description` | Brief description                                                            |
| `version`     | Semver version                                                               |
| `strict`      | When `false`, marketplace entry defines everything (no `plugin.json` needed) |

Use `strict: false` when the marketplace entry should fully define the plugin without requiring a separate `plugin.json` manifest. When `true` (default), the plugin source must contain a `plugin.json`, and marketplace entry fields are merged with it.

### Local Development Marketplace

This repo uses `.claude-plugin/marketplace.json` as the `tool-dev` marketplace:

```bash
# Refresh after plugin changes
claude plugin marketplace update tool-dev

# Install/reinstall
claude plugin install <plugin>@tool-dev
```

### Remote Marketplaces

For distribution:

```bash
# Add marketplace (one-time)
claude plugin marketplace add https://github.com/owner/marketplace-repo.git

# Install from it
claude plugin install plugin-name@marketplace-name

# Update marketplace index
claude plugin marketplace update marketplace-name
```

**Private repository authentication:**

For background auto-updates, set the appropriate token:

| Provider  | Environment variables        |
|-----------|------------------------------|
| GitHub    | `GITHUB_TOKEN` or `GH_TOKEN` |
| GitLab    | `GITLAB_TOKEN` or `GL_TOKEN` |
| Bitbucket | `BITBUCKET_TOKEN`            |

### Publishing Workflow

1. Validate: `claude plugin validate <path>`
2. Update version in `plugin.json`
3. Update `CHANGELOG.md`
4. Commit changes
5. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
6. Push: `git push origin main --tags`
7. Update marketplace.json with new version
8. Users run: `claude plugin marketplace update <name>`

## Testing

### Validation

```bash
# CLI
claude plugin validate ./packages/plugins/my-plugin

# Interactive (from within Claude Code)
/plugin validate ./packages/plugins/my-plugin
```

### Manual Testing

```bash
# Test without installing
claude --plugin-dir ./packages/plugins/my-plugin

# Or install from local marketplace
claude plugin install my-plugin@tool-dev
```

### Debug Output

```bash
claude --debug
```

Shows plugin loading, manifest errors, component registration.

## Anti-patterns

| Anti-pattern                    | Problem                 | Fix                                         |
| ------------------------------- | ----------------------- | ------------------------------------------- |
| Components in `.claude-plugin/` | Won't be discovered     | Put at plugin root (`commands/`, `skills/`) |
| Absolute paths                  | Break on other machines | Use `${CLAUDE_PLUGIN_ROOT}`                 |
| Path traversal (`../`)          | Files not copied        | Keep everything self-contained              |
| Hardcoded secrets               | Security risk           | Use environment variables                   |
| Missing README/CHANGELOG        | Can't publish           | Add documentation                           |
| Non-executable scripts          | Hooks fail              | `chmod +x` scripts                          |
| Wrong event name case           | Hook doesn't fire       | Use exact case: `PostToolUse`               |
| Backslashes in paths            | Fails on Unix           | Use forward slashes only                    |

## Compliance Checklist

Before publishing a plugin, verify:

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

## Workflow (This Project)

```bash
# 1. Edit plugin in packages/plugins/<name>/
# 2. Update version in .claude-plugin/plugin.json
# 3. Refresh marketplace
claude plugin marketplace update tool-dev

# 4. Reinstall
claude plugin install <name>@tool-dev

# 5. Restart Claude Code (required for skills, MCP server changes)
```

**Restart required after:** Installing/updating plugins, MCP server config changes, skill changes.

## See Also

- **skills.md** — Skill development (plugins bundle skills)
- **commands.md** — Command development (plugins bundle commands)
- **agents.md** — Agent development (plugins bundle agents)
- **hooks.md** — Hook development (plugins bundle hooks)
- **mcp-servers.md** — MCP server development (plugins bundle MCP servers)
- **settings.md** — Configure plugin enable/disable in `enabledPlugins`

## References

Official documentation:

- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)

Project-specific:

- @.claude/skills/auditing-tool-designs/references/fallback-specs.md — Plugin manifest fields
