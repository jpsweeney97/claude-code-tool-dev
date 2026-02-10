# Codex MCP FAQ

**Purpose:** Fast answers to the most common integration and operations questions.

---

## Basics

### 1) What is `codex mcp-server`?

It runs Codex as an MCP server (stdio transport) so MCP clients can call Codex tools.

### 2) How is that different from `codex mcp`?

`codex mcp` manages MCP servers that Codex consumes as a client. Different direction.

### 3) Which tools does Codex MCP expose?

At minimum: `codex` (new conversation) and `codex-reply` (continue existing thread).

### 4) What does `threadId` do?

It links follow-up turns to the same conversation context.

### 5) Do I need to pass model/sandbox every time?

Not required by the tool schema. However, this repository’s consultation integration passes resolved execution controls (`sandbox`, `approval-policy`, and `config.model_reasoning_effort`) explicitly for least privilege and deterministic behavior. Only pass `model` when overriding Codex’s default model.

---

## Authentication

### 6) Can I use interactive login?

Yes. Run `codex login` and reuse cached credentials until logout/expiry/revocation.

### 7) Can I use API keys instead?

Yes. Use `OPENAI_API_KEY` and optional `codex login --with-api-key` flow.

### 8) Should tokens appear in tool inputs or logs?

No. Never pass or log token material.

---

## Integration and Runtime

### 9) Why are no tools visible in my client?

Usually a stdio connectivity or process-launch issue. Verify direct command launch and version.

### 10) Why does `codex-reply` fail?

Most often the `threadId` is missing, stale, or malformed.

### 11) Which sandbox should I default to?

`read-only` unless a justified write path is required.

### 12) Is `danger-full-access` recommended?

Only for explicit break-glass scenarios with strong governance.

### 13) What approval policy should teams start with?

Policy depends on environment, but defaults should be documented and consistently enforced.

---

## Reliability and Operations

### 14) How do I reduce timeout pain?

Set clear timeout budgets, use bounded retries, and monitor latency trends.

### 15) What if upstream service is degraded?

Follow runbook: verify upstream health, switch to degraded guidance, and communicate impact.

### 16) How do I know if deployment is production-ready?

Use the production checklist in runbook + threat model + maturity model evidence bundle.

---

## Security

### 17) What are the top security mistakes?

Over-permissioned sandbox, secret leakage in logs, and missing policy/change controls.

### 18) What should always be redacted?

`id_token`, `access_token`, `refresh_token`, bearer headers, and key-like secrets.

### 19) Should prompt text be logged?

Not by default. Use strict debug gates and redaction if ever enabled.

---

## Learning Path

### 20) Where should a beginner start?

`docs/codex-mcp/learning-path/01-codex-mcp-concepts.md`, then the first-success tutorial.

### 21) What defines “expert” here?

Reliable operations, secure defaults, incident handling, and ability to teach/improve team patterns.

### 22) How do I assess progress objectively?

Use `docs/codex-mcp/assessments/codex-mcp-skill-maturity-model.md` and collect required evidence.

---

## References

- `../references/codex-mcp-server-beginner-to-expert.md`
- `../runbooks/codex-mcp-operations.md`
- `../security/codex-mcp-threat-model.md`
- `../assessments/codex-mcp-skill-maturity-model.md`
