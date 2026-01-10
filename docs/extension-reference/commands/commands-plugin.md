---
id: commands-plugin
topic: Plugin Commands
category: commands
tags: [commands, plugins, distribution, namespacing]
requires: [commands-overview]
related_to: [plugins-components, commands-frontmatter]
official_docs: https://code.claude.com/en/slash-commands
---

# Plugin Commands

Plugins can provide custom slash commands distributed through plugin marketplaces.

## How Plugin Commands Work

Plugin commands are:

- **Namespaced**: Use `/plugin-name:command-name` format to avoid conflicts
- **Automatically available**: Once installed and enabled, appear in `/help`
- **Fully integrated**: Support all command features (arguments, frontmatter, bash execution, file references)

## Plugin Command Structure

**Location**: `commands/` directory in plugin root

**File format**: Markdown files with frontmatter

```markdown
---
description: Brief description of what the command does
---

# Command Name

Detailed instructions for Claude on how to execute this command.
Include specific guidance on parameters, expected outcomes, and special considerations.
```

## Invocation Patterns

```bash
# Direct command (when no conflicts)
/command-name

# Plugin-prefixed (when needed for disambiguation)
/plugin-name:command-name

# With arguments (if command supports them)
/command-name arg1 arg2
```

The plugin prefix is optional unless there are name collisions with other commands.

## Features

Plugin commands support:

- **Arguments**: Use `$ARGUMENTS` and `$1`, `$2` placeholders
- **Subdirectories**: Organize commands in subdirectories for namespacing
- **Bash integration**: Execute shell scripts with `` `!command` `` syntax
- **File references**: Reference project files with `@path`
- **Frontmatter**: All standard frontmatter fields

## Visibility

Plugin commands show `(plugin-name)` in `/help` output to indicate their source.

## Key Points

- Plugin prefix optional unless name collision exists
- Same features as project/user commands
- Distributed via plugin marketplaces
- Automatically discovered on plugin install
