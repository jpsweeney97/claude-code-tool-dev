---
id: marketplaces-troubleshooting
topic: Marketplace Troubleshooting
category: marketplaces
tags: [troubleshooting, debugging, errors, validation]
requires: [marketplaces-overview]
related_to: [marketplaces-schema, marketplaces-sources, plugins-troubleshooting, plugins-caching]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Troubleshooting

Common issues when creating, validating, or distributing marketplaces.

## Validation Commands

Check marketplace JSON syntax before distribution:

```bash
claude plugin validate .
```

Or from within Claude Code:

```bash
/plugin validate .
```

## Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `File not found: .claude-plugin/marketplace.json` | Missing manifest | Create `.claude-plugin/marketplace.json` with required fields |
| `Invalid JSON syntax: Unexpected token...` | JSON syntax error | Check for missing commas, extra commas, or unquoted strings |
| `Duplicate plugin name "x" found in marketplace` | Two plugins share the same name | Give each plugin a unique `name` value |
| `plugins[0].source: Path traversal not allowed` | Source path contains `..` | Use paths relative to marketplace root without `..` |

## Validation Warnings

Non-blocking issues that should be addressed:

| Warning | Meaning |
|---------|---------|
| `Marketplace has no plugins defined` | Add at least one plugin to the `plugins` array |
| `No marketplace description provided` | Add `metadata.description` to help users understand your marketplace |
| `Plugin "x" uses npm source which is not yet fully implemented` | Use `github` or local path sources instead |

## Marketplace Not Loading

**Symptoms:** Cannot add marketplace or see plugins from it.

**Checklist:**

| Check | Action |
|-------|--------|
| URL accessible | Verify the marketplace URL is reachable |
| File exists | Confirm `.claude-plugin/marketplace.json` exists at the specified path |
| Valid JSON | Run `claude plugin validate` or `/plugin validate` |
| Access permissions | For private repositories, confirm you have access |

## Plugin Installation Failures

**Symptoms:** Marketplace appears but plugin installation fails.

**Checklist:**

| Check | Action |
|-------|--------|
| Source accessible | Verify plugin source URLs are reachable |
| Required files exist | Check that plugin directories contain required files |
| GitHub access | For GitHub sources, ensure repos are public or you have access |
| Manual test | Clone/download plugin sources manually to verify |

## Files Not Found After Installation

**Symptoms:** Plugin installs but references to files fail, especially files outside the plugin directory.

**Cause:** Plugins are copied to a cache directory when installed, not used in-place. Paths that reference files outside the plugin's directory (like `../shared-utils`) won't work because those files aren't copied.

**Solutions:**

1. **Use symlinks:** Symlinks are followed during copying, so linked files will be included
2. **Restructure:** Move shared files inside the plugin source path
3. **Use `${CLAUDE_PLUGIN_ROOT}`:** For paths in hooks and MCP configs (see below)

For complete details on plugin caching behavior, see [plugins-caching](../plugins/plugins-caching.md).

## The `${CLAUDE_PLUGIN_ROOT}` Variable

Plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` when installed. Use `${CLAUDE_PLUGIN_ROOT}` to reference files within the installed plugin directory.

**Where to use:**

| Context | Example |
|---------|---------|
| Hook commands | `"command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"` |
| MCP server paths | `"command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server"` |
| MCP server args | `"args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]` |

**Example:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
      }]
    }]
  },
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/server/main",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

## Key Points

- Run `claude plugin validate .` before distributing
- Path traversal (`..`) is blocked for security
- Plugins are cached, not used in-place
- Use `${CLAUDE_PLUGIN_ROOT}` for hook and MCP paths
- npm sources are not fully implemented yet
