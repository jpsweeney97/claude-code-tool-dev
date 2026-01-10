---
id: mcp-authentication
topic: MCP Authentication
category: mcp
tags: [authentication, oauth, headers, tokens]
requires: [mcp-overview]
related_to: [mcp-transports, mcp-scopes]
official_docs: https://code.claude.com/en/mcp
---

# MCP Authentication

MCP servers support header-based and OAuth authentication.

## Header Authentication

Pass headers during registration:

```bash
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer $TOKEN"
```

## OAuth Authentication

Many MCP servers require OAuth flow:

```bash
# 1. Add server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# 2. Authenticate (opens browser)
/mcp
# Select "Authenticate" for the server
```

### OAuth Features

| Feature | Behavior |
|---------|----------|
| Token storage | Tokens stored securely |
| Auto-refresh | Tokens refreshed automatically |
| Clear auth | Use "Clear authentication" in `/mcp` menu |
| Browser fallback | Copy URL manually if browser doesn't open |
| Transport | OAuth works with HTTP servers |

## Environment Variables in Config

Store tokens in environment, reference in config:

```json
{
  "mcpServers": {
    "api": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

## Key Points

- Use `--header` for static tokens
- Use `/mcp` for OAuth flow
- Tokens stored securely and refreshed automatically
- "Clear authentication" in `/mcp` menu to revoke access
- Copy browser URL if auto-open fails
- OAuth works with HTTP servers
- Store tokens in environment variables, use `${VAR}` in config
