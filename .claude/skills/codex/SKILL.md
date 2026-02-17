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

Codex has no knowledge of the current session. Before calling it, build a complete briefing from conversation context.

Include:
- **Current task:** What we're working on and why
- **Decisions made:** What's been decided, what trade-offs were considered
- **Relevant material:** Inline key content or reference file paths — Codex in read-only mode can browse files but not write. Inline when concise; reference paths when files are large.
- **What's been tried:** If applicable, what approaches failed and why
- **Specific question:** Frame the consultation as a clear, answerable question

Structure:

```
## Context
[Task, state, and relevant decisions]

## Material
[Inline relevant content — code, plans, docs, error output. Be selective, not exhaustive.]

## Question
[What we want Codex's input on]
```

Always include **all three** top-level sections (`## Context`, `## Material`, `## Question`) exactly once per briefing. If there is no relevant material for a simple question, keep `## Material` but make it explicit:

```
## Material
- (none)
```

**Calibrate depth to the question.** A quick "what do you think of this approach?" needs a paragraph of context. A debugging session needs file contents, error output, and a list of failed approaches. Do not inline entire repositories or large file trees — summarize or reference paths. Briefing assembly should be linear in input size.

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

### Token safety (hard rules)

1. Never read or parse `auth.json` during normal consultation flow.
2. Never include `id_token`, `access_token`, `refresh_token`, `account_id`, bearer tokens, or API keys (`sk-...`) in prompts, tool parameters, logs, or user-visible output.
3. Before sending a briefing, scan for secret-like text. If detected, replace with `[REDACTED: credential material]` and note the redaction to the user.
4. If redaction cannot be confirmed, do not send the briefing (fail-closed).

### New conversation

Call `mcp__codex__codex`:

| Parameter | Value |
|-----------|-------|
| `prompt` | Enriched briefing from Step 1 |
| `model` | From `-m` flag, or omit for Codex default |
| `sandbox` | From `-s` flag, or `read-only` |
| `approval-policy` | From `-a` flag, or `never` (read-only) / `on-failure` (workspace-write) |
| `config` | `{"model_reasoning_effort": "<-t flag or 'xhigh'>"}` |

### Continue conversation

Call `mcp__codex__codex-reply` with:
- `prompt`: follow-up message (enrich with any new context since last turn)
- at least one continuity identifier: `threadId` or `conversationId` (see [Governance](#governance-decision-locked) rule #5)

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

If normalized `threadId` is invalid/expired upstream, start a new conversation and rebuild a full briefing.

### Continuity state

After a successful Codex tool call, persist `threadId` for follow-up turns:
- Prefer `structuredContent.threadId` (primary source).
- Fall back to the top-level `threadId` field (when present).
- Treat `content` as compatibility output only.

## Step 4: Relay Response

Present Codex's response to the user with your own assessment:
- Where you agree or disagree with Codex's take
- How it changes (or doesn't change) the current approach
- Recommended next steps

Do not just parrot Codex's response. Add value as the primary agent.

**After relaying:** Capture diagnostics for this consultation (see [Diagnostics](#diagnostics) section below — timestamp, strategy, flags, success/failure).

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
| Secret in briefing material | Redaction detector hit | Redact with marker and continue; note the redaction to the user |
| Policy mismatch | Disallowed sandbox or approval combination | Return error with allowed values |

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
6. **Egress sanitization:** no outbound payload to Codex (briefing, follow-up, diagnostics) without a sanitizer pass. The agent's token safety rules and the context injection server's redaction pipeline are complementary layers — both apply to their respective data paths. The fail-closed default applies to all paths.

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
