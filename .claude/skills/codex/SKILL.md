---
name: codex
description: Consult OpenAI Codex for second opinions on architecture, debugging, code review, plans, and decisions.
argument-hint: "[-m <model>] [-s {read-only|workspace-write|danger-full-access}] [-a {untrusted|on-failure|on-request|never}] [-t {minimal|low|medium|high|xhigh}] [PROMPT]"
user-invocable: true
allowed-tools: mcp__codex__codex, mcp__codex__codex-reply
---

# Codex Consultation Protocol

Consult OpenAI Codex via its MCP server for second opinions. Claude remains the primary agent — Codex is a consultant.

**Auto-invocation rule:** Only invoke when the user explicitly requests a second opinion or Codex consultation. Do not call Codex proactively — wait for user intent.

## Scope Boundaries

In scope:
1. Invoke Codex only when the user explicitly requests Codex or a second opinion.
2. Use Codex as an advisory consultant for architecture, debugging, review, planning, and decision support.
3. Continue prior Codex conversations only with a valid continuity identifier.

Out of scope (non-exhaustive):
1. Proactive Codex invocation without explicit user intent.
2. Treating Codex output as authoritative without Claude's independent assessment.
3. Sending any outbound payload that fails required sanitizer/redaction checks.
4. Consultations that depend on live runtime state that cannot be represented in briefing artifacts.

Default on ambiguity: Do not invoke Codex until scope is clear. Ask one clarifying question.

## Operational Definitions

- **fail-closed:** If a required check cannot be completed with a passing result, block the Codex call and return an error.
- **debug-gated:** Include prompt/response retention or expanded logging only when debug mode is explicitly enabled for the current consultation; otherwise keep it off.
- **egress sanitization:** Run sanitizer/redaction checks on every outbound Codex payload (`prompt`, follow-up text, and outbound diagnostics metadata) before dispatch.

Two MCP tools available:
- `mcp__codex__codex` — start a new conversation
- `mcp__codex__codex-reply` — continue an existing conversation

## Setup (required)

This skill assumes Claude Code can see an MCP server named `codex` that runs the Codex CLI MCP server (`codex mcp-server`).

**Project scope (recommended):** this repo includes a `.mcp.json` at the project root that registers:

```json
{
  "mcpServers": {
    "codex": {
      "type": "stdio",
      "command": "codex",
      "args": ["mcp-server"]
    }
  }
}
```

**macOS stability note:** some spawn environments may start `codex mcp-server` without the full user environment. If the Codex CLI panics at startup (for example, `Attempted to create a NULL object.`), ensure the MCP server process receives `CODEX_SANDBOX=seatbelt`. This repo’s `.mcp.json` sets `CODEX_SANDBOX` by default.

**Auth prerequisite:** ensure the `codex` CLI is installed and authenticated (interactive `codex login` or `OPENAI_API_KEY`). Never paste tokens into prompts or logs.

## Arguments

Parse optional flags from `$ARGUMENTS` — the raw text following `/codex` in the user's command (e.g., for `/codex -t high review this PR`, `$ARGUMENTS` is `-t high review this PR`). Remaining text after extracting flags = PROMPT.

| Flag | MCP Parameter | Default |
|------|---------------|---------|
| `-m <model>` | `model` | Codex's default model |
| `-s {read-only\|workspace-write\|danger-full-access}` | `sandbox` | `read-only` |
| `-a {untrusted\|on-failure\|on-request\|never}` | `approval-policy` | `never` if read-only, `on-failure` if workspace-write or danger-full-access |
| `-t {minimal\|low\|medium\|high\|xhigh}` | `config` → `{"model_reasoning_effort": "<value>"}` | `xhigh` |

Flag values are case-insensitive: `high`, `HIGH`, and `High` are all accepted for `-t` and other enum flags.

Only `prompt` is required by the MCP tool schema for `mcp__codex__codex`. For deterministic, least-privilege behavior, always pass resolved execution controls (`sandbox`, `approval-policy`, and `config.model_reasoning_effort`) rather than relying on upstream defaults. Only include `model` when overriding Codex's default model. If the user explicitly sets `-a`, that value always overrides the sandbox-coupled default.

Examples:
- `/codex review the plan in docs/plans/auth-redesign.md` → all defaults, PROMPT = "review the plan..."
- `/codex -t xhigh why is the auth middleware failing?` → reasoning xhigh, rest defaults
- `/codex -s workspace-write fix the flaky test in auth.test.ts` → workspace-write sandbox, approval on-failure

### Argument validation (deterministic)

Validation behavior:
1. Reject unknown flags.
2. Reject missing values after flags that require values.
3. Reject invalid enum values.
4. Preserve all remaining text after flags as prompt, including punctuation.
5. Trim outer whitespace from prompt.

Error format:
`argument parsing failed: {reason}. Got: {input!r:.100}`

## Step 1: Build Context Briefing

Briefing structure is defined in `docs/references/consultation-contract.md` § Briefing Contract (§5). This file is not normative for briefing format.

Before building a briefing:
1. Read and apply the Briefing Contract (§5) in full.
2. Include all 3 required sections: `## Context`, `## Material`, `## Question`.
3. If the Briefing Contract cannot be read, build a minimal briefing with `## Context` (task and why) and `## Question` (specific ask); include `## Material: (none)` if no material applies.

## Step 2: Choose Invocation Strategy

**Direct invocation** (default):
- Quick consultations (1-2 expected turns)
- Codex's response will immediately inform your next action
- Conversation context matters for interpreting the response

**Subagent delegation** (for extended sessions):
- 3+ expected turns of back-and-forth
- Topic is self-contained — main conversation context isn't needed turn-by-turn
- A summary of the outcome is sufficient

If uncertain whether to use direct or delegated, default to direct invocation.

For subagent delegation:
1. Spawn a `codex-dialogue` subagent (purpose-built for multi-turn Codex conversations)
2. Pass the enriched briefing, goal, and optionally a posture (adversarial, collaborative, exploratory, evaluative) and turn budget
3. The subagent manages the conversation, detects convergence, and returns a synthesis + the Codex `threadId`
4. To continue later, resume the subagent via its `agentId` (preserves richer context than raw `threadId`)

**Delegation example:**

User asks: `/codex I need a deep review of our caching strategy — challenge my assumptions`

This likely needs 3+ adversarial turns — delegate to codex-dialogue:

```
Task(
  subagent_type: "codex-dialogue",
  prompt: """
    Goal: Challenge the caching strategy assumptions.
    Posture: adversarial
    Budget: 5

    ## Context
    [Current caching approach, decisions made, trade-offs considered]

    ## Material
    [Key cache implementation files, config, performance data]

    ## Question
    What are the weakest assumptions in this caching strategy?
  """
)
```

The subagent returns a confidence-annotated synthesis with convergence points, divergence points, and the Codex `threadId`. Present this synthesis to the user with your own assessment.

## Step 3: Invoke Codex

Authentication is handled by the Codex CLI from cached login state.

### Pre-dispatch gate and credential safety (Normative Contract)

Safety rules are defined in `docs/references/consultation-contract.md` § Safety Pipeline (§7). This file is not normative for credential patterns.

Before any outbound Codex dispatch:
1. Read and apply the Safety Pipeline (§7) in full.
2. Run sanitizer/redaction on every outbound payload.
3. If the Safety Pipeline cannot be read or applied, block dispatch and return: `pre-dispatch gate failed: contract unavailable. Got: {input!r:.100}`.

### New conversation

Call `mcp__codex__codex` with parameters from `docs/references/consultation-contract.md` § Codex Transport Adapter (§9) and § Policy Resolver Contract (§8). Always pass resolved `sandbox`, `approval-policy`, and `config` — do not rely on upstream defaults.

### Continue conversation

Call `mcp__codex__codex-reply` per `docs/references/consultation-contract.md` § Codex Transport Adapter (§9). Apply `threadId` canonicalization from § Continuity State Contract (§10) before dispatch.

### Continuity state

Persist `threadId` per `docs/references/consultation-contract.md` § Continuity State Contract (§10).
- Prefer `structuredContent.threadId`. Fall back to top-level `threadId`.
- If `threadId` is invalid or expired upstream, start a new conversation with a rebuilt full briefing.

## Step 4: Relay Response

Relay obligations are defined in `docs/references/consultation-contract.md` § Relay Assessment Contract (§11). This file is not normative for relay format.

After every Codex response:
1. Read and apply the Relay Assessment Contract (§11) in full.
2. Present output using the required 3-part structure: Codex Position, Claude Assessment, Decision and Next Action.
3. If the Relay Assessment Contract cannot be read, present Codex output with your own assessment in free form — do not relay verbatim.

After relaying, capture diagnostics for this consultation (see [Diagnostics](#diagnostics) section — timestamp, strategy, flags, success/failure).

## Failure Handling

All failure messages use this format:
`"{operation} failed: {reason}. Got: {input!r:.100}"`

| Condition | Detection | Required Behavior |
|---|---|---|
| Invalid flag | Parser enum mismatch | Return parse error with allowed values |
| Missing prompt | Empty prompt on new call | Ask the user for a specific question |
| MCP tool unavailable | Tool call failure | Return troubleshooting steps + fallback guidance |
| Thread invalid/expired | Reply error from upstream | Start new `codex` call with rebuilt full briefing |
| Timeout | Tool timeout | Do not auto-retry. Report that upstream may have processed the request; retrying could create duplicates. Prompt the user to confirm before retrying |
| Auth missing | Login/API key unavailable | Return auth remediation steps (see Troubleshooting) |
| Pre-dispatch gate failure | `controls_status`, `sanitizer_status`, or any field not pass-equivalent | Return `pre-dispatch gate failed: {reason}`. Do not dispatch. |
| Secret in briefing material | `sanitizer_status=fail_unresolved_match` | Redact with `[REDACTED: credential material]`; set `sanitizer_status=pass_redacted`; note redaction to user |
| Policy mismatch | `controls_status=fail` — disallowed sandbox or approval combination | Return error with allowed values; do not dispatch |

Retry policy:
- No automatic retries for failures where upstream execution is uncertain (timeout, connection drop after dispatch).
- No retries for deterministic validation errors.

## Diagnostics

After each Codex consultation, capture these non-secret diagnostics:
- Timestamp
- Strategy chosen (direct or delegated)
- Resolved flags and defaults
- New or continued conversation
- `threadId` present (boolean only — do not log the full ID in conversation output; full IDs are permitted in audit artifacts for traceability)
- Tool call success or failure
- Error code (if any)

Do not log prompt bodies or Codex response text by default. Prompt/log retention is debug-gated opt-in only.

## Governance (Decision-Locked)

These rules are non-negotiable:
1. **Prompt/log retention:** debug-gated opt-in only. Never log prompts or responses by default.
2. **Redaction failures are fail-closed:** if redaction cannot be confirmed, do not send the briefing. Err on the side of blocking.
3. **Dangerous mode never auto-escalates:** never upgrade sandbox from `read-only` to `workspace-write` or `danger-full-access` without explicit user flag (`-s`).
4. **Strategy default:** when uncertain, use direct invocation.
5. **Reply continuity:** `threadId` is canonical; `conversationId` is a deprecated compatibility alias.
6. **Egress sanitization:** no outbound payload to Codex (briefing, follow-up, diagnostics) without a sanitizer pass. The pre-dispatch gate (§ Step 3) enforces this — `sanitizer_status` must be `pass_clean` or `pass_redacted` before dispatch. The context injection server's redaction pipeline is a complementary layer; both apply to their respective data paths.
7. **Consent required for scope expansion:** any scope change after initial preflight requires explicit re-consent.

## Troubleshooting

### MCP server not available
Codex MCP server must be configured in settings and `codex` CLI installed (`npm install -g @openai/codex`).

Authentication can use either method:
- **Interactive login (recommended):** run `codex login` once and complete the auth flow. Credentials are cached locally and reused across sessions until logout, expiry, or revocation.
- **API key login:** set `OPENAI_API_KEY` in the environment, then optionally persist via `printenv OPENAI_API_KEY | codex login --with-api-key`.

### Codex response seems off-base
The briefing was likely insufficient. Re-invoke with more context — include specific file contents, error messages, or conversation history that was omitted.

### Thread lost
If a `threadId` is no longer valid, start a new conversation. Re-enrich the prompt with full context.
