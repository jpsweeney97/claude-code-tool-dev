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

### Pre-dispatch gate and credential safety (required)

Run this gate immediately before every outbound Codex call (`mcp__codex__codex` or `mcp__codex__codex-reply`).

Create an internal pre-dispatch record with these fields:
- `parse_status`: `pass` | `fail`
- `prompt_status`: `pass` | `fail` | `not_required`
- `strategy_status`: `pass` | `fail`
- `continuity_status`: `pass` | `fail` | `not_required`
- `controls_status`: `pass` | `fail`
- `credential_rules_status`: `pass` | `fail`
- `sanitizer_status`: `pass_clean` | `pass_redacted` | `fail_not_run` | `fail_unresolved_match`

Do not proceed until all required fields are pass-equivalent (`pass`, `pass_clean`, `pass_redacted`, `not_required`).

Credential rules (non-negotiable):
1. Never read or parse `auth.json` during consultation flow.
2. Never include raw credential material in outbound text: `id_token`, `access_token`, `refresh_token`, `account_id`, bearer tokens, API keys (`sk-...`), or equivalent secrets.

Sanitizer rule:
1. Scan all outbound payload text (`prompt`, follow-up text, outbound diagnostics metadata) for secret candidates, including:
   - API keys matching `sk-...`
   - AWS access keys beginning with `AKIA`
   - `Bearer ...` tokens
   - PEM private key blocks
   - fields/assignments containing `password`, `secret`, `token`, `api_key`, `id_token`, `access_token`, `refresh_token`, `account_id`
   - base64-like strings (length >= 40) adjacent to auth-related variable names
2. Replace every detected candidate with `[REDACTED: credential material]`.
3. If any candidate cannot be confidently classified as safe, redact it.
4. Set `sanitizer_status` to:
   - `pass_clean` if none found
   - `pass_redacted` if found and redacted
   - `fail_unresolved_match` if any unresolved candidate remains
   - `fail_not_run` if scan did not run

If another agent profile defines additional secret patterns, treat those patterns as additive, not alternative.

On any gate failure, return:
`pre-dispatch gate failed: {reason}. Got: {input!r:.100}`

Allowed reasons:
- `argument parse invalid`
- `missing prompt for new conversation`
- `invocation strategy not selected`
- `missing conversation identifier`
- `threadId and conversationId mismatch`
- `resolved execution controls incomplete`
- `credential rule violation`
- `sanitizer not run`
- `unresolved secret candidate in outbound payload`

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

Present Codex output and your independent judgment using this required 3-part contract.

1. **Codex Position**
   - Summarize Codex's answer in 1-3 bullets.
   - If Codex reports uncertainty or requests more context, state that explicitly.

2. **Claude Assessment**
   - State `agree`, `partially agree`, or `disagree`, and give the reason.
   - Name at least one risk, trade-off, or assumption.

3. **Decision and Next Action**
   - Choose one disposition:
     - Recommendation dispositions: `adopt`, `adopt-with-changes`, `defer`, `reject`
     - Informational dispositions: `incorporate`, `note`, `no-change`
   - State one concrete next action. If no action is needed, state `no change` explicitly.

If Codex requests more context or cannot conclude:
- Keep all 3 sections.
- Use `defer` or `note`.
- Request the specific missing artifacts.
- State whether to re-invoke Codex after those artifacts are provided.

Completion criteria:
- All 3 sections are present.
- Disposition is explicit.
- Next action is observable.
- Do not relay Codex output verbatim as the final response.

After relaying, capture diagnostics for this consultation (see [Diagnostics](#diagnostics) section below — timestamp, strategy, flags, success/failure).

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
