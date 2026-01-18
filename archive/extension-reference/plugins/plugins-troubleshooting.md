---
id: plugins-troubleshooting
topic: Plugin Troubleshooting
category: plugins
tags: [debugging, troubleshooting, errors, hooks, mcp, issues]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-cli, plugins-caching]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Troubleshooting

Debugging tools and solutions for common plugin issues.

## Debug Command

Use `claude --debug` to see plugin loading details:

```bash
claude --debug
```

Shows:
- Which plugins are being loaded
- Errors in plugin manifests
- Command, agent, and hook registration
- MCP server initialization

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Invalid `plugin.json` | Validate JSON with `claude plugin validate` or `/plugin validate` |
| Commands not appearing | Wrong directory structure | Ensure `commands/` at root, not in `.claude-plugin/` |
| Hooks not firing | Script not executable | Run `chmod +x script.sh` |
| MCP server fails | Missing `${CLAUDE_PLUGIN_ROOT}` | Use variable for all plugin paths |
| Path errors | Absolute paths used | All paths must be relative and start with `./` |
| LSP `Executable not found` | Language server not installed | Install the binary (e.g., `npm install -g typescript-language-server`) |

## Error Messages

**Manifest validation errors:**

- `Invalid JSON syntax: Unexpected token } in JSON at position 142`: Missing commas, extra commas, or unquoted strings
- `Plugin has an invalid manifest file at .claude-plugin/plugin.json. Validation errors: name: Required`: A required field is missing
- `Plugin has a corrupt manifest file at .claude-plugin/plugin.json. JSON parse error: ...`: JSON syntax error

**Plugin loading errors:**

- `Warning: No commands found in plugin my-plugin custom directory: ./cmds. Expected .md files or SKILL.md in subdirectories.`: Command path contains no valid files
- `Plugin directory not found at path: ./plugins/my-plugin. Check that the marketplace entry has the correct path.`: The `source` path in marketplace.json points to non-existent directory
- `Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.`: Remove duplicate component definitions or set `strict: true` in marketplace entry

## Hook Troubleshooting

**Script not executing:**

1. Check script is executable: `chmod +x ./scripts/your-script.sh`
2. Verify shebang line: First line should be `#!/bin/bash` or `#!/usr/bin/env bash`
3. Check path uses `${CLAUDE_PLUGIN_ROOT}`: `"command": "${CLAUDE_PLUGIN_ROOT}/scripts/your-script.sh"`
4. Test script manually: `./scripts/your-script.sh`

**Hook not triggering:**

1. Verify event name is correct (case-sensitive): `PostToolUse`, not `postToolUse`
2. Check matcher pattern: `"matcher": "Write|Edit"` for file operations
3. Confirm hook type is valid: `command`, `prompt`, or `agent`

## MCP Server Troubleshooting

**Server not starting:**

1. Check command exists and is executable
2. Verify paths use `${CLAUDE_PLUGIN_ROOT}` variable
3. Check MCP server logs: `claude --debug` shows initialization errors
4. Test server manually outside Claude Code

**Tools not appearing:**

1. Ensure server is configured in `.mcp.json` or `plugin.json`
2. Verify server implements MCP protocol correctly
3. Check for connection timeouts in debug output

## Directory Structure Mistakes

**Symptoms:** Plugin loads but components (commands, agents, hooks) are missing.

**Problem:** Components inside `.claude-plugin/` instead of plugin root.

**Correct structure:**

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      <- Only manifest here
├── commands/            <- At root level
├── agents/              <- At root level
└── hooks/               <- At root level
```

**Debug checklist:**

1. Run `claude --debug` and look for "loading plugin" messages
2. Check each component directory is listed in debug output
3. Verify file permissions allow reading plugin files

## Key Points

- Use `claude --debug` for loading diagnostics
- Components go at plugin root, not in `.claude-plugin/`
- Scripts must be executable (`chmod +x`)
- Use `${CLAUDE_PLUGIN_ROOT}` for all plugin paths
