---
paths: packages/mcp-servers/**
---

# MCP Server Development

## Structure

```
packages/mcp-servers/<name>/
├── package.json      # With claudeCode.mcp metadata
├── tsconfig.json     # Extends ../../tsconfig.base.json
├── src/
│   └── index.ts
└── dist/             # Build output (gitignored)
```

## package.json Metadata

```json
{
  "name": "@claude-tools/<name>",
  "claudeCode": {
    "mcp": {
      "transport": "stdio",
      "command": "node dist/index.js",
      "env": ["OPTIONAL_ENV_VAR"]
    }
  }
}
```

## tsconfig.json

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

## Workflow

1. Create package structure
2. Develop and test: `npm run build -w packages/mcp-servers/<name>`
3. Promote: `uv run scripts/promote mcp-server <name>`
   - Builds server
   - Registers via `claude mcp add`
   - Updates `.mcp.json`
