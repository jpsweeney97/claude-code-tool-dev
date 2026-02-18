# /codex Skill — Three-Angle Deep Review

**Date:** 2026-02-17
**Subject:** `.claude/skills/codex/SKILL.md` (270 lines)
**Method:** 3 parallel codex-dialogue subagents, 2 rounds each
**Total turns:** 30 (10 adversarial + 8 evaluative + 12 exploratory)

## Overview

Three independent Codex dialogues examined the `/codex` skill from complementary angles. Round 1 diagnosed issues; Round 2 produced concrete designs and draft text.

| Dialogue | Posture | Turns | Converged | Output |
|----------|---------|-------|-----------|--------|
| Security | Adversarial | 10 | Yes (T10) | Sprint plan with 3 prioritized remediations |
| Design Quality | Evaluative | 8 | Yes (T8) | Paste-ready draft text for 4 SKILL.md fixes |
| Evolution | Exploratory | 12 | Budget-capped | P0 substrate contract design + file inventory |

---

## Dialogue 1: Security (Adversarial)

### Round 1 (T1-T6): Structural Diagnosis

**Core finding:** The `/codex` egress path has a structural asymmetry — the context-injection helper has real code enforcement (HMAC tokens, denylist, git-ls-files, redaction pipeline with 969 tests), while the skill's egress controls are purely advisory markdown instructions consumed by an LLM.

**Dominant risk:** IP/confidential-context exfiltration through normal intended use, not credential leakage. Step 1 explicitly instructs gathering "current task, decisions made, relevant material" — token safety rules only catch credential-shaped patterns.

**Governance rule #6 verdict:** Underspecified + unenforceable compliance semantics. Real controls exist in complementary systems, but rule #6 itself has no enforcement mechanism.

**Priority ranking (resolved disagreement):**
1. Scope-delta consent gate (addresses dominant IP risk)
2. Danger break-glass guard (blocks `danger-full-access` + `never`)
3. Mandatory egress dispatch gate with sanitizer receipt (enforces rule #6)

**Additional findings:**
- Token safety rule #3 ("scan for secret-like text") is not reliably implementable by an LLM alone — will miss signed URLs, session cookies, DSNs, nonstandard formats
- "Decision-locked" governance labels are intent, not enforcement — 5 of 6 rules are code-enforceable; rule 4 (strategy default) resists automation
- Prompt injection from Codex responses is a real but bounded attack path; `manual_legacy` fallback bypasses helper-side controls

### Round 2 (T7-T10): Concrete Remediation Design

#### Scope-Delta Consent Gate (Sprint 1 MVP)

**Manifest format:** User-visible egress plan showing source items by class:
- Classes: `user_text`, `repo_doc`, `repo_code`, `runtime_error`, `scout_excerpt`
- Byte sizes per class
- Scope envelope: `allowed_roots` and `allowed_classes`
- 5 deterministic re-consent triggers: new root, new class, budget exceed, secret-adjacent path, mode escalation

**Scope envelope:** Strict mode (MVP) — exact files/paths from briefing assembly, no adjacency expansion, stop-on-breach.

**Subagent interaction:** Scope envelope passed at delegation time (immutable). On breach, subagent exits with resume capsule:
```
{threadId, current_turn, checkpoint_id, state_checkpoint,
 turn_history, extraction_history, consent_state,
 ledger_summary, integrity_tag}
```

**UX target:** p50 zero interruptions, p90 at most one per dialogue.

#### Break-Glass for Dangerous Flag Combinations

Interim: skill-level hard reject of `danger-full-access` + `approval-policy=never`.
Future (Sprint 2): MCP wrapper server with server-side policy enforcement.

#### `manual_legacy` Assessment

Different risk shape, not safer overall. Narrower exfiltration channel (no scouts) but all helper protections gone, agent retains normal tool access. Recommended policy: constrained mode (no new file reads after initial consented set, low turn cap, strict outbound budget).

#### Sprint Plan

| Sprint | Item | Effort |
|--------|------|--------|
| **1 (MVP)** | Hard reject `danger-full-access + never` | ~1 day |
| 1 | Start-of-run egress manifest + PROCEED/CANCEL | ~2-3 days |
| 1 | Strict scope envelope, stop-on-breach | ~2-3 days |
| 1 | Behavioral conformance tests for shipped invariants | ~2-3 days |
| 1 | Governance drift CI check | ~1 day |
| 1 | Telemetry on consent stops and breach reasons | ~1 day |
| **2** | Resume capsule + resume entrypoint | ~3-5 days |
| 2 | Wrapper MCP server (outbound gate + danger policy + sanitizer receipt) | ~5-8 days |
| 2 | Conformance tests for wrapper-path and fallback-path parity | ~2-3 days |
| **3+** | Repo policy file (`.codex-egress-policy.yml`) | TBD |
| 3+ | Heuristic expansion tuning (if telemetry warrants) | TBD |

#### Open Questions (Adversarial)

- Resume capsule `turn_history` field: full `validated_entry` records or compact summary?
- Consent telemetry vs. governance rule #1 tension (debug-gated log retention)
- Strict envelope false-positive rate without telemetry data

---

## Dialogue 2: Design Quality (Evaluative)

### Round 1 (T1-T5): Principle Compliance Assessment

**Grade:** High C against project's 14 writing principles.

**4 material principle violations identified:**

| Priority | Fix | Principle Violated |
|----------|-----|--------------------|
| 1 | Pre-dispatch gate checklist before Step 3 | #4/#8 (Gates/Preconditions) |
| 2 | Step 4 relay output contract | #13 (Outcomes) |
| 3 | Scope boundaries block (in/out/default) | #5 (Boundaries) |
| 4 | Parser/continuity loophole closures | #9 (Loopholes) |

**Strengths identified:**
- 4-step workflow structure (Briefing -> Strategy -> Invoke -> Relay) is well-organized
- Failure handling table is comprehensive
- Argument validation is deterministic
- Token safety is correctly fail-closed in intent
- Governance section correctly labeled "Decision-Locked"

**Emergent insight:** Term definition threshold — "define terms that change runtime behavior with one-line operational definitions, not conceptual explanations." Generalizable to all skill files.

### Round 2 (T6-T8): Paste-Ready Draft Text

#### P1: Pre-Dispatch Gate (replaces Token safety, lines 158-163)

```markdown
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
```

#### P2: Step 4 Relay Output Contract (replaces lines 203-212)

```markdown
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

After relaying, capture diagnostics for this consultation (see Diagnostics section below -- timestamp, strategy, flags, success/failure).
```

#### P3: Scope Boundaries (insert after auto-invocation rule, line 13)

```markdown
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

Default on ambiguity:
Do not invoke Codex until scope is clear. Ask one clarifying question.
```

#### P4: Operational Definitions (insert after Scope Boundaries)

```markdown
## Operational Definitions

- **fail-closed:** If a required check cannot be completed with a passing result, block the Codex call and return an error.
- **debug-gated:** Include prompt/response retention or expanded logging only when debug mode is explicitly enabled for the current consultation; otherwise keep it off.
- **egress sanitization:** Run sanitizer/redaction checks on every outbound Codex payload (`prompt`, follow-up text, and outbound diagnostics metadata) before dispatch.
```

#### Open Questions (Evaluative)

- Whether the Governance section needs updating to reference the new pre-dispatch gate
- Whether the Failure Handling table should reference `controls_status` for sandbox x approval-policy validation
- Whether the anti-drift line ("treat those patterns as additive") is operationally testable

---

## Dialogue 3: Evolution (Exploratory)

### Round 1 (T1-T6): Feature Landscape Mapping

**P0: Shared consultation substrate** — Extract duplicated logic between skill and agent into a shared contract. Enables all downstream features.

**Dependency graph:**
```
P0: Shared consultation substrate
    ↓
P1 (parallelizable after P0):
├── Observability event system (unified KPI + episodic recall)
├── Learning-aware briefing injection (## Prior Learnings section)
├── Profiles-first UX (/codex --profile deep-review)
└── Direct-mode follow-up classifier (5 triggers, escalation policy)
    ↓
P2: Fan-out/synthesis composition (2+1 hybrid pattern, max 3 threads)
```

**Key design decisions:**
- **Profiles over flags:** Primary UX should be named profiles with NL modifiers; flags retained as machine/audit layer
- **Learning injection as weak priors:** Append `## Prior Learnings (Weak Priors)` to briefings before `## Question`. Visible, not hidden.
- **Multi-model abstraction is premature:** Thin transport seam (`start()` / `reply()`) only. Full provider-agnostic protocol when second backend exists.
- **Observability and episodic memory are the same physical event system:** Append-only consultation events with two projections (KPI metrics and episodic index)
- **5 follow-up triggers for direct mode:** contradiction_detected, high_risk_unverified, ambiguity_blocking, coverage_gap, learning_conflict

### Round 2 (T7-T12): P0 Substrate Contract Design

#### Contract Artifact

Single file: `docs/references/consultation-contract.md` (~410 lines, 16 sections + 2 appendices)

| # | Section |
|---|---------|
| 1 | Purpose, Scope, and Non-Goals |
| 2 | Normative Terms and Precedence |
| 3 | Contract Preflight (Fail-Closed) |
| 4 | Shared Vocabulary |
| 5 | Briefing Contract |
| 6 | Delegation Envelope Contract |
| 7 | Safety Pipeline |
| 8 | Policy Resolver Contract |
| 9 | Codex Transport Adapter |
| 10 | Continuity State Contract |
| 11 | Relay Assessment Contract |
| 12 | Error Contract |
| 13 | Event Contract (6 event types) |
| 14 | Profile Schema and Resolution |
| 15 | Governance Locks |
| 16 | Conformance Checklist |
| A | Canonical Examples |
| B | Field Dictionary |

#### Module Triage

Only 4 of 8 originally proposed modules are true hard duplicates:

| Module | Status | Evidence |
|--------|--------|----------|
| briefing_contract | Hard duplicate | Both files specify ## Context / ## Material / ## Question structure |
| safety_pipeline | Hard duplicate | Both files enumerate credential patterns and fail-closed rules |
| continuity_state | Hard duplicate | Both files specify threadId canonicalization and validation |
| transport_adapter | Hard duplicate | Both files specify mcp__codex__codex / mcp__codex__codex-reply parameters |
| delegation_handoff | Partial — folds into briefing | Only agent consumes delegation envelopes |
| error_contract | Partial — minimal shared format | Both use `"{operation} failed: {reason}. Got: {input!r:.100}"` |
| events_schema | Agent-only (currently) | No event system in skill today |
| learning_injection_adapter | Agent-only, phase-gated | Not implemented yet |

#### Stub Pattern

Full replacement (Option A) with fail-closed preflight guard. Each document that delegates to the contract uses this pattern:

```markdown
### Token Safety (Normative Contract)
Token safety is defined in `docs/references/consultation-contract.md` under `## Safety Pipeline`.
This file is not normative for credential patterns.

Before any outbound Codex dispatch:
1. Read and apply the Safety Pipeline in full.
2. Run sanitizer/redaction on every outbound payload.
3. If the Safety Pipeline cannot be read or applied, block dispatch.
```

#### Event Schema (6 event types)

1. `consultation.started` — consultation begins
2. `briefing.validated` — briefing passes preflight
3. `turn.processed` — each Codex turn completes (includes episodic recall fields)
4. `synthesis.emitted` — synthesis produced (includes episodic recall fields)
5. `consultation.failed` — consultation fails
6. `consultation.aborted` — crash before synthesis

#### Profiles

Stored separately in `docs/references/consultation-profiles.yaml` (not inside the contract). Optional gitignored local override for user customization.

#### Skill/Agent Boundary (Capability Split)

| Owner | Responsibilities |
|-------|-----------------|
| **Skill** | Step 0 preflight, argument/profile resolution, strategy selection, direct-mode dispatch + relay, event emission |
| **Agent** | 7-step loop, convergence detection, synthesis, manual_legacy, posture patterns |
| **Contract** | Briefing schema, safety pipeline, transport/continuity, error format, event schema, profile schema, relay assessment obligations |

#### File Inventory (8 files)

| Path | Action | ~Lines |
|------|--------|--------|
| `docs/references/consultation-contract.md` | Create | 300-420 |
| `docs/references/consultation-profiles.yaml` | Create | 70-130 |
| `.claude/skills/codex/SKILL.md` | Modify | 271 -> ~180-200 |
| `.claude/agents/codex-dialogue.md` | Modify | 543 -> ~500-520 |
| `docs/references/README.md` | Modify | +6-14 |
| `docs/references/context-injection-contract.md` | Modify | +6-20 |
| `scripts/validate_consultation_contract.py` | Create | 120-190 |
| `tests/test_consultation_contract_sync.py` | Create | 120-200 |

#### Key Correction: Direct Mode is Strictly Single-Turn

The exploratory dialogue (T3, round 2) overrode the prior round's proposal for a 5-trigger auto follow-up classifier in direct mode. Argument: it leaks multi-turn control into the skill and recreates the drift problem the contract solves. The classifier is deferred to a future "enhanced direct mode" feature in the agent.

#### Open Questions (Exploratory)

- CI drift validator versioning when contract sections are added/removed
- Whether preflight Step 0 should verify contract version compatibility or just presence
- `consultation.aborted` trigger conditions (timeout on turn 3? user cancel?)

---

## Cross-Dialogue Convergence

Three findings were independently reinforced across multiple dialogues:

### 1. Self-containment principle for skills

- **Evaluative (T8):** "Each skill should be fully operational standalone, with extensibility as a property rather than a dependency"
- **Exploratory (T4):** "Full replacement stubs over summary stubs" — because summary stubs create hard dependencies
- Both independently rejected conditional references to other specs

### 2. Direct mode is strictly single-turn

- **Exploratory (T3, round 2):** Auto follow-up leaks multi-turn control and recreates drift
- **Adversarial:** Consent gate scope envelope is set once at consultation start — only works if direct mode is single dispatch-relay

### 3. Pre-dispatch gate is the convergence point

All three dialogues produce designs that route through a pre-dispatch gate:
- **Evaluative:** 7-field record with enumerated patterns
- **Adversarial:** Consent manifest with scope envelope
- **Exploratory:** Contract preflight (Step 0) with fail-closed guard

These are complementary layers of the same checkpoint, not competing designs.

---

## Cross-Dialogue Tension

**Contract line count:** Exploratory targets ~410 lines. Assessment: sections 1-4 could merge into "Overview" and conformance checklist + appendices could defer to v0.2, yielding ~300 lines for v0.1.

---

## Agent IDs (for resumption)

| Dialogue | Agent ID |
|----------|----------|
| Adversarial | `a9562e8` |
| Evaluative | `aeb05f1` |
| Exploratory | `ad12dbc` |
