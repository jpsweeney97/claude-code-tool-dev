# Codex Consultation Skill — Implementation Specification

**Date:** 2026-02-09  
**Status:** Approved (decision-locked)  
**Scope:** Defines what must be built for the `/codex` skill workflow described in `.claude/skills/codex/SKILL.md`  
**Primary outcome:** A deterministic, testable implementation contract for consulting OpenAI Codex as a secondary reviewer

> **Navigation note:** For consolidated onboarding and implementation context, start with `../codex-mcp-master-guide.md`. Use this document as the normative client/skill build contract.

---

## 1) Goal

Build a robust consultation flow where the primary agent can invoke Codex via MCP for second opinions on architecture, debugging, code review, and planning, while preserving:

- deterministic behavior
- strong security boundaries (no credential leakage)
- clear defaults
- actionable response handoff

This document is the build contract. If implementation behavior conflicts with this spec, this spec wins unless superseded by a newer approved spec.

---

## 2) Problem Statement

The current skill prompt is useful operational guidance but is not a complete build spec. It lacks explicit acceptance criteria, validation rules, failure behavior, and test coverage requirements. This introduces ambiguity in implementation and review.

This spec closes those gaps.

---

## 3) Definitions

- **Primary agent:** The agent handling the user session directly.
- **Consultant agent:** Codex, invoked through MCP tools.
- **New consultation:** A first call using `mcp__codex__codex`.
- **Follow-up consultation:** A continuation call using `mcp__codex__codex-reply`.
- **Briefing:** Structured prompt payload containing task context, relevant material, and a specific question.
- **Session strategy:** Either direct invocation or delegated subagent management.

---

## 4) Scope & Non-Goals

### 4.1 In Scope

1. Parse `/codex` command flags and prompt text.
2. Build a structured Codex briefing.
3. Select invocation strategy (direct vs delegated).
4. Invoke Codex tools with validated parameters and defaults.
5. Continue conversations by canonical `threadId` (with compatibility alias handling).
6. Relay consultant output with primary-agent judgment.
7. Handle errors deterministically.
8. Enforce auth/token safety requirements.

### 4.2 Out of Scope

1. Implementing Codex CLI itself.
2. Defining Codex model internals.
3. Replacing the primary agent with Codex.
4. Adding new MCP transport protocols.
5. Long-term credential lifecycle management beyond documented CLI behavior.

---

## 5) Source-of-Truth Constraints

Implementation must align with official OpenAI Codex docs and local CLI behavior.

Minimum constraints:

1. `prompt` is required for new calls; other call fields are optional unless overridden.
2. Supported sandbox modes include `read-only`, `workspace-write`, `danger-full-access`.
3. Supported approval policies include `untrusted`, `on-failure`, `on-request`, `never`.
4. Supported reasoning effort includes `minimal`, `low`, `medium`, `high`, `xhigh`.
5. Read-only mode permits reading/browsing files, not writes.
6. Authentication may be interactive login or API key login (`OPENAI_API_KEY`).

---

## 6) Functional Requirements

### FR-1: Command Argument Parsing

The parser must accept this surface form:

```
/codex [-m <model>] [-s <sandbox>] [-a <approval-policy>] [-t <reasoning-effort>] [PROMPT...]
```

Allowed values:

- `sandbox`: `read-only | workspace-write | danger-full-access`
- `approval-policy`: `untrusted | on-failure | on-request | never`
- `reasoning-effort`: `minimal | low | medium | high | xhigh`

Validation behavior:

1. Reject unknown flags.
2. Reject missing values after flags that require values.
3. Reject invalid enum values.
4. Preserve all remaining text after flags as prompt, including punctuation.
5. Trim outer whitespace from prompt.

Error format (deterministic):

```
"argument parsing failed: {reason}. Got: {input!r:.100}"
```

### FR-2: Default Resolution

If omitted:

- `model`: omitted from tool call (Codex default)
- `sandbox`: `read-only`
- `approval-policy`:
  - `never` when sandbox = `read-only`
  - `on-failure` when sandbox ∈ {`workspace-write`, `danger-full-access`}
- `reasoning-effort`: `high`

If user sets `-a`, explicit value always wins.

### FR-3: Briefing Assembly

Before invocation, the agent must build a briefing with exactly these top-level sections:

```
## Context
...

## Material
...

## Question
...
```

Briefing content requirements:

1. Include current objective and why consultation is needed.
2. Include decisions already made and trade-offs considered.
3. Include relevant artifacts:
   - inline excerpt when small and essential
   - file paths or concise summaries when large
4. Include failed attempts and observed failure modes (if any).
5. End with one explicit, answerable question.

### FR-4: Invocation Strategy Selection

Strategy decision:

- **Direct invocation** when expected interaction depth is 1–2 turns.
- **Delegated subagent** when expected depth is 3+ turns and outcome can be summarized.

If uncertain, default to direct invocation.

### FR-5: New Conversation Invocation Contract

For `mcp__codex__codex`, the call payload must contain:

- `prompt`: briefing (required)
- `approval-policy`: resolved value
- `model`: only when user set `-m`
- `sandbox`: resolved value
- `config`: `{ "model_reasoning_effort": "<resolved reasoning>" }`

Rationale: while the upstream tool may apply defaults if these fields are omitted, the client MUST pass resolved execution controls explicitly to enforce least-privilege defaults and deterministic behavior even if upstream defaults change.

No credentials, tokens, or auth file contents may be included.

### FR-6: Follow-Up Invocation Contract

For `mcp__codex__codex-reply`, payload must contain:

- `prompt` follow-up enriched with new context since last turn
- at least one continuity identifier:
  - `threadId` (canonical)
  - `conversationId` (deprecated compatibility alias)

Normalization and deterministic validation:

1. Normalize `threadId` and `conversationId` by trimming outer whitespace; treat empty strings as absent.
2. If both are absent, return:
   - code: `MISSING_REQUIRED_FIELD`
   - message format: `"validation failed: missing conversation identifier. Got: {input!r:.100}"`
3. If both are present and values are unequal, return:
   - code: `INVALID_ARGUMENT`
   - message format: `"validation failed: threadId and conversationId mismatch. Got: {input!r:.100}"`
4. If `threadId` is present, use it as canonical continuity identifier.
5. Else map `conversationId` to canonical `threadId` before upstream dispatch.

If normalized `threadId` is invalid/expired upstream, start a new conversation and rebuild full briefing.

### FR-7: Response Relay Contract

Primary agent relay must include:

1. Codex recommendation summary.
2. Primary-agent assessment:
   - where it agrees/disagrees
   - what changes in plan (or not)
3. Concrete next actions.

Disallowed: blind copy/paste without analysis.

Continuity output contract:

- `structuredContent.threadId` is canonical continuity state.
- `content` is compatibility output only.

### FR-8: Authentication Behavior

The workflow must support both:

1. Interactive login (`codex login`) with locally cached credentials.
2. API key login (`OPENAI_API_KEY`; optional `codex login --with-api-key` persistence).

The skill logic must treat auth as infrastructure state, not prompt content.

### FR-9: Token-Safety Rules

Hard requirements:

1. Never read or parse `auth.json` during normal consultation flow.
2. Never include `id_token`, `access_token`, `refresh_token`, `account_id` in prompts or logs.
3. Never echo auth headers or bearer tokens in user-visible output.
4. If secret-like text is detected in intended briefing material, redact or omit.

Redaction marker:

```
[REDACTED: sensitive credential material]
```

### FR-10: Deterministic Failure Handling

All failures must be actionable and structured:

- parse failure
- tool invocation failure
- timeout
- invalid/expired thread
- auth unavailable
- policy mismatch (e.g., disallowed sandbox)

Message format:

```
"{operation} failed: {reason}. Got: {input!r:.100}"
```

### FR-11: Observability Hooks

Capture non-secret diagnostics per consultation:

- timestamp
- chosen strategy
- resolved flags/defaults
- whether new or continued conversation
- threadId presence (boolean and/or opaque id suffix only)
- tool call success/failure
- error class

Do not log prompt bodies by default unless explicit debug mode is enabled.

### FR-12: Decision-Locked Governance

The implementation must enforce these resolved decisions:

1. Prompt/log retention is debug-gated opt-in only.
2. Redaction failures are fail-closed.
3. Dangerous mode never auto-escalates.
4. Strategy default is direct invocation when uncertain.
5. Reply continuity is `threadId` canonical with `conversationId` as compatibility alias.

---

## 7) Non-Functional Requirements

### NFR-1: Security

No credential leakage in prompts, logs, or user output.

### NFR-2: Determinism

Given identical input flags/context and tool responses, output decisions and payload shapes must be identical.

### NFR-3: Explainability

User-facing relay must clearly separate Codex opinion from primary-agent judgment.

### NFR-4: Graceful Degradation

If Codex server unavailable, workflow returns fallback guidance (what failed + next best step), not silent failure.

### NFR-5: Performance

Prompt assembly should be linear in briefing input size. Avoid expensive whole-repo inlining by default.

---

## 8) Data Contracts

### 8.1 Internal Parsed Input

```ts
type ParsedCodexCommand = {
  model?: string;
  sandbox: "read-only" | "workspace-write" | "danger-full-access";
  approvalPolicy: "untrusted" | "on-failure" | "on-request" | "never";
  reasoningEffort: "minimal" | "low" | "medium" | "high" | "xhigh";
  prompt: string;
};
```

### 8.2 Tool Payload (New)

```ts
type CodexNewCall = {
  prompt: string;
  sandbox: "read-only" | "workspace-write" | "danger-full-access";
  "approval-policy": "untrusted" | "on-failure" | "on-request" | "never";
  model?: string;
  config: { model_reasoning_effort: "minimal" | "low" | "medium" | "high" | "xhigh" };
};
```

### 8.3 Tool Payload (Reply)

```ts
type CodexReplyCall = {
  prompt: string;
  threadId?: string;
  conversationId?: string;
};
```

### 8.4 Normative MCP Input Schemas (must match server spec exactly)

`codex` input schema:

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

`codex-reply` input schema:

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

Identifier normalization algorithm:

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

## 9) End-to-End Behavior

1. User invokes `/codex ...`.
2. Parse and validate arguments.
3. Resolve defaults.
4. Build briefing.
5. Choose strategy.
6. Invoke `mcp__codex__codex` or `mcp__codex__codex-reply`.
7. Receive Codex output.
8. Produce assessed relay response.
9. Persist/propagate `threadId` for continuity.
10. Emit diagnostics without secrets.

---

## 10) Failure Matrix

| Condition | Detection | Required Behavior |
|---|---|---|
| Invalid flag | parser enum mismatch | Return parse error with allowed values |
| Missing prompt on new call | empty prompt | Ask for specific question/prompt |
| MCP tool unavailable | tool call failure | Return troubleshooting + fallback |
| Thread invalid | reply error indicates unknown thread | Start new call with rebuilt full briefing |
| Timeout | tool timeout | Do not automatically retry (cannot guarantee idempotency). Return actionable message and let the user opt into a retry with a clear warning about possible duplicate threads/messages |
| Auth missing | login/API key unavailable | Return auth remediation steps |
| Secret in material | redaction detector hit | redact and continue, note redaction |

Retry policy:

- No automatic retries for failures where upstream execution is uncertain (e.g., tool timeout, connection drop after dispatch).
- No retry for deterministic validation errors.

---

## 11) Security & Privacy Requirements

1. Credentials are never required as user prompt input.
2. Auth state is delegated to Codex CLI runtime.
3. Any referenced local auth files remain out-of-bounds for normal flow.
4. Secret scanning applies to:
   - API keys
   - bearer tokens
   - OAuth/JWT-like strings
   - auth.json token fields
5. Redaction must happen before tool invocation and before user relay.

---

## 12) Testing Requirements

### 12.1 Unit Tests (Must)

1. Argument parsing happy paths:
   - defaults only
   - each flag override
   - mixed ordering
2. Argument parsing failures:
   - unknown flag
   - invalid enum values
   - missing flag values
3. Default mapping:
   - sandbox/approval coupling
4. Briefing assembly:
   - required sections present
   - question section non-empty
5. Redaction:
   - token-like strings are removed
6. Error formatting:
   - exact deterministic template

### 12.2 Integration Tests (Must)

Use mocked MCP tools.

1. New conversation payload shape.
2. Reply payload shape with `threadId`.
3. Reply payload shape with `conversationId`-only compatibility request.
4. Mismatched `threadId` and `conversationId` is deterministically rejected with `INVALID_ARGUMENT`.
5. Invalid normalized `threadId` fallback to new conversation.
6. Timeout does not trigger an automatic retry.
7. Relay contains assessment + next actions.

### 12.3 End-to-End Manual Validation (Should)

1. `/codex review this plan` (default args).
2. `/codex -s workspace-write -a on-failure ...`.
3. `/codex -t xhigh ...`.
4. Follow-up with same `threadId`.
5. Follow-up with `conversationId` only (normalized path).
6. Auth missing scenario (logged out state).

---

## 13) Acceptance Criteria

Implementation is done when all are true:

1. All FR-1 through FR-12 pass.
2. All required unit + integration tests pass.
3. No secret leakage in logs/prompts/user responses across test suite.
4. Strategy choice and defaults are deterministic.
5. `threadId` continuation works, `conversationId` alias normalizes correctly, and mismatches reject deterministically.
6. User relay includes explicit primary-agent assessment, not only Codex output.

---

## 14) Rollout Plan

### Phase 1: Core correctness

- Implement parser/defaults/payload contracts.
- Implement briefing builder.
- Implement deterministic error wrapper.

### Phase 2: Reliability and safety

- Add timeout handling + retry guidance (no unsafe automatic retries).
- Add redaction + secret scanning.
- Add diagnostics hooks.

### Phase 3: UX quality

- Improve relay quality rubric.
- Add regression tests from real consultation transcripts.

---

## 15) Resolved Decisions

1. Prompt/log retention is debug-gated opt-in only.
2. Redaction failures are fail-closed.
3. Dangerous mode never auto-escalates.
4. Strategy default is direct invocation when uncertain.
5. Reply continuity is `threadId` canonical with `conversationId` as compatibility alias.

---

## 16) Recommended Implementation Order

1. Build parser + defaults + validation.
2. Build briefing assembler.
3. Build invocation wrappers for new/reply.
4. Build relay assessment formatter.
5. Add failure matrix handling.
6. Add secret redaction.
7. Add full test suite.

---

## 17) Appendix: Example Valid New Call Payload

```json
{
  "prompt": "## Context\nNeed review of auth middleware approach...\n\n## Material\n- /repo/src/auth/middleware.ts\n\n## Question\nWhat design changes reduce race conditions?",
  "sandbox": "read-only",
  "approval-policy": "never",
  "config": {
    "model_reasoning_effort": "high"
  }
}
```

## 18) Appendix: Example Valid Reply Payload

```json
{
  "threadId": "thread_abc123",
  "prompt": "New benchmark results attached. Re-evaluate your recommendation given this evidence."
}
```

## 19) Appendix: Example Compatibility Reply Payload

```json
{
  "conversationId": "thread_abc123",
  "prompt": "Continue using compatibility identifier only, then normalize to canonical threadId."
}
```
