---
id: plugins-cli
topic: Plugin CLI Commands
category: plugins
tags: [cli, install, uninstall, enable, disable, update, scripting]
requires: [plugins-overview, plugins-scopes]
related_to: [plugins-troubleshooting]
official_docs: https://code.claude.com/en/plugins
---

# Plugin CLI Commands

Non-interactive plugin management for scripting and automation.

## plugin install

Install a plugin from available marketplaces.

```bash
claude plugin install <plugin> [options]
```

**Arguments:**
- `<plugin>`: Plugin name or `plugin-name@marketplace-name`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scope <scope>` | Installation scope: `user`, `project`, or `local` | `user` |
| `-h, --help` | Display help | |

**Examples:**

```bash
# Install to user scope (default)
claude plugin install formatter@my-marketplace

# Install to project scope (shared with team)
claude plugin install formatter@my-marketplace --scope project

# Install to local scope (gitignored)
claude plugin install formatter@my-marketplace --scope local
```

## plugin uninstall

Remove an installed plugin.

```bash
claude plugin uninstall <plugin> [options]
```

**Arguments:**
- `<plugin>`: Plugin name or `plugin-name@marketplace-name`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scope <scope>` | Uninstall from scope: `user`, `project`, or `local` | `user` |
| `-h, --help` | Display help | |

**Aliases:** `remove`, `rm`

## plugin enable

Enable a disabled plugin.

```bash
claude plugin enable <plugin> [options]
```

**Arguments:**
- `<plugin>`: Plugin name or `plugin-name@marketplace-name`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scope <scope>` | Scope to enable: `user`, `project`, or `local` | `user` |
| `-h, --help` | Display help | |

## plugin disable

Disable a plugin without uninstalling it.

```bash
claude plugin disable <plugin> [options]
```

**Arguments:**
- `<plugin>`: Plugin name or `plugin-name@marketplace-name`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scope <scope>` | Scope to disable: `user`, `project`, or `local` | `user` |
| `-h, --help` | Display help | |

## plugin update

Update a plugin to the latest version.

```bash
claude plugin update <plugin> [options]
```

**Arguments:**
- `<plugin>`: Plugin name or `plugin-name@marketplace-name`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scope <scope>` | Scope to update: `user`, `project`, `local`, or `managed` | `user` |
| `-h, --help` | Display help | |

## Key Points

- All commands support `plugin-name@marketplace-name` format
- Default scope is `user` for all commands
- `uninstall` has aliases: `remove`, `rm`
- `update` additionally supports `managed` scope
