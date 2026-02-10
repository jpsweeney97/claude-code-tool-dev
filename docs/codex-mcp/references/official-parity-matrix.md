# Official Parity Matrix (Codex MCP Docs)

**Verified date:** 2026-02-10  
**Final verification timestamp (UTC):** 2026-02-10T05:10:12Z  
**Verified by:** docs refactor plan v2.2 implementation pass

This matrix maps local canonical claims in `docs/codex-mcp` to official OpenAI documentation sources.

| Parity claim | Local canonical source | Official source URL | Verified date | Status |
|---|---|---|---|---|
| `codex` MCP tool requires `prompt`; execution controls can be optional | `../specs/2026-02-09-codex-mcp-server-build-spec.md` | `https://developers.openai.com/codex/mcp` | 2026-02-10 | Verified |
| `codex-reply` uses thread continuity and accepts `prompt` for follow-up turns | `../specs/2026-02-09-codex-mcp-server-build-spec.md` | `https://developers.openai.com/codex/mcp` | 2026-02-10 | Verified |
| Deprecated compatibility alias behavior for `conversationId` is documented and normalized to canonical `threadId` | `../specs/2026-02-09-codex-mcp-server-build-spec.md` | `https://developers.openai.com/codex/mcp` | 2026-02-10 | Verified |
| Canonical continuity output uses `structuredContent.threadId`; `content` remains compatibility output | `../specs/2026-02-09-codex-mcp-server-build-spec.md` | `https://developers.openai.com/codex/mcp` | 2026-02-10 | Verified |
| New MCP config key name parity: `mcp_servers.<id>.startup_timeout_sec` | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/config-reference` | 2026-02-10 | Verified |
| New MCP config key name parity: `mcp_servers.<id>.tool_timeout_sec` | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/config-reference` | 2026-02-10 | Verified |
| New MCP config key name parity: `mcp_oauth_credentials_store` | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/config-reference` | 2026-02-10 | Verified |
| CLI authentication status command is `codex login status` | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/auth` | 2026-02-10 | Verified |
| API key authentication flow includes `--with-api-key` login mode | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/auth` | 2026-02-10 | Verified |
| MCP inspector-driven startup command remains `npx @modelcontextprotocol/inspector@0.20.0 codex mcp-server` | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/mcp` | 2026-02-10 | Verified |
| Agents SDK integration guidance aligns with tool invocation and continuity principles | `../cookbooks/client-integration-recipes.md` | `https://developers.openai.com/codex/guides/agents-sdk` | 2026-02-10 | Verified |
| CLI command behavior and top-level command families align with official CLI docs | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/cli` | 2026-02-10 | Verified |
| Command-level option behavior references the official CLI reference | `../codex-mcp-master-guide.md` | `https://developers.openai.com/codex/cli/reference` | 2026-02-10 | Verified |

## Official baseline URLs (locked)

- `https://developers.openai.com/codex/guides/agents-sdk`
- `https://developers.openai.com/codex/mcp`
- `https://developers.openai.com/codex/cli`
- `https://developers.openai.com/codex/cli/reference`
- `https://developers.openai.com/codex/config-reference`
- `https://developers.openai.com/codex/auth`
