---
id: lsp-configuration
topic: LSP Configuration Schema
category: lsp
tags: [configuration, schema, lsp-json, extensions]
requires: [lsp-overview]
related_to: [lsp-examples, plugins-manifest]
official_docs: https://code.claude.com/en/plugins-reference#lsp-servers
---

# LSP Configuration Schema

LSP servers are configured in `.lsp.json` at the plugin root.

## Full Schema

```json
{
  "<language-id>": {
    "command": "<executable>",
    "args": ["<arg1>", "<arg2>"],
    "extensionToLanguage": {
      ".<ext>": "<language-id>"
    },
    "loggingConfig": {
      "args": ["--log-level", "4"],
      "env": {
        "LOG_VAR": "${CLAUDE_PLUGIN_LSP_LOG_FILE}"
      }
    }
  }
}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | Yes | Executable to run |
| `args` | array | No | Command-line arguments |
| `extensionToLanguage` | object | Yes | File extension to language mapping |
| `loggingConfig` | object | No | Debug logging configuration |

## Extension to Language Mapping

Maps file extensions to LSP language identifiers:

```json
{
  "extensionToLanguage": {
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".js": "javascript",
    ".jsx": "javascriptreact"
  }
}
```

## Debug Logging

Enable verbose logging for troubleshooting:

```json
{
  "loggingConfig": {
    "args": ["--log-level", "4"],
    "env": {
      "TSS_LOG": "-level verbose -file ${CLAUDE_PLUGIN_LSP_LOG_FILE}"
    }
  }
}
```

Environment variable `${CLAUDE_PLUGIN_LSP_LOG_FILE}` expands to plugin's log file path.

## Key Points

- Configure in .lsp.json at plugin root
- Map extensions to language IDs
- Use loggingConfig for debugging
- ${CLAUDE_PLUGIN_LSP_LOG_FILE} for log output
