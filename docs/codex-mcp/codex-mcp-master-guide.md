# Codex MCP Master Guide (Clueless → Expert)

**Last updated:** 2026-02-10  
**Purpose:** One consolidated document for understanding, integrating, building, operating, and mastering Codex MCP in this repository.

---

## 1) What This Master Guide Gives You

If you follow this document end to end, you should be able to:

1. Explain Codex MCP architecture clearly.
2. Run `codex mcp-server` and validate `codex`/`codex-reply`.
3. Build against both implementation specs in this repo:
   - `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`
   - `docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
4. Apply secure defaults and avoid common failure patterns.
5. Operate the system with runbook-level reliability.

---

## 2) Fast Mental Model

There are two different command families:

| Command | Role | Typical Use |
|---|---|---|
| `codex mcp-server` | Codex acts as **MCP server** | Expose Codex tools to an MCP client |
| `codex mcp ...` | Codex acts as **MCP client manager** | Add/list/login to external MCP servers Codex can call |

Tool semantics:

- `codex` = start new consultation thread
- `codex-reply` = continue existing thread using a conversation identifier (`threadId` canonical; `conversationId` deprecated alias)

---

## 3) Core Concepts You Must Know

### MCP transport

- `codex mcp-server` uses stdio for MCP JSON-RPC transport.
- Client and server lifecycle are coupled to process/stdin state.

### `threadId` continuity

- Multi-turn quality depends on preserving and reusing `threadId`.
- If `threadId` is invalid/lost, start new `codex` call with full context.

### Runtime controls

- Sandbox: `read-only`, `workspace-write`, `danger-full-access`
- Approval policy: `untrusted`, `on-failure`, `on-request`, `never`
- Reasoning effort: `minimal`, `low`, `medium`, `high`, `xhigh`

### Auth modes

- Interactive login (`codex login`)
- API key (`OPENAI_API_KEY`, optional `codex login --with-api-key`)

---

<a id="canonical-quickstart"></a>
## 4) 30-Minute First Success

Two common ways to run this flow:

1. **Inspector-driven (recommended):** the inspector spawns `codex mcp-server` as a child process (no separate terminal needed).
2. **Client integration (advanced):** configure your own MCP client to spawn `codex mcp-server` and communicate over stdio (there is no network port by default).

### Step 1 — Verify install and auth

```bash
codex --version
codex mcp-server --help
codex login status
```

If needed:

```bash
codex login
```

### Step 2 — Inspect tools (recommended)

Use the pinned inspector command in the [Canonical Command Reference](#canonical-command-reference).

That command starts `codex mcp-server` for you. Do not run `codex mcp-server` separately for the inspector flow.

Expected tools:

- `codex`
- `codex-reply`

### Step 3 — First request

Minimum payload:

```json
{
  "prompt": "Give me a pragmatic architecture review checklist for a Python API."
}
```

Recommended (explicit execution controls for least privilege + deterministic behavior):

```json
{
  "prompt": "Give me a pragmatic architecture review checklist for a Python API.",
  "sandbox": "read-only",
  "approval-policy": "never",
  "config": { "model_reasoning_effort": "high" }
}
```

Save the returned `threadId`.

### Step 4 — Follow-up request

```json
{
  "threadId": "<thread-from-previous-call>",
  "prompt": "Now prioritize only high-risk migration issues."
}
```

### Step 5 — Run server standalone (debugging only)

You can run the server directly to observe startup behavior, but because transport is stdio, a client normally spawns the server process. Do not expect to “attach” from another terminal like you would with an HTTP server.

```bash
codex mcp-server
```

---

## 5) Canonical Tool Contracts (Build-Time Baseline)

## `codex` (new thread)

Required:

- `prompt`

Optional:

- `approval-policy`
- `base-instructions`
- `config` (open object; commonly includes `model_reasoning_effort`)
- `cwd`
- `include-plan-tool`
- `model`
- `profile`
- `sandbox`

Recommended defaults:

- sandbox: `read-only`
- approval: `never` for read-only
- approval: `on-failure` for write/full-access modes
- reasoning: `high`

Note: while these fields are optional in the tool schema, this repository’s consultation integration passes `sandbox`, `approval-policy`, and `config.model_reasoning_effort` explicitly to enforce least privilege and deterministic behavior.

## `codex-reply` (existing thread)

Required:

- `prompt`

Identifier requirement:

- `threadId` (canonical)
- `conversationId` (deprecated compatibility alias)

Normalization behavior:

- If only `conversationId` is provided, map it to canonical `threadId`.
- If both are provided and unequal, reject with deterministic `INVALID_ARGUMENT`.

---

## 6) Build Blueprint for the Two Specs

This section is the implementation roadmap for:

- `docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
- `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`

### Build Order (recommended)

1. Build MCP server layer first.
2. Build client/skill integration second.
3. Validate end-to-end behavior and acceptance criteria.

### Phase A — MCP server implementation

Implement first:

1. Tool registration (`codex`, `codex-reply`)
2. Input validation and default resolution
3. Execution adapter
4. Stable success/error envelopes
5. Error taxonomy mapping
6. Timeout/retry policy
7. Security guards and redaction
8. Observability fields and metrics

Definition of done:

- Conformance, integration, and security tests pass.
- Error codes are deterministic and documented.

### Phase B — Client/skill implementation

Implement next:

1. `/codex` argument parsing and validation
2. Briefing assembly (`## Context`, `## Material`, `## Question`)
3. Strategy selection (direct vs delegated)
4. New/reply invocation wrappers
5. Assessed relay response format
6. Failure handling matrix implementation
7. Secret-safe diagnostics

Definition of done:

- FR/NFR and acceptance criteria in client spec pass.
- Follow-up continuity and fallback behavior validated.

### Phase C — End-to-end hardening

1. Verify server + client defaults align.
2. Verify thread continuity across retries/restarts.
3. Verify no secret leakage in logs/prompts/errors.
4. Validate with manual scenarios + synthetic checks.

---

## 7) Briefing Quality Standards (Critical for Result Quality)

Use this template for new `codex` calls:

```markdown
## Context
[Goal, constraints, state]

## Material
[Relevant code paths/errors/attempts]

## Question
[One specific, answerable ask]
```

For `codex-reply`:

1. Add only new evidence.
2. Reference previous recommendation briefly.
3. Ask one refinement question.

Avoid:

- vague asks (“thoughts?”)
- unstructured dumps
- multi-topic follow-ups in one turn

---

## 8) Security Baseline (Non-Negotiable)

1. Default to least privilege (`read-only`).
2. Never pass secrets/tokens through tool args.
3. Never log raw auth/token material.
4. Redact sensitive payloads before logging/display.
5. Treat `danger-full-access` as break-glass only.

Sensitive material to redact:

- `id_token`
- `access_token`
- `refresh_token`
- bearer headers
- API key-like values

---

## 9) Operations Baseline (Day-2)

Minimum operational controls:

1. Startup checks (`codex --version`, `codex login status`, tool discovery).
2. Functional health checks (`codex` and `codex-reply` path).
3. Timeout and retry policy with clear limits.
4. Incident playbooks for:
   - auth outage
   - upstream degradation/timeouts
   - thread continuity failure
   - policy misconfiguration
5. Post-incident review process and owners.

Suggested starter SLOs:

- success rate ≥ 99%
- p95 latency ≤ 15s
- timeout rate ≤ 1%

---

## 10) Failure Drills You Should Practice

Run these drills before claiming production readiness:

1. Missing/expired auth
2. Invalid `threadId`
3. Timeout/transient upstream failure
4. Sandbox/policy mismatch
5. Mid-session server interruption

For each drill, capture:

- symptom
- root cause
- recovery action
- verification evidence

---

## 11) Expert Competency Checklist

You are “expert-ready” when you can independently:

1. Explain server-vs-client MCP roles without confusion.
2. Build both specs with deterministic behavior.
3. Handle common failure modes quickly and correctly.
4. Operate with secure defaults and no leakage.
5. Mentor others and improve patterns/runbooks.

---

## 12) Minimal Reading Set (When Time Is Tight)

Read in this exact order:

1. Official docs:
   - Codex MCP Server
   - Codex CLI
   - Codex Config Reference
   - Codex Authentication
2. `docs/codex-mcp/learning-path/01-codex-mcp-concepts.md`
3. `docs/codex-mcp/references/codex-mcp-server-beginner-to-expert.md`
4. `docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
5. `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`
6. `docs/codex-mcp/cookbooks/prompt-briefing-patterns.md`
7. `docs/codex-mcp/learning-path/02-first-success-30-min.md`

---

<a id="canonical-command-reference"></a>
## 13) Consolidated Command Reference

```bash
# Install + verify
npm install -g @openai/codex
codex --version
codex mcp-server --help

# Auth
codex login
codex login status
printenv OPENAI_API_KEY | codex login --with-api-key

# Inspect tools (this spawns `codex mcp-server`)
npx @modelcontextprotocol/inspector@0.20.0 codex mcp-server

# Run Codex as MCP server (debugging only; normally spawned by a client)
codex mcp-server

# Codex as MCP client manager (different workflow)
codex mcp list
codex mcp add myserver --url https://example.com/mcp
codex mcp login myserver
```

---

## 14) Local Doc Map (Single-Source Navigation)

- Learning path: `docs/codex-mcp/learning-path/README.md`
- Beginner→expert reference: `docs/codex-mcp/references/codex-mcp-server-beginner-to-expert.md`
- Server build spec: `docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
- Client/skill spec: `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`
- Integration recipes: `docs/codex-mcp/cookbooks/client-integration-recipes.md`
- Briefing patterns: `docs/codex-mcp/cookbooks/prompt-briefing-patterns.md`
- Operations runbook: `docs/codex-mcp/runbooks/codex-mcp-operations.md`
- Threat model: `docs/codex-mcp/security/codex-mcp-threat-model.md`
- Maturity model: `docs/codex-mcp/assessments/codex-mcp-skill-maturity-model.md`
- FAQ: `docs/codex-mcp/faq/codex-mcp-faq.md`

---

## 15) Official Documentation

- [Codex MCP](https://developers.openai.com/codex/mcp)
- [Codex CLI](https://developers.openai.com/codex/cli)
- [Codex CLI Reference](https://developers.openai.com/codex/cli/reference)
- [Codex Config Reference](https://developers.openai.com/codex/config-reference)
- [Codex Authentication](https://developers.openai.com/codex/auth)
