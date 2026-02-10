# 02 — First Success in 30 Minutes

**Stage:** Hands-on quick win  
**Goal:** Go from no setup to successful `codex` + `codex-reply` flow.

---

## Success Criteria

Use the canonical walkthrough and command set, then verify outcomes:

1. Follow `../codex-mcp-master-guide.md#canonical-quickstart`.
2. Run commands from `../codex-mcp-master-guide.md#canonical-command-reference`.
3. Confirm tool discovery (`codex`, `codex-reply`) and thread continuity via `threadId`.

---

## Canonical Procedure Pointers

- Quickstart owner: `../codex-mcp-master-guide.md#canonical-quickstart`
- Command owner: `../codex-mcp-master-guide.md#canonical-command-reference`
- Tool contract details: `../specs/2026-02-09-codex-mcp-server-build-spec.md`

---

## Expected Results (After Canonical Procedure)

- Clear textual response from both calls.
- Same thread lineage via `threadId`.
- No auth or transport errors.

---

## Quick Troubleshooting

| Symptom | Most Likely Cause | Fix |
|---|---|---|
| No tools visible | stdio connection issue | Use `../codex-mcp-master-guide.md#canonical-command-reference` exactly |
| Auth error | not logged in/expired login | Run auth flow from canonical command reference, then retry |
| Reply fails with invalid thread | stale or incorrect identifier | Start a new `codex` request and persist the new canonical `threadId` |

---

## Completion Evidence

Record these artifacts:

1. Command transcript for setup commands.
2. One successful `codex` response.
3. One successful `codex-reply` response.
4. Saved `threadId` value (or redacted suffix if required by policy).

Move to the failure lab after collecting evidence.
