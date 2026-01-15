# docs-kb Claude Code Plugin

Verification skill for Claude Code that checks documentation before writing code.

## Prerequisites

- [docs-kb](https://github.com/username/docs-kb) installed and configured as an MCP server
- Documentation sources ingested

## Installation

1. Clone this plugin to your Claude Code plugins directory:
   ```bash
   cd ~/.claude/plugins
   git clone <repo-url>/docs-kb-plugin
   ```

   Or symlink from your local clone:
   ```bash
   ln -s /path/to/docs-kb/docs-kb-plugin ~/.claude/plugins/docs-kb-plugin
   ```

2. Restart Claude Code or run `/refresh` to load the plugin.

## Usage

Invoke the verification skill with:

```
/docs-kb:verify
```

Or Claude will use it automatically when you ask to "verify this" or "check the docs".

## What it does

1. **Identifies** APIs/patterns to verify from your current task
2. **Discovers** relevant documentation sources via `list_sources`
3. **Queries** documentation with `ask` tool
4. **Synthesizes** results into concise verification summaries

## Example

```
User: Help me create a LangChain agent with tools

Claude: [Uses /docs-kb:verify]
   -> Identifies: AgentExecutor, create_tool_calling_agent
   -> Queries langchain source
   -> Returns verified signatures, examples, gotchas
   -> Proceeds with verified knowledge
```
