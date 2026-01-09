---
paths: packages/mcp-servers/**
---

# MCP Server Development

MCP (Model Context Protocol) servers extend Claude Code with custom tools, resources, and prompts. They run as separate processes that communicate via JSON-RPC over stdio or HTTP.

## When to Use MCP Servers

- **Custom tool integrations**: Connect to databases, APIs, or external services
- **Persistent services**: Long-running processes that maintain state across calls
- **Complex operations**: Operations too complex for Bash or requiring special libraries
- **Team infrastructure**: Shared capabilities across projects (deploy tools, ticket systems)

## When NOT to Use MCP Servers

- **Simple file operations**: Use built-in Read/Write/Edit tools
- **One-off scripts**: Use Bash or Python hooks
- **Prompt injection**: Use commands or skills
- **Event-driven automation**: Use hooks (MCP servers don't receive events)

## Structure

MCP servers are TypeScript packages:

```
packages/mcp-servers/<name>/
├── package.json          # With claudeCode.mcp metadata
├── tsconfig.json         # Extends ../../tsconfig.base.json
├── src/
│   └── index.ts          # Server entry point
└── dist/                 # Build output (gitignored)
```

## package.json Configuration (Project Convention)

**Note**: The `claudeCode.mcp` field is this project's convention for organizing MCP server metadata. Native Claude Code uses `.mcp.json` or CLI registration.

```json
{
  "name": "@claude-tools/<name>",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
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

## Basic Server Implementation

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "my_tool",
      description: "What this tool does",
      inputSchema: {
        type: "object",
        properties: {
          param1: { type: "string", description: "First parameter" },
        },
        required: ["param1"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "my_tool") {
    const result = await doSomething(args.param1);
    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

## MCP Capabilities

MCP servers can provide:

| Capability | Purpose | Example |
|------------|---------|---------|
| **Tools** | Actions Claude can invoke | Database queries, API calls |
| **Resources** | Data Claude can read | File contents, API responses |
| **Prompts** | Reusable prompt templates | Code review checklist |

## Tool Definition

Tools are the primary interface. Define them with clear schemas:

```typescript
{
  name: "query_database",
  description: "Execute a read-only SQL query against the database",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "SQL SELECT query to execute"
      },
      limit: {
        type: "number",
        description: "Maximum rows to return (default: 100)"
      }
    },
    required: ["query"]
  }
}
```

### Tool Design Principles

**Be specific in descriptions**
Claude uses descriptions to decide when to use tools. Vague descriptions lead to misuse.

**Define input schemas precisely**
Use JSON Schema to validate inputs. Include descriptions for each property.

**Return structured data**
Return JSON for complex results. Claude can parse and reason about structured data.

**Handle errors gracefully**
Return error information in the response, don't crash the server.

## Design Principles

### Servers are long-running
MCP servers stay alive across tool calls. Use this for connection pooling, caching.

### Tools should be idempotent when possible
Read operations should be safe to retry. Write operations should be clearly marked.

### Document side effects
If a tool modifies external state, make it explicit in the description.

### Validate inputs
Don't trust input. Validate against schema and sanitize before use.

### Log for debugging
Use stderr for logging. Claude Code captures this for troubleshooting.

## Common Patterns

### Database query tool

```typescript
{
  name: "query",
  description: "Execute read-only SQL query",
  inputSchema: {
    type: "object",
    properties: {
      sql: { type: "string" },
    },
    required: ["sql"]
  }
}

// In handler:
if (!args.sql.trim().toLowerCase().startsWith("select")) {
  return { content: [{ type: "text", text: "Error: Only SELECT queries allowed" }] };
}
```

### API wrapper tool

```typescript
{
  name: "fetch_tickets",
  description: "Fetch tickets from issue tracker. Returns up to 50 tickets.",
  inputSchema: {
    type: "object",
    properties: {
      status: { type: "string", enum: ["open", "closed", "all"] },
      assignee: { type: "string" }
    }
  }
}
```

### File operation tool

```typescript
{
  name: "search_logs",
  description: "Search application logs for patterns. Returns matching lines with context.",
  inputSchema: {
    type: "object",
    properties: {
      pattern: { type: "string", description: "Regex pattern to search" },
      since: { type: "string", description: "ISO timestamp to search from" }
    },
    required: ["pattern"]
  }
}
```

## Transport Types

| Transport | Use Case | Registration |
|-----------|----------|--------------|
| **stdio** | Local processes, system access | `claude mcp add --transport stdio <name> -- <cmd>` |
| **http** | Remote/cloud services (recommended) | `claude mcp add --transport http <name> <url>` |
| **sse** | Server-sent events (deprecated) | `claude mcp add --transport sse <name> <url>` |

## Anti-patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Vague tool descriptions | Claude misuses tool | Be specific about purpose and behavior |
| No input validation | Security risk, crashes | Validate all inputs |
| Blocking operations without timeout | Server hangs | Add timeouts to all external calls |
| Returning raw errors | Exposes internals | Return sanitized error messages |
| No rate limiting | Resource exhaustion | Add rate limits for expensive operations |
| Modifying state without documentation | Unexpected side effects | Document all write operations |
| Windows npx without cmd wrapper | "Connection closed" errors | Use `cmd /c npx` on native Windows |
| Large tool outputs | Warning at 10K tokens, max 25K | Paginate or filter responses |

## Testing

### Unit testing

```typescript
import { describe, it, expect } from "vitest";

describe("my_tool", () => {
  it("should return expected result", async () => {
    const result = await handleMyTool({ param1: "test" });
    expect(result.content[0].text).toContain("expected");
  });
});
```

### Manual testing

```bash
# Build the server
npm run build -w packages/mcp-servers/<name>

# Test with MCP inspector (if available)
npx @modelcontextprotocol/inspector dist/index.js

# Or register and test in Claude Code
claude mcp add <name> node packages/mcp-servers/<name>/dist/index.js
```

### Integration testing

1. Build server
2. Register with Claude Code
3. Start new session
4. Invoke tools and verify behavior
5. Check stderr logs for errors

## Workflow

1. Create package structure in `packages/mcp-servers/<name>/`
2. Implement server with tool definitions
3. Build: `npm run build -w packages/mcp-servers/<name>`
4. Test locally with MCP inspector
5. Register: `claude mcp add <name> node packages/mcp-servers/<name>/dist/index.js`
6. Test in Claude Code session
7. Deploy (manual; `scripts/promote` doesn't support MCP servers yet)

## Configuration Storage

MCP servers are configured in:

| Scope | Location | Use Case |
|-------|----------|----------|
| **Local** (default) | `~/.claude.json` per project | Per-project, not shared |
| **Project** | `.mcp.json` in project root | Checked into git, shared with team |
| **User** | `~/.claude.json` cross-project | Personal servers across all projects |

### .mcp.json format

```json
{
  "mcpServers": {
    "my-server": {
      "command": "/path/to/server",
      "args": ["--option"],
      "env": { "API_KEY": "${API_KEY}" },
      "type": "stdio"
    }
  }
}
```

**Environment variable expansion**: Use `${VAR}` or `${VAR:-default}` in command, args, env, url, headers.

## Registration Commands

```bash
# Add stdio server
claude mcp add --transport stdio <name> -- <command> [args...]
claude mcp add --transport stdio --env KEY=value <name> -- npx package

# Add HTTP server
claude mcp add --transport http <name> <url>
claude mcp add --transport http <name> <url> --header "Authorization: Bearer token"

# Add SSE server (deprecated - use HTTP where available)
claude mcp add --transport sse <name> <url>

# Add from JSON
claude mcp add-json <name> '<json>'
claude mcp add-json <name> '<json>' --scope user

# Import from Claude Desktop
claude mcp add-from-claude-desktop
claude mcp add-from-claude-desktop --scope user

# Management
claude mcp list
claude mcp get <server-name>
claude mcp remove <server-name>
claude mcp reset-project-choices

# Serve Claude Code as MCP server
claude mcp serve
```

**Important**: Options (`--transport`, `--env`, `--scope`) must come before server name. Use `--` to separate server name from command arguments.

### Scope flags

| Flag | Behavior |
|------|----------|
| `--scope local` | Default; stored in `~/.claude.json` per project |
| `--scope project` | Stored in `.mcp.json`; checked into git |
| `--scope user` | Stored in `~/.claude.json` cross-project |

## Compliance Checklist

Before deploying an MCP server, verify:

- [ ] All tools have clear, specific descriptions
- [ ] Input schemas define all parameters with types and descriptions
- [ ] Required vs optional parameters are correctly marked
- [ ] Input validation prevents malformed/malicious inputs
- [ ] Errors are handled gracefully (no server crashes)
- [ ] Side effects are documented in tool descriptions
- [ ] Timeouts are set for external calls
- [ ] Logging goes to stderr for debugging
- [ ] Unit tests cover core functionality
- [ ] Integration tested with Claude Code

## Security Considerations

### Input sanitization
Never pass user input directly to shells, databases, or APIs without validation.

### Credential handling
Use environment variables for secrets. Never hardcode credentials.

### Rate limiting
Expensive operations (API calls, queries) should have rate limits.

### Principle of least privilege
Tools should request minimal permissions. Read-only where possible.

## See Also

- **settings.md** — Configure MCP permissions with `mcp__servername` rules
- **plugins.md** — Bundle MCP servers with plugins for distribution
- **hooks.md** — Use hooks for simpler automation (MCP for persistent services)
- **agents.md** — Agents can use MCP tools via `tools` field

## References

- [MCP Specification](https://modelcontextprotocol.io/docs) — Official protocol documentation
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) — SDK reference
- @.claude/skills/claude-tool-audit/references/fallback-specs.md — Tool behavioral patterns
