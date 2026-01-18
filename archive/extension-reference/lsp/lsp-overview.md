---
id: lsp-overview
topic: LSP Servers Overview
category: lsp
tags: [lsp, language-server, diagnostics, code-intelligence]
related_to: [lsp-configuration, plugins-overview]
official_docs: https://code.claude.com/en/plugins-reference#lsp-servers
---

# LSP Servers Overview

LSP (Language Server Protocol) servers provide code intelligence: diagnostics, go-to-definition, type information, and hover documentation. LSP servers are **plugin-only components**.

## Purpose

- Instant diagnostics after file edits
- Go to definition and find references
- Type information and hover documentation
- Symbol search across project

## Plugin-Only Restriction

LSP servers can only be provided through plugins. They cannot be registered independently like MCP servers.

## Features

| Feature | Description |
|---------|-------------|
| Diagnostics | Errors and warnings after file edits |
| Navigation | Go to definition, find references |
| Type Info | Hover for types and documentation |
| Symbols | Find symbols across project |

## Available Official Plugins

| Plugin | Languages |
|--------|-----------|
| `pyright-lsp` | Python |
| `typescript-lsp` | TypeScript, JavaScript |
| `rust-lsp` | Rust |

## Configuration Schema

LSP configuration in `manifest.json`:

```json
{
  "lsp": {
    "servers": [
      {
        "id": "typescript",
        "command": "typescript-language-server",
        "args": ["--stdio"],
        "languages": ["typescript", "javascript"],
        "filePatterns": ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique server identifier |
| `command` | string | Command to start server |
| `args` | string[] | Command arguments |
| `env` | object | Environment variables |
| `initializationOptions` | object | LSP init options |
| `languages` | string[] | Language IDs to activate |
| `filePatterns` | string[] | Glob patterns for activation |

## Transport Options

| Transport | Use Case |
|-----------|----------|
| stdio | Default, most common |
| tcp | Network-based servers |
| pipe | Named pipe communication |

Most LSP servers use stdio transport. Specify with `--stdio` argument.

## How LSP Works

1. Plugin registers LSP server with Claude Code
2. When file matches patterns, server starts
3. Server receives file content on open/change
4. Server returns diagnostics, completions, etc.
5. Claude Code displays results

## Debug Logging

Enable LSP debug output for troubleshooting:

```json
{
  "lsp": {
    "debug": true,
    "logFile": "/tmp/lsp-debug.log"
  }
}
```

| Setting | Purpose |
|---------|---------|
| `debug` | Enable verbose logging |
| `logFile` | Write logs to file |
| `traceServer` | Log server communication |

## Key Points

- LSP servers are plugin-only
- Provide code intelligence features
- Configure via .lsp.json in plugin
- Map file extensions to languages
