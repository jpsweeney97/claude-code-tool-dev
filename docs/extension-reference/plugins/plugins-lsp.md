---
id: plugins-lsp
topic: LSP Server Configuration
category: plugins
tags: [lsp, language-server, code-intelligence, diagnostics]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-components, plugins-troubleshooting]
official_docs: https://code.claude.com/en/plugins
---

# LSP Server Configuration

Language Server Protocol integration for code intelligence.

## What LSP Provides

- **Instant diagnostics**: Claude sees errors and warnings after each edit
- **Code navigation**: Go to definition, find references, hover information
- **Language awareness**: Type information and documentation for symbols

## Discovery

Search for "lsp" in the `/plugin` Discover tab to find available LSP plugins from the official marketplace.

## Configuration Location

File: `.lsp.json` in plugin root, or inline in `plugin.json`

**Standalone `.lsp.json`:**

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

**Inline in `plugin.json`:**

```json
{
  "name": "my-plugin",
  "lspServers": {
    "go": {
      "command": "gopls",
      "args": ["serve"],
      "extensionToLanguage": {
        ".go": "go"
      }
    }
  }
}
```

## Required Fields

| Field | Description |
|-------|-------------|
| `command` | The LSP binary to execute (must be in PATH) |
| `extensionToLanguage` | Maps file extensions to language identifiers |

## Optional Fields

| Field | Description |
|-------|-------------|
| `args` | Command-line arguments for the LSP server |
| `transport` | Communication transport: `stdio` (default) or `socket` |
| `env` | Environment variables when starting server |
| `initializationOptions` | Options passed during server initialization |
| `settings` | Settings via `workspace/didChangeConfiguration` |
| `workspaceFolder` | Workspace folder path for the server |
| `startupTimeout` | Max time to wait for startup (milliseconds) |
| `shutdownTimeout` | Max time for graceful shutdown (milliseconds) |
| `restartOnCrash` | Auto-restart server if it crashes |
| `maxRestarts` | Maximum restart attempts before giving up |
| `loggingConfig` | Debug logging configuration |

## Debug Logging

The `loggingConfig` field enables verbose LSP logging when users pass `--enable-lsp-logging`:

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact"
    },
    "loggingConfig": {
      "args": ["--log-level", "4"],
      "env": {
        "TSS_LOG": "-level verbose -file ${CLAUDE_PLUGIN_LSP_LOG_FILE}"
      }
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `args` | Additional CLI arguments when logging enabled |
| `env` | Additional environment variables when logging enabled |

`${CLAUDE_PLUGIN_LSP_LOG_FILE}` expands to log file path. Logs written to `~/.claude/debug/`.

## Available LSP Plugins

Install from the official marketplace:

| Plugin | Language Server | Install Command |
|--------|-----------------|-----------------|
| `pyright-lsp` | Pyright (Python) | `pip install pyright` or `npm install -g pyright` |
| `typescript-lsp` | TypeScript Language Server | `npm install -g typescript-language-server typescript` |
| `rust-lsp` | rust-analyzer | [See rust-analyzer installation](https://rust-analyzer.github.io/manual.html#installation) |

## Installation Requirement

LSP plugins configure how Claude Code connects to a language server, but don't include the server itself. Install the language server binary separately:

```bash
# Install server first
npm install -g typescript-language-server typescript

# Then install plugin
claude plugin install typescript-lsp@official
```

If you see `Executable not found in $PATH` in the `/plugin` Errors tab, install the required binary.

## Key Points

- LSP provides diagnostics, navigation, and type awareness
- Install language server binary before installing LSP plugin
- Use `loggingConfig` for debugging with `--enable-lsp-logging`
- `${CLAUDE_PLUGIN_LSP_LOG_FILE}` for debug log path
