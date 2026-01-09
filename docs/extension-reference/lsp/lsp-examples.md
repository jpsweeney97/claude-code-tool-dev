---
id: lsp-examples
topic: LSP Configuration Examples
category: lsp
tags: [examples, typescript, python, go]
requires: [lsp-overview, lsp-configuration]
official_docs: https://code.claude.com/en/plugins-reference#lsp-servers
---

# LSP Configuration Examples

Complete working LSP configurations.

## TypeScript/JavaScript

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact",
      ".js": "javascript",
      ".jsx": "javascriptreact"
    }
  }
}
```

## Python (Pyright)

```json
{
  "python": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python",
      ".pyi": "python"
    }
  }
}
```

## Go

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

## Rust

```json
{
  "rust": {
    "command": "rust-analyzer",
    "args": [],
    "extensionToLanguage": {
      ".rs": "rust"
    }
  }
}
```

## Multiple Languages

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact"
    }
  },
  "python": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python"
    }
  }
}
```

## Key Points

- Each language server is a separate key
- Use --stdio for most language servers
- Map all relevant file extensions
- Can configure multiple languages in one plugin
