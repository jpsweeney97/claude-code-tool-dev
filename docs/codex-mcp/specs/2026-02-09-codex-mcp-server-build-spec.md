# Codex MCP Server — Build Specification

**Date:** 2026-02-09  
**Status:** Approved (decision-locked)  
**Scope:** Build requirements for an MCP server that exposes Codex consultation tools to the primary agent framework  
**Related spec:** `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`

> **Navigation note:** For consolidated onboarding and implementation context, start with `../codex-mcp-master-guide.md`. Use this document as the normative MCP server build contract.

---

## 1) Executive Summary

This specification defines how to build an MCP server that provides two tools:

1. `codex` — start a new Codex consultation thread.
2. `codex-reply` — continue an existing Codex thread.

The server sits between the primary agent runtime and Codex execution, enforcing:

- parameter validation
- deterministic defaults
- security boundaries (no credential leakage)
- robust error handling
- observability

This is a **server-layer** spec. Client/skill behavior is defined in the related consultation skill spec.

---

## 2) Why Build This (and When Not To)

### 2.1 Use Cases for a Custom Server

Build this server only if you need one or more of:

1. Organization-specific policy enforcement (sandbox/approval restrictions).
2. Unified telemetry and audit events.
3. Redaction controls and sensitive-data guards at the server boundary.
4. Multi-tenant routing and workspace isolation.
5. Controlled retries/timeouts and deterministic error envelopes.

### 2.2 When Not To Build

If built-in `codex mcp-server` behavior is sufficient, prefer using it directly and avoid duplicate maintenance.

---

## 3) Goals and Non-Goals

### 3.1 Goals

1. Expose stable MCP tools: `codex`, `codex-reply`.
2. Validate all inputs and resolve defaults consistently.
3. Execute Codex requests safely with bounded retries/timeouts.
4. Return deterministic responses with actionable failures.
5. Preserve thread continuity through `threadId`.
6. Emit non-secret diagnostic events for operations.

### 3.2 Non-Goals

1. Re-implement Codex model internals.
2. Replace Codex auth provider behavior.
3. Store or manage raw credentials directly.
4. Invent proprietary transport incompatible with MCP.

---

## 4) Normative References

Implementation must align with:

1. OpenAI Codex MCP server docs.
2. OpenAI Codex CLI/config/auth docs.
3. MCP protocol expectations (JSON-RPC over stdio for baseline transport).

When conflicts arise:

1. Security constraints in this spec.
2. Official protocol requirements.
3. This server’s API contract.

---

## 5) High-Level Architecture

```
Primary Agent Runtime
        │
        │ MCP (JSON-RPC)
        ▼
┌──────────────────────────┐
│   Codex MCP Server       │
│                          │
│  1) Schema Validator     │
│  2) Default Resolver     │
│  3) Policy Guard         │
│  4) Execution Adapter    │──► Codex runtime (CLI / API-backed)
│  5) Error Mapper         │
│  6) Telemetry Emitter    │
└──────────────────────────┘
        │
        ▼
MCP tool result (threadId, output, metadata)
```

---

## 6) Tool Surface

### 6.1 Tool: `codex`

Purpose: create a new consultation turn.

Required:

- `prompt: string`

Optional:

- `approval-policy: "untrusted" | "on-failure" | "on-request" | "never"`
- `base-instructions: string`
- `config: object` (open object; `additionalProperties: true`)
- `cwd: string`
- `include-plan-tool: boolean`
- `model: string`
- `profile: string`
- `sandbox: "read-only" | "workspace-write" | "danger-full-access"`

Defaults:

- `sandbox = "read-only"`
- `approval-policy = "never"` if `read-only`
- `approval-policy = "on-failure"` if `workspace-write` or `danger-full-access`
- `config.model_reasoning_effort = "high"`
- `model` omitted unless provided

### 6.2 Tool: `codex-reply`

Purpose: append a follow-up turn to existing thread.

Required:

- `prompt: string`

Optional:

- `threadId: string`
- `conversationId: string` (compatibility alias; deprecated)

Validation and normalization:

- At least one identifier is required (`threadId` or `conversationId`).
- If `threadId` exists, it is canonical and must be used.
- If only `conversationId` is provided, map it to canonical `threadId`.
- If both are present and unequal, return deterministic `INVALID_ARGUMENT`.
- If both are absent/empty, return deterministic `MISSING_REQUIRED_FIELD`.

---

## 7) JSON Schemas (Normative)

### 7.1 `codex` input schema

```json
{
  "type": "object",
  "required": ["prompt"],
  "additionalProperties": false,
  "properties": {
    "prompt": { "type": "string", "minLength": 1 },
    "approval-policy": {
      "type": "string",
      "enum": ["untrusted", "on-failure", "on-request", "never"]
    },
    "base-instructions": { "type": "string", "minLength": 1 },
    "config": {
      "type": "object",
      "additionalProperties": true
    },
    "cwd": { "type": "string", "minLength": 1 },
    "include-plan-tool": { "type": "boolean" },
    "model": { "type": "string", "minLength": 1 },
    "profile": { "type": "string", "minLength": 1 },
    "sandbox": {
      "type": "string",
      "enum": ["read-only", "workspace-write", "danger-full-access"]
    }
  }
}
```

### 7.2 `codex-reply` input schema

```json
{
  "type": "object",
  "required": ["prompt"],
  "additionalProperties": false,
  "properties": {
    "prompt": { "type": "string", "minLength": 1 },
    "threadId": { "type": "string", "minLength": 1 },
    "conversationId": { "type": "string", "minLength": 1 }
  },
  "anyOf": [
    { "required": ["threadId"] },
    { "required": ["conversationId"] }
  ]
}
```

### 7.3 `codex-reply` identifier normalization algorithm (normative)

1. Normalize `threadId` and `conversationId` by trimming outer whitespace; treat empty strings as absent.
2. If both are absent, return:
   - code: `MISSING_REQUIRED_FIELD`
   - message format: `"validation failed: missing conversation identifier. Got: {input!r:.100}"`
3. If both are present and values are unequal, return:
   - code: `INVALID_ARGUMENT`
   - message format: `"validation failed: threadId and conversationId mismatch. Got: {input!r:.100}"`
4. If `threadId` is present, use it as canonical continuity identifier.
5. Else map `conversationId` to canonical `threadId` before upstream dispatch.

---

## 8) Response Contract

### 8.1 Success Envelope

```json
{
  "ok": true,
  "threadId": "thread_xxx",
  "outputText": "...",
  "structuredContent": {
    "threadId": "thread_xxx",
    "outputText": "..."
  },
  "content": [
    { "type": "text", "text": "..." }
  ],
  "metadata": {
    "model": "o3",
    "sandbox": "read-only",
    "approvalPolicy": "never",
    "reasoningEffort": "high",
    "durationMs": 1234
  }
}
```

Minimum required keys: `ok`, `threadId`, `outputText`.

### 8.2 Error Envelope

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "input validation failed: invalid sandbox. Got: {'sandbox': 'nope'}",
    "retryable": false
  }
}
```

Server must return stable error codes and avoid stack traces in user-facing fields.

### 8.3 Continuity output contract (normative)

- `structuredContent.threadId` is the canonical continuity source.
- `content` remains compatibility output only and must not be treated as canonical continuity state.
- `threadId` at the envelope top level should mirror canonical `structuredContent.threadId`.

### 8.4 Tool Errors vs MCP/JSON-RPC Errors (Normative)

The server must distinguish:

1. **Tool-level failures** (validation, policy, auth, timeouts, upstream errors)
   - MUST return a normal MCP tool result whose payload matches the Error Envelope (`ok: false`).
   - MUST NOT rely on JSON-RPC error objects for these cases.

2. **Protocol-level failures** (malformed JSON-RPC, unknown methods, transport corruption)
   - SHOULD return JSON-RPC/MCP errors when the request is not a valid tool invocation.
   - MUST avoid leaking stack traces or sensitive material in error messages.

---

## 9) Error Taxonomy (Normative)

Standard server error codes:

1. `INVALID_ARGUMENT`
2. `MISSING_REQUIRED_FIELD`
3. `POLICY_VIOLATION`
4. `AUTH_UNAVAILABLE`
5. `THREAD_NOT_FOUND`
6. `TIMEOUT`
7. `UPSTREAM_UNAVAILABLE`
8. `INTERNAL_ERROR`

Retryability:

- Retryable: `TIMEOUT`, transient `UPSTREAM_UNAVAILABLE` (retryable means another attempt may succeed, not that the operation is guaranteed idempotent)
- Non-retryable: validation/policy/auth deterministic errors

Deterministic message format:

```
"{operation} failed: {reason}. Got: {input!r:.100}"
```

---

## 10) Authentication & Credential Handling

### 10.1 Accepted Auth Modes

1. Interactive login state managed by Codex runtime.
2. API key mode (`OPENAI_API_KEY`) managed by Codex runtime.

### 10.2 Hard Security Rules

1. Server must never require clients to pass tokens in tool arguments.
2. Server must never emit token material in responses, logs, or traces.
3. Server must never read/parse auth secrets unless explicit secure-debug mode exists and is gated off by default.
4. If upstream auth missing/expired, emit `AUTH_UNAVAILABLE` with remediation guidance.

Sensitive fields to always redact if encountered:

- `id_token`
- `access_token`
- `refresh_token`
- bearer headers
- key-like material (`sk-...`)

---

## 11) Policy Guardrails

Server must enforce policy before upstream execution:

1. Optional allowlist for sandbox mode per environment.
2. Optional denylist for `danger-full-access`.
3. Approval policy compatibility checks.
4. Optional model allowlist.
5. Prompt size cap (configurable) to prevent payload abuse.

On violation: return `POLICY_VIOLATION`.

---

## 12) Thread and State Management

### 12.1 Thread Identity

- `codex` returns a new `threadId`.
- `codex-reply` requires an existing conversation identifier and normalizes to canonical `threadId`.

### 12.2 State Model

Server should treat Codex as source-of-truth for thread state. Local state can cache:

- request metadata
- latency
- success/failure outcomes
- opaque thread reference

Local cache must not mutate semantic thread content.

### 12.3 Invalid Thread Behavior

If upstream indicates missing/invalid thread:

1. Return `THREAD_NOT_FOUND`.
2. Include recovery hint: client should reissue via `codex` with full briefing.

---

## 13) Execution Adapter Requirements

The adapter that calls Codex runtime must:

1. Convert validated payload into upstream invocation format.
2. Propagate resolved defaults explicitly.
3. Apply per-call timeout.
4. Classify upstream failures into standard error taxonomy.
5. Capture thread id from successful responses.

Timeout baseline:

- default 120s (configurable)

Retry policy:

- no automatic retries for failures where upstream execution is uncertain (e.g., timeout waiting for response)
- one automatic retry is allowed only for failures known to occur before dispatch (e.g., transient local process spawn/handshake failure)
- exponential backoff with jitter (e.g., 250–750ms)

Timeout messaging requirement:

- If a request times out after dispatch, return `TIMEOUT` with `retryable: true` and include an explicit warning that the upstream request may have been processed and a retry can create duplicate threads/messages.

---

## 14) Transport and Lifecycle

### 14.1 Required Transport

- MCP-compatible JSON-RPC over stdio (baseline).

### 14.2 Startup

On startup, server must:

1. Register tool schemas.
2. Validate runtime prerequisites.
3. Emit readiness signal.

### 14.3 Shutdown

On shutdown, server must:

1. stop accepting new requests
2. complete or cancel in-flight requests deterministically
3. flush buffered logs/telemetry

---

## 15) Observability and Audit

### 15.1 Required Metrics

Per-tool:

- request count
- success/failure count by error code
- latency p50/p95/p99
- timeout count
- retry count

### 15.2 Required Structured Fields

- `requestId`
- `toolName`
- `threadIdPresent` (boolean)
- `sandbox`
- `approvalPolicy`
- `reasoningEffort`
- `resultCode`
- `durationMs`

### 15.3 Prohibited Logging

Never log:

- prompt text by default
- credential material
- full bearer/auth headers

---

## 16) Performance & Scalability

1. Validation must be O(input size).
2. Server must support concurrent in-flight requests (configurable worker count).
3. Backpressure policy required when queue depth exceeds threshold.
4. Memory growth must be bounded; no unbounded request body retention.

---

## 17) Testing Plan (Required)

### 17.1 Unit Tests

1. Schema validation success/failure for both tools.
2. Default resolution matrix.
3. Error mapper classification.
4. Redaction utility behavior.
5. Policy enforcement outcomes.

### 17.2 Integration Tests (Mocked Upstream)

1. `codex` happy path returns thread and output.
2. `codex-reply` happy path appends by thread.
3. Timeout maps to `TIMEOUT` and does not automatically retry by default.
4. Invalid thread maps to `THREAD_NOT_FOUND`.
5. Auth failure maps to `AUTH_UNAVAILABLE`.
6. Policy violation blocks upstream call.

### 17.3 Protocol Conformance Tests

1. MCP tool registration shape.
2. JSON-RPC request/response compatibility.
3. Unknown method handling.
4. Malformed JSON handling.

### 17.4 Security Tests

1. Secret leakage regression tests for logs and responses.
2. Prompt redaction tests with token-like payloads.
3. Fuzz tests for oversized or malformed fields.

---

## 18) Acceptance Criteria

Implementation is complete when:

1. All required tests pass.
2. Both tools are discoverable and callable over MCP.
3. Error taxonomy is stable and documented.
4. No credentials are leaked in outputs/logs.
5. Timeout/retry behavior matches spec.
6. Thread continuity works for success cases and recovers deterministically for invalid thread cases.
7. Observability fields are emitted for every request.

---

## 19) Rollout Plan

### Phase 1 — Core server skeleton

- MCP transport + tool registration
- request validation
- execution adapter plumbing

### Phase 2 — Reliability and policy

- retries/timeouts
- policy guards
- standardized error mapping

### Phase 3 — Security and telemetry hardening

- redaction enforcement
- structured metrics/logging
- security regression tests

### Phase 4 — Production readiness

- load tests
- operational runbooks
- alerting thresholds

---

## 20) Operational Runbook (Minimum)

Document these procedures before production:

1. startup verification checklist
2. auth failure triage
3. upstream outage fallback
4. timeout spike investigation
5. thread-not-found recovery guidance
6. emergency policy lockdown (disable dangerous sandbox)

---

## 21) Resolved Decisions

1. Prompt/log retention is debug-gated opt-in only.
2. Redaction failures are fail-closed.
3. Dangerous mode never auto-escalates.
4. Strategy default is direct invocation when uncertain.
5. Reply continuity is `threadId` canonical with `conversationId` as compatibility alias.

---

## 22) Example MCP Tool Definitions (Reference)

### 22.1 `codex`

```json
{
  "name": "codex",
  "description": "Run a Codex consultation turn",
  "inputSchema": {
    "type": "object",
    "required": ["prompt"],
    "additionalProperties": false,
    "properties": {
      "prompt": { "type": "string", "minLength": 1 },
      "approval-policy": {
        "type": "string",
        "enum": ["untrusted", "on-failure", "on-request", "never"]
      },
      "base-instructions": { "type": "string", "minLength": 1 },
      "config": {
        "type": "object",
        "additionalProperties": true
      },
      "cwd": { "type": "string", "minLength": 1 },
      "include-plan-tool": { "type": "boolean" },
      "model": { "type": "string", "minLength": 1 },
      "profile": { "type": "string", "minLength": 1 },
      "sandbox": {
        "type": "string",
        "enum": ["read-only", "workspace-write", "danger-full-access"]
      }
    }
  }
}
```

### 22.2 `codex-reply`

```json
{
  "name": "codex-reply",
  "description": "Continue a Codex consultation thread",
  "inputSchema": {
    "type": "object",
    "required": ["prompt"],
    "additionalProperties": false,
    "properties": {
      "prompt": { "type": "string", "minLength": 1 },
      "threadId": { "type": "string", "minLength": 1 },
      "conversationId": { "type": "string", "minLength": 1 }
    },
    "anyOf": [
      { "required": ["threadId"] },
      { "required": ["conversationId"] }
    ]
  }
}
```
