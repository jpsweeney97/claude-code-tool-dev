# Consultation Contract

**Version:** 0.1.0
**Status:** Draft
**Purpose:** Define the normative protocol for Codex consultations — shared by the `/codex` skill and the `codex-dialogue` agent. Both reference this document as the single source of truth for briefing structure, safety rules, transport parameters, continuity logic, and relay obligations.

---

## 1. Purpose, Scope, and Non-Goals

This contract governs interaction between:
- The `/codex` skill (direct-mode consultations)
- The `codex-dialogue` agent (extended multi-turn consultations)
- OpenAI Codex via `mcp__plugin_codex_codex__codex` and `mcp__plugin_codex_codex__codex-reply` MCP tools

**In scope:** Briefing assembly, pre-dispatch safety checks, transport parameters, continuity state, relay output obligations, conformance verification.

**Out of scope:** The context injection protocol (see `context-injection-contract.md`), subagent orchestration, event persistence, profile UX flag parsing, and learning injection.

---

## 2. Normative Terms and Precedence

| Term | Meaning |
|------|---------|
| **MUST** | Required — violation is a contract breach |
| **MUST NOT** | Prohibited — doing this is a contract breach |
| **SHOULD** | Recommended — omit only with documented rationale |
| **fail-closed** | On check failure, block dispatch and return error |
| **debug-gated** | Retain only when debug mode explicitly enabled |
| **normative** | This contract section is authoritative; callers must not define local alternatives |

**Precedence:** This contract takes precedence over inline instructions in skill and agent files for 4 normative sections: Briefing Contract (§5), Safety Pipeline (§7), Continuity State Contract (§10), and Relay Assessment Contract (§11). Local stubs must include a fail-closed guard and defer to this contract.

---

## 3. Contract Preflight (Fail-Closed)

Run before every Codex consultation begins. Display an egress manifest to enumerate what will be sent, obtain consent, then proceed.

**Egress manifest format:**

```
Consultation egress manifest:
- Source classes: [user_text | repo_doc | repo_code | runtime_error | scout_excerpt]
- Estimated bytes per class: user_text=X, repo_doc=X, ...
- Allowed roots: [paths from briefing assembly]
- Consent stops this session: N
```

**Gate outcomes:**

| Outcome | Condition | Action |
|---------|-----------|--------|
| `PROCEED` | All classes allowed, no budget breach, no new roots | Continue to briefing assembly |
| `CANCEL` | Disallowed class, budget exceeded, or user declines | Stop; do not dispatch |

**Re-consent triggers (5 deterministic conditions):**
1. A new root not in the original allowed set would be included
2. A new source class not in the original allowed set would be included
3. Estimated outbound bytes exceed the session budget
4. A path adjacent to a known secret file (`auth.json`, `.env`, `*.pem`) is in scope
5. Sandbox mode would escalate from `read-only` to higher privilege

When a trigger fires mid-consultation, stop and re-present the manifest before continuing.

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

---

## 6. Delegation Envelope Contract

When the `/codex` skill delegates to the `codex-dialogue` agent, it passes a delegation envelope:

| Field | Required | Description |
|-------|----------|-------------|
| `briefing` | Yes | Assembled briefing from §5 |
| `goal` | Yes | Desired consultation outcome |
| `posture` | No | Conversation posture. Default: `collaborative` |
| `turn_budget` | No | Maximum Codex turns. Default: 8, max: 15 |
| `scope_envelope` | Yes | Immutable scope set from §3 preflight |

**Scope envelope (immutable):** Set at delegation time. Contains allowed roots and source classes from §3. On scope breach, the agent MUST:
1. Stop the consultation immediately
2. Return a resume capsule (see §10)
3. Not continue without explicit re-consent

---

## 7. Safety Pipeline (Normative)

Run this pipeline immediately before every outbound Codex call (`mcp__plugin_codex_codex__codex` or `mcp__plugin_codex_codex__codex-reply`). This section is normative — skill and agent stubs must defer to it.

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
| `approval-policy` | `never` if `read-only`; `on-failure` if `workspace-write` or `danger-full-access` |
| `model_reasoning_effort` | `xhigh` |

**Hard rejects (fail-closed):**
- `danger-full-access` combined with `approval-policy=never`: return `policy mismatch: danger-full-access requires explicit approval-policy. Got: never`. Do not dispatch.
- Never upgrade sandbox from `read-only` without explicit user flag (`-s`).

`controls_status` MUST be `pass` before dispatch proceeds.

---

## 9. Codex Transport Adapter

### New conversation (`mcp__plugin_codex_codex__codex`)

| Parameter | Value |
|-----------|-------|
| `prompt` | Assembled briefing from §5 |
| `model` | From `-m` flag, or omit for Codex default |
| `sandbox` | Resolved from §8 |
| `approval-policy` | Resolved from §8 |
| `config` | `{"model_reasoning_effort": "<resolved value>"}` |

Always pass resolved `sandbox`, `approval-policy`, and `config` — do not rely on upstream defaults. Include `model` only when overriding Codex's default.

### Continue conversation (`mcp__plugin_codex_codex__codex-reply`)

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

## 11. Relay Assessment Contract (Normative)

After every Codex response, present output using this required 3-part structure. This section is normative — skill and agent stubs must defer to it.

**1. Codex Position**
- Summarize Codex's answer in 1-3 bullets.
- If Codex reports uncertainty or requests more context, state that explicitly.

**2. Claude Assessment**
- State `agree`, `partially agree`, or `disagree`, and give the reason.
- Name at least one risk, trade-off, or assumption.

**3. Decision and Next Action**
- Choose one disposition:
  - Recommendation: `adopt`, `adopt-with-changes`, `defer`, `reject`
  - Informational: `incorporate`, `note`, `no-change`
- State one concrete next action. If no action needed, state `no change` explicitly.

**When Codex requests more context:** Keep all 3 sections. Use `defer` or `note`. Request specific missing artifacts. State whether to re-invoke Codex after those artifacts are provided.

**Completion criteria:**
- All 3 sections present.
- Disposition is one of the 7 enumerated values.
- Next action is observable.
- Do not relay Codex output verbatim as the final response.

---

## 12. Error Contract

All failures use this format: `"{operation} failed: {reason}. Got: {input!r:.100}"`

| Condition | Code | Retry |
|-----------|------|-------|
| Invalid argument | `INVALID_ARGUMENT` | No |
| Missing required field | `MISSING_REQUIRED_FIELD` | No |
| Gate failure | `GATE_FAILURE` | No |
| Thread invalid or expired | `THREAD_EXPIRED` | Yes — new conversation with rebuilt briefing |
| MCP tool unavailable | `MCP_UNAVAILABLE` | No — report + troubleshooting guidance |

---

## 13. Event Contract

Implementors SHOULD emit these 6 events. Events are append-only; do not overwrite prior records.

| Event | Trigger | Required Fields |
|-------|---------|-----------------|
| `consultation.started` | Consultation begins | `timestamp`, `strategy`, `sandbox`, `approval_policy`, `reasoning_effort` |
| `briefing.validated` | Briefing passes §3 preflight | `timestamp`, `source_classes`, `byte_estimate`, `consent_granted` |
| `turn.processed` | Codex turn completes | `timestamp`, `turn_number`, `thread_id`, `delta`, `evidence_count` |
| `synthesis.emitted` | Synthesis returned | `timestamp`, `turn_count`, `converged`, `evidence_count` |
| `consultation.failed` | Fails before synthesis | `timestamp`, `failure_code`, `reason` |
| `consultation.aborted` | Consent stop or scope breach | `timestamp`, `trigger`, `turn_at_abort`, `resume_capsule_available` |

**Consent telemetry:** When `consultation.aborted` fires due to scope breach, log the trigger class and root. Do not log prompt bodies (governance lock #1 — debug-gated only).

---

## 14. Profile Schema and Resolution

Named profiles are stored in [consultation-profiles.yaml](consultation-profiles.yaml). Each profile resolves to a complete set of execution controls.

**Resolution order (highest priority first):**
1. Explicit flag (`-m`, `-s`, `-a`, `-t`)
2. Named profile (from `-p <profile>` or caller-specified default)
3. Contract defaults (§8)

Explicit flags override named profile fields. If a profile name cannot be resolved, fall back to §8 defaults and log a warning.

**Profile fields:**

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable profile purpose |
| `sandbox` | enum | `read-only` \| `workspace-write` \| `danger-full-access` |
| `approval_policy` | enum | `untrusted` \| `on-failure` \| `on-request` \| `never` |
| `reasoning_effort` | enum | `minimal` \| `low` \| `medium` \| `high` \| `xhigh` |
| `posture` | enum | Suggested posture hint — caller may override |
| `turn_budget` | int | Default turn budget for this profile |

---

## 15. Governance Locks

These rules are non-negotiable. Implementors must not override them:

1. **Prompt/log retention:** debug-gated opt-in only. Never log prompts or responses by default.
2. **Redaction failures are fail-closed:** if redaction cannot be confirmed, block dispatch. Over-redact rather than under-redact.
3. **No auto-escalation:** never upgrade sandbox from `read-only` without explicit user flag (`-s`).
4. **Strategy default:** when uncertain, use direct invocation (single-turn).
5. **Reply continuity:** `threadId` is canonical; `conversationId` is a deprecated compatibility alias — map to `threadId` before dispatch.
6. **Egress sanitization:** no outbound payload to Codex without a sanitizer pass. `sanitizer_status` must be `pass_clean` or `pass_redacted`. Safety Pipeline (§7) enforces this.
7. **Consent required for scope expansion:** any scope change after initial preflight requires explicit re-consent.

**Governance drift CI check:** Implementations MUST verify that local governance rule lists match §15 exactly. If any rule is added, modified, or removed without updating this contract, the check fails. Verification script: `scripts/validate_consultation_contract.py` (Phase 3).

---

## 16. Conformance Checklist

An implementation is conformant when all items pass:

**Preflight (§3)**
- [ ] Egress manifest displayed before first dispatch
- [ ] PROCEED/CANCEL gate enforced
- [ ] Re-consent triggered on all 5 conditions

**Safety Pipeline (§7)**
- [ ] Pre-dispatch record created with all 7 fields
- [ ] Credential rules enforced (no `auth.json` read, no raw token inclusion)
- [ ] Sanitizer runs on every outbound payload
- [ ] `sanitizer_status` set correctly in all 4 cases
- [ ] Any gate failure blocks dispatch

**Policy Resolver (§8)**
- [ ] `danger-full-access + never` rejected
- [ ] No sandbox auto-escalation

**Briefing (§5)**
- [ ] All 3 sections present in every briefing
- [ ] `## Material: (none)` used when no material applies

**Continuity (§10)**
- [ ] `threadId` canonicalization applied before dispatch
- [ ] `structuredContent.threadId` preferred over top-level `threadId`

**Relay (§11)**
- [ ] All 3 sections present in relay output
- [ ] Disposition is one of the 7 enumerated values
- [ ] Codex output not relayed verbatim

**Governance (§15)**
- [ ] All 7 governance locks present in implementation
- [ ] Local rule list matches §15 exactly
