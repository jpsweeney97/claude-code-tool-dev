# 02 — First Success in 30 Minutes

**Stage:** Hands-on quick win  
**Goal:** Go from no setup to successful `codex` + `codex-reply` flow.

---

## Success Criteria

You are done when all are true:

1. MCP inspector successfully spawns `codex mcp-server`.
2. MCP inspector shows `codex` and `codex-reply`.
3. First `codex` call returns response + `threadId`.
4. Follow-up `codex-reply` call succeeds using same `threadId`.

---

## Prerequisites

- Codex installed (`codex --version` works).
- Auth completed (`codex login status` returns authenticated state).
- Network access allowed for Codex runtime.

---

## Step-by-Step

### Step 1: Verify install and auth

```bash
codex --version
codex mcp-server --help
codex login status
```

If not logged in:

```bash
codex login
```

### Step 2: Inspect tools (recommended)

```bash
npx @modelcontextprotocol/inspector codex mcp-server
```

This command starts `codex mcp-server` for you. Do not run `codex mcp-server` separately for the inspector flow.

### Step 3: Confirm tool discovery

Confirm tool list contains:

- `codex`
- `codex-reply`

### Step 4: Run first tool call (`codex`)

Use input:

```json
{
  "prompt": "Give me a pragmatic code review checklist for a TypeScript service."
}
```

Capture and save returned `threadId`.

### Step 5: Run follow-up call (`codex-reply`)

Use input:

```json
{
  "threadId": "<thread-from-step-4>",
  "prompt": "Now rewrite that checklist for high-risk production migrations."
}
```

### Step 6: Run server standalone (debugging only)

You can run the server directly to observe startup behavior, but because transport is stdio, a client typically spawns the server process. Do not expect to “attach” from another terminal like you would with an HTTP server.

```bash
codex mcp-server
```

---

## Expected Results

- Clear textual response from both calls.
- Same thread lineage via `threadId`.
- No auth or transport errors.

---

## Quick Troubleshooting

| Symptom | Most Likely Cause | Fix |
|---|---|---|
| No tools visible | stdio connection issue | Re-run inspector and ensure direct process launch |
| Auth error | not logged in/expired login | `codex login` then retry |
| Reply fails with invalid thread | stale or incorrect `threadId` | restart with new `codex` call |

---

## Completion Evidence

Record these artifacts:

1. Command transcript for setup commands.
2. One successful `codex` response.
3. One successful `codex-reply` response.
4. Saved `threadId` value (or redacted suffix if required by policy).

Move to the failure lab after collecting evidence.
