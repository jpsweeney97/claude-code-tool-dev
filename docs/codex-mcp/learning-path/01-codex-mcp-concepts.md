# 01 — Codex MCP Concepts

**Stage:** Foundations  
**Goal:** Build an accurate mental model before touching implementation.

---

## Learning Objectives

After this module, you should be able to:

1. Differentiate `codex mcp-server` from `codex mcp ...` commands.
2. Explain how `codex` and `codex-reply` tool calls work.
3. Describe sandbox and approval policy trade-offs.
4. Explain `threadId` continuity and failure recovery paths.
5. Identify baseline security boundaries for auth and tokens.

---

## Concept Map

| Concept | What It Means | Why It Matters |
|---|---|---|
| MCP | Standard protocol for tool exposure/invocation | Enables client/server interoperability |
| `codex mcp-server` | Runs Codex as MCP server over stdio | Makes Codex tools callable by MCP clients |
| `codex mcp add/list/login` | Configures MCP servers Codex can consume | Different workflow from running Codex as server |
| `codex` tool | Starts a new consultation thread | Entry point for first-turn reasoning |
| `codex-reply` tool | Continues an existing consultation thread | Maintains conversation continuity |
| `threadId` | Conversation handle for follow-up turns | Required for coherent multi-turn workflows |

---

## How a Request Flows

1. MCP client connects to `codex mcp-server` over stdio.
2. Client invokes `codex` with prompt and optional runtime controls.
3. Server executes Codex call and returns output + `threadId`.
4. Client invokes `codex-reply` with `threadId` for follow-up.
5. Repeat until task is complete.

---

## Runtime Control Model

### Sandbox

- `read-only`: safest default.
- `workspace-write`: allows controlled edits.
- `danger-full-access`: high risk; use break-glass controls only.

### Approval policy

- `untrusted`
- `on-failure`
- `on-request`
- `never`

### Reasoning effort

- `minimal`, `low`, `medium`, `high`, `xhigh`

Use defaults unless there is a clear reason to override.

---

## Security Baseline

1. Keep auth outside prompt payloads.
2. Never include tokens (`id_token`, `access_token`, `refresh_token`) in docs/logs/prompts.
3. Default to least privilege sandbox.
4. Redact sensitive material before tool invocation.

---

## Common Misconceptions

| Misconception | Correction |
|---|---|
| “`codex mcp-server` and `codex mcp add` are the same thing.” | One runs a server; the other manages servers Codex consumes. |
| “I can continue a conversation without `threadId`.” | `codex-reply` requires `threadId`; otherwise start a new thread. |
| “Read-only means no file visibility.” | Read-only blocks writes, not reads. |
| “Danger-full-access is just faster workspace-write.” | It removes sandbox protections and needs explicit governance. |

---

## Self-Check (Pass/Fail)

- Can you explain the difference between server mode and client-management mode?
- Can you describe when to use `codex` vs `codex-reply`?
- Can you justify a default sandbox/approval policy for a new team?
- Can you list at least three sensitive fields that must never appear in logs?

If any answer is “no,” review this module before moving forward.

