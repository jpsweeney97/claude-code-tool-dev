---
id: commands-builtin
topic: Built-in Commands Reference
category: commands
tags: [commands, builtin, reference, cli]
related_to: [commands-overview]
official_docs: https://code.claude.com/en/slash-commands
---

# Built-in Commands Reference

Claude Code includes built-in slash commands for session management, configuration, and development workflows.

## Command Reference

| Command | Purpose |
|---------|---------|
| `/add-dir` | Add additional working directories |
| `/agents` | Manage custom AI subagents for specialized tasks |
| `/bashes` | List and manage background tasks |
| `/bug` | Report bugs (sends conversation to Anthropic) |
| `/clear` | Clear conversation history |
| `/compact [instructions]` | Compact conversation with optional focus instructions |
| `/config` | Open the Settings interface (Config tab) |
| `/context` | Visualize current context usage as a colored grid |
| `/cost` | Show token usage statistics (see [cost tracking guide](https://code.claude.com/en/costs#using-the-cost-command) for subscription details) |
| `/doctor` | Checks the health of your Claude Code installation |
| `/exit` | Exit the REPL |
| `/export [filename]` | Export the current conversation to a file or clipboard |
| `/help` | Get usage help |
| `/hooks` | Manage hook configurations for tool events |
| `/ide` | Manage IDE integrations and show status |
| `/init` | Initialize project with CLAUDE.md guide |
| `/install-github-app` | Set up Claude GitHub Actions for a repository |
| `/login` | Switch Anthropic accounts |
| `/logout` | Sign out from your Anthropic account |
| `/mcp` | Manage MCP server connections and OAuth authentication |
| `/memory` | Edit CLAUDE.md memory files |
| `/model` | Select or change the AI model |
| `/output-style [style]` | Set the output style directly or from a selection menu |
| `/permissions` | View or update [permissions](https://code.claude.com/en/iam#configuring-permissions) |
| `/plan` | Enter plan mode directly from the prompt |
| `/plugin` | Manage Claude Code plugins |
| `/pr-comments` | View pull request comments |
| `/privacy-settings` | View and update your privacy settings |
| `/release-notes` | View release notes |
| `/rename <name>` | Rename the current session for easier identification |
| `/remote-env` | Configure remote session environment (claude.ai subscribers) |
| `/resume [session]` | Resume a conversation by ID or name, or open the session picker |
| `/review` | Request code review |
| `/rewind` | Rewind the conversation and/or code |
| `/sandbox` | Enable sandboxed bash tool with filesystem and network isolation |
| `/security-review` | Complete a security review of pending changes |
| `/stats` | Visualize daily usage, session history, streaks, and model preferences |
| `/status` | Open the Settings interface (Status tab) showing version, model, account, and connectivity |
| `/statusline` | Set up Claude Code's status line UI |
| `/teleport` | Resume a remote session from claude.ai (claude.ai subscribers) |
| `/terminal-setup` | Install Shift+Enter key binding for newlines (VS Code, Alacritty, Zed, Warp) |
| `/theme` | Change the color theme |
| `/todos` | List current TODO items |
| `/usage` | Show plan usage limits and rate limit status (subscription plans only) |
| `/vim` | Enter vim mode for alternating insert and command modes |

## Categories

### Session Management
`/clear`, `/compact`, `/exit`, `/export`, `/rename`, `/resume`, `/rewind`

### Configuration
`/config`, `/hooks`, `/memory`, `/model`, `/output-style`, `/permissions`, `/privacy-settings`, `/statusline`, `/theme`

### Account & Authentication
`/login`, `/logout`, `/usage`

### Development
`/init`, `/review`, `/security-review`, `/sandbox`, `/pr-comments`

### Diagnostics
`/context`, `/cost`, `/doctor`, `/stats`, `/status`, `/release-notes`

### Extensions
`/agents`, `/mcp`, `/plugin`

### Environment
`/add-dir`, `/ide`, `/terminal-setup`, `/bashes`

### Remote Sessions
`/remote-env`, `/teleport`

### Support
`/bug`, `/help`

## Key Points

- Built-in commands cannot be invoked via the Skill tool
- Custom commands can shadow built-in names (not recommended)
- Use `/help` to see all available commands in current session
