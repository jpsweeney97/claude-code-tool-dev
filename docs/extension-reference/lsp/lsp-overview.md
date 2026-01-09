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

## Key Points

- LSP servers are plugin-only
- Provide code intelligence features
- Configure via .lsp.json in plugin
- Map file extensions to languages
