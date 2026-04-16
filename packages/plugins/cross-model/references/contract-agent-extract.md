<!-- extract-hash: 1bb426ca1305 -->
# Consultation Contract — Agent Extract

Extracted from [consultation-contract.md](consultation-contract.md) for use by the `codex-dialogue` agent. Contains only the sections the agent needs at runtime: §4 (vocabulary), §5 (briefing), §7 (safety), §8 (policy), §9 (transport), §10 (continuity), §15 (governance).

For the full contract including §1-3 (meta/preflight), §6 (delegation), §11 (relay), §12-14 (error/event/profile), §16-17 (conformance/learning), see the full contract.

---

## 4. Shared Vocabulary

| Term | Definition |
|------|-----------|
| `briefing` | The assembled prompt: `## Context`, `## Material`, `## Question` |
| `threadId` | Canonical Codex conversation identifier (source of truth for continuity) |
| `conversationId` | Deprecated alias for `threadId` — map to `threadId` before dispatch |
| `controls` | Resolved execution controls: `sandbox`, `approval-policy`, `config` |
| `sanitizer_status` | Pass/fail result of the outbound credential scan |
| `consultation` | One interaction with Codex: preflight → briefing → dispatch → relay |

---

## 5. Briefing Contract (Normative)

Every Codex consultation MUST use this 3-section structure:

```
## Context
[Topic and background. What we're working on and why.]

## Material
[Relevant content — code, plans, docs, decisions. Inline when concise; summarize when large.]

## Question
[Clear framing of what we want Codex's input on.]
```

**Rules:**
1. Always include all 3 sections exactly once per briefing.
2. If no material applies, include `## Material` with `- (none)`.
3. Calibrate depth to the question: simple questions need a paragraph; debugging sessions need file contents, error output, and failed approaches.
4. Do not inline entire repositories or large file trees — summarize or reference paths.
5. Briefing assembly MUST be linear in input size — no recursive expansion.

**Pre-assembled briefing (sentinel carve-out):**

When a briefing contains `<!-- dialogue-orchestrated-briefing -->` before `## Context`, the assembling skill has already applied §5 formatting and verified conformance. The consumer MUST:
1. Use the briefing **verbatim** as the `prompt` for the initial Codex call.
2. Do NOT rewrite, summarize, restructure, or re-apply §5 formatting.
3. Do NOT re-derive `## Context`, `## Material`, or `## Question` — they are already present and populated.

The sentinel certifies §5 conformance. Re-assembly discards structured metadata (provenance tags, assumption IDs, citation formats) that downstream pipeline stages depend on.

---

## 7. Safety Pipeline (Normative)

Run this pipeline immediately before every outbound Codex call (`mcp__plugin_cross-model_codex__codex` or `mcp__plugin_cross-model_codex__codex-reply`). This section is normative — skill and agent stubs must defer to it.

### Pre-dispatch record

Create an internal record with these fields:

| Field | Values |
|-------|--------|
| `parse_status` | `pass` \| `fail` |
| `prompt_status` | `pass` \| `fail` \| `not_required` |
| `strategy_status` | `pass` \| `fail` |
| `continuity_status` | `pass` \| `fail` \| `not_required` |
| `controls_status` | `pass` \| `fail` |
| `credential_rules_status` | `pass` \| `fail` |
| `sanitizer_status` | `pass_clean` \| `pass_redacted` \| `fail_not_run` \| `fail_unresolved_match` |

Do not proceed until all required fields are pass-equivalent (`pass`, `pass_clean`, `pass_redacted`, `not_required`).

### Credential rules (non-negotiable)

1. Never read or parse `auth.json` during consultation flow.
2. Never include raw credential material in outbound text: `id_token`, `access_token`, `refresh_token`, `account_id`, bearer tokens, API keys (`sk-...`), or equivalent secrets.

### Sanitizer rules

Scan all outbound payload text (`prompt`, follow-up text, outbound diagnostics metadata) for secret candidates:
- API keys matching `sk-...`
- AWS access keys beginning with `AKIA`
- `Bearer ...` tokens
- PEM private key blocks
- Fields/assignments containing `password`, `secret`, `token`, `api_key`, `id_token`, `access_token`, `refresh_token`, `account_id`
- Base64-like strings (length >= 40) adjacent to auth-related variable names

No credential-bearing payload may be dispatched. Candidates must be redacted with `[REDACTED: credential material]` before dispatch, or the dispatch must be blocked. If any candidate cannot be confidently classified as safe, block or redact — over-redaction is always preferable to dispatch.

Set `sanitizer_status`:
- `pass_clean` — none found
- `pass_redacted` — found and redacted
- `fail_unresolved_match` — any unresolved candidate remains
- `fail_not_run` — scan did not run

Additional secret patterns from caller profiles are additive, not alternative.

### Gate failure

On any gate failure: `pre-dispatch gate failed: {reason}. Got: {input!r:.100}`

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

---

## 8. Policy Resolver Contract

Resolve execution controls before dispatch:

| Control | Default |
|---------|---------|
| `sandbox` | `read-only` |
| `approval-policy` | `never` if `read-only`; `on-request` if `workspace-write` or `danger-full-access` |
| `model_reasoning_effort` | `high` |

**Delegated precedence:** When the delegation envelope includes `reasoning_effort`, the agent uses it directly — no re-resolution of profile files. The delegating skill is responsible for resolution order. The agent's §8 resolver is the fallback when the delegation envelope omits the field.

**Hard rejects (fail-closed):**
- `danger-full-access` combined with `approval-policy=never`: return `policy mismatch: danger-full-access requires explicit approval-policy. Got: never`. Do not dispatch.
- Never upgrade sandbox from `read-only` without explicit user flag (`-s`).

`controls_status` MUST be `pass` before dispatch proceeds.

---

## 9. Codex Transport Adapter

### New conversation (`mcp__plugin_cross-model_codex__codex`)

| Parameter | Value |
|-----------|-------|
| `prompt` | Assembled briefing from §5 |
| `model` | Do NOT set this parameter unless `-m` was explicitly provided. Omit entirely — the Codex server selects the correct model. Never guess model names from training knowledge. |
| `sandbox` | Resolved from §8 |
| `approval-policy` | Resolved from §8 |
| `config` | `{"model_reasoning_effort": "<resolved value>"}` |

Always pass resolved `sandbox`, `approval-policy`, and `config` — do not rely on upstream defaults. Do NOT include `model` unless the user explicitly passed `-m <model>`. Omitting `model` lets the Codex server select its default — this is the correct behavior. Setting `model` to values from training knowledge (e.g., "o3", "o4 mini") causes API failures.

### Continue conversation (`mcp__plugin_cross-model_codex__codex-reply`)

| Parameter | Value |
|-----------|-------|
| `prompt` | Follow-up message |
| `threadId` or `conversationId` | Canonical identifier from §10 |

---

## 10. Continuity State Contract

### threadId canonicalization

1. Normalize: trim outer whitespace; treat empty strings as absent.
2. If both `threadId` and `conversationId` absent: `validation failed: missing conversation identifier. Got: {input!r:.100}` (code: `MISSING_REQUIRED_FIELD`)
3. If both present and unequal: `validation failed: threadId and conversationId mismatch. Got: {input!r:.100}` (code: `INVALID_ARGUMENT`)
4. If `threadId` present: use it as canonical identifier.
5. Else: map `conversationId` to `threadId` before dispatch.

### Thread persistence

After a successful Codex call:
- Prefer `structuredContent.threadId` (primary source).
- Fall back to top-level `threadId` field (when present).
- Treat `content` as compatibility output only.
- If `threadId` is invalid or expired upstream: start a new conversation with a rebuilt full briefing.

### Resume capsule (scope breach)

On scope breach during a delegated consultation, return:

| Field | Description |
|-------|-------------|
| `threadId` | Current thread identifier |
| `current_turn` | Turn count at breach |
| `checkpoint_id` | From last successful `process_turn` |
| `state_checkpoint` | From last successful `process_turn` |
| `ledger_summary` | Compact trajectory summary |
| `consent_state` | Classes and roots consented at consultation start |

---

## 15. Governance Locks

These rules are non-negotiable. Implementors must not override them:

1. **Prompt/log retention:** debug-gated opt-in only. Never log prompts or responses by default.
2. **Redaction failures are fail-closed:** if redaction cannot be confirmed, block dispatch. Over-redact rather than under-redact.
3. **No auto-escalation:** never upgrade sandbox from `read-only` without explicit user flag (`-s`).
4. **Strategy default:** when uncertain, use direct invocation (single-turn).
5. **Reply continuity:** `threadId` is canonical; `conversationId` is a deprecated compatibility alias — map to `threadId` before dispatch.
6. **Egress sanitization:** no outbound payload to Codex without a sanitizer pass. `sanitizer_status` must be `pass_clean` or `pass_redacted`.
7. **Consent required for scope expansion:** any scope change after initial preflight requires explicit re-consent.
