# Cross-Model Plugin Enhancements

**Date:** 2026-02-19
**Status:** Design Complete
**Purpose:** Three enhancements to the cross-model plugin: (1) gathering agent tuning to reduce output overlap, (2) Codex-assisted planning via `--plan` flag, (3) consultation analytics for cross-session outcome tracking.
**Derived from:** Integration testing of `/dialogue` pipeline (2026-02-19) + 5-turn collaborative Codex dialogue on enhancement approaches.

---

## 1. Problem Statements

### 1.1 Gathering Agent Overlap

When the `/dialogue` pipeline processes questions with no testable assumptions (e.g., "How does X work?"), the falsifier agent falls back to emitting `CLAIM`/`OPEN` lines — the same tag types the code explorer emits. Both agents explore code files, producing structurally redundant output. The existing domain partition (code explorer barred from `docs/decisions/`, `docs/plans/`, `docs/learnings/`; falsifier directed to start there) is advisory in the fallback path, not mandatory. The dedup mechanism only removes exact `path:line` matches, not semantically similar content.

**Evidence:** Integration test (2026-02-19) — both gatherers produced overlapping CLAIMs about the redaction pipeline's 3-stage structure, footgun tests, and fail-closed behavior when no assumptions were extractable.

### 1.2 No Codex-Assisted Planning

The `/dialogue` pipeline assumes a formed question. Planning tasks start with problem statements ("how should we architect X?"), not questions with testable assumptions. There is no mechanism to decompose a problem statement into a structured question with assumptions and key terms before the gatherers run. The existing profiles (`quick-check`, `deep-review`, `adversarial-challenge`, `exploratory`, `code-review`) set posture and budget but don't affect the pipeline's input processing.

### 1.3 No Consultation Analytics

Each `/codex` and `/dialogue` invocation produces a Synthesis Checkpoint with structured outcomes (RESOLVED/UNRESOLVED/EMERGED), but this data exists only in the conversation context. There is no cross-session persistence for dialogue outcomes. The `codex_guard.py` hook writes security telemetry (`block`, `shadow`) and basic consultation metadata (`consultation`) to `~/.claude/.codex-events.jsonl`, but lacks dialogue-quality fields: posture, turn count, convergence, seed_confidence, synthesis counts, gatherer metrics.

The learning system spec (Phase 2+) defines Episode and Learning Card schemas for knowledge capture, but analytics — statistical outcome tracking — is architecturally adjacent, not identical. The V2 deferred item "third conditional gatherer when LOW_SEED_CONFIDENCE >30% over 10+ sessions" explicitly requires cross-session outcome data that doesn't exist yet.

---

## 2. Enhancement 1: Gathering Agent Tuning

### 2.1 Approach

Constrain the falsifier's no-assumptions fallback to **rationale surfaces only**. Add inline **provenance tags** to CLAIM lines, validated by the assembler.

### 2.2 Falsifier Fallback Constraint

In `context-gatherer-falsifier.md`, replace the no-assumptions fallback (current: "explore the codebase repo-first as in Step 2") with:

> When the `assumptions` list is empty:
> 1. Explore **rationale surfaces only**: `docs/decisions/`, `docs/plans/`, `docs/learnings/`, `CLAUDE.md`, `README.md`, and architectural files at repository root.
> 2. Do NOT explore code files, test files, or config files — those are the code explorer's domain.
> 3. Emit `CLAIM` and `OPEN` items about design rationale, architectural decisions, and documented constraints relevant to the question.
> 4. Tag every `CLAIM` line with `[SRC:docs]`.

This makes the domain partition **mandatory** in the fallback path, eliminating structural overlap with the code explorer (which is already barred from these directories).

### 2.3 Provenance Tags

Add a `[SRC:<source>]` metadata field to `CLAIM` lines:

| Tag | Meaning | Emitter |
|-----|---------|---------|
| `[SRC:code]` | Derived from code, test, or config files | Gatherer A (code explorer) |
| `[SRC:docs]` | Derived from decision docs, plans, learnings, architecture files | Gatherer B (falsifier) |

**Emission rules:**
- Gatherer A: emit `[SRC:code]` on every `CLAIM` line.
- Gatherer B: emit `[SRC:docs]` on every `CLAIM` line (no-assumptions fallback only). When testing assumptions (COUNTER/CONFIRM), no provenance tag required — the AID field already provides traceability.
- `OPEN` lines: no provenance tag required (they signal gaps, not findings).

### 2.4 Assembler Validation

In the `/dialogue` SKILL.md assembly step, after 3a (Parse):

**3a-bis. Validate provenance:** For each `CLAIM` line, check for `[SRC:code]` or `[SRC:docs]`. If a CLAIM line lacks a provenance tag:
- **Infer from citation path** as fallback: if citation starts with `docs/decisions/`, `docs/plans/`, `docs/learnings/`, or matches `CLAUDE.md`/`README.md` → infer `[SRC:docs]`. Otherwise → infer `[SRC:code]`.
- Increment `provenance_inferred_count`.

If `provenance_inferred_count > 0`, set `seed_confidence` to `low` (the gatherer didn't follow its output format consistently — context quality is uncertain).

**Why path inference instead of hard-dropping:** Avoids a bootstrapping problem. The first runs after updating gatherer instructions will likely produce untagged lines. Path inference provides a grace period without losing data.

### 2.5 Tag Grammar Extension

Add to `tag-grammar.md`:

```
[SRC:<source>] — provenance tag. Values: `code`, `docs`. Indicates the exploration surface the finding came from. Required on CLAIM lines. Optional on OPEN lines. Not used on COUNTER/CONFIRM (AID provides traceability).
```

Update the grammar line:
```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>] [SRC:<source>]
```

### 2.6 Files Modified

| File | Change |
|------|--------|
| `agents/context-gatherer-falsifier.md` | Constrain no-assumptions fallback to rationale surfaces; add `[SRC:docs]` to CLAIM output |
| `agents/context-gatherer-code.md` | Add `[SRC:code]` to CLAIM output |
| `skills/dialogue/SKILL.md` | Add 3a-bis provenance validation; path inference fallback |
| `skills/dialogue/references/tag-grammar.md` | Add `[SRC:<source>]` to grammar, tag table, and examples |

All paths relative to `packages/plugins/cross-model/`.

### 2.7 Open Questions

1. **Provenance tag scope beyond no-assumptions fallback.** Should Gatherer B always emit `[SRC:docs]` on CLAIM lines, even when testing assumptions? Current design: only in no-assumptions fallback. Rationale: when assumptions exist, the COUNTER/CONFIRM tags with AID already provide traceability — adding SRC is redundant. Revisit if analytics shows assembler needs richer signal.

2. **Path inference deprecation timeline.** Path inference is a bootstrapping mechanism. After N sessions where provenance_inferred_count is consistently 0, the inference code could be replaced with hard-drop. No timeline set — measure via analytics first.

---

## 3. Enhancement 2: Codex-Assisted Planning (`--plan`)

### 3.1 Approach

Add a `--plan` flag to `/dialogue` that triggers a **Step 0 question-shaping pre-step** before the normal pipeline. Step 0 decomposes a problem statement into a structured question with assumptions, key terms, and confidence signal.

### 3.2 Argument Extension

Add to the `/dialogue` SKILL.md argument table:

| Flag | Short | Values | Default |
|------|-------|--------|---------|
| `--plan` | — | boolean | false |

When `--plan` is present, Step 0 runs before Step 1.

### 3.3 Step 0: Question Shaping

When `--plan` is set, before the normal pipeline:

**Input:** The user's raw problem statement (e.g., "how should we architect the caching layer?").

**Process:** Claude (locally, no Codex) decomposes the problem statement into:

| Field | Type | Description |
|-------|------|-------------|
| `planning_question` | string | A focused, answerable question derived from the problem statement |
| `assumptions` | list[string] | 2-5 testable assumptions extracted from or implied by the problem statement, with A1/A2/... IDs |
| `key_terms` | list[string] | 3-8 search terms for the code explorer (function names, module names, concepts) |
| `shape_confidence` | `high` \| `medium` \| `low` | Claude's confidence that the decomposition captures the user's intent |
| `ambiguities` | list[string] | 0-3 ambiguities that could change the decomposition if resolved |

**Output flow:**
- `planning_question` replaces the raw question for all downstream steps.
- `assumptions` feed into Step 1 (assumption extraction) — the normal Step 1 extraction is skipped when Step 0 provides assumptions.
- `key_terms` feed into Step 2 (Gatherer A prompt) — replaces the normal key term extraction.
- `shape_confidence` is logged in analytics (see §4). If `low`, emit a note to the user: "Question decomposition has low confidence. Consider clarifying: {ambiguities}."
- `ambiguities` are surfaced to the user but do not block the pipeline.

**Multiplicative benefit:** Step 0 improves both gatherers simultaneously. The code explorer gets better search targets (`key_terms`), and the falsifier gets better assumption lists (`assumptions`). This is multiplicative, not additive — the quality improvement compounds across both parallel agents.

### 3.4 Planning Profile

Add to `consultation-profiles.yaml`:

```yaml
planning:
  description: >
    Plan review and architectural design. Evaluative posture with proactive
    question shaping. Use when reviewing plans, making architectural decisions,
    or exploring design trade-offs.
  sandbox: read-only
  approval_policy: never
  reasoning_effort: xhigh
  posture: evaluative
  turn_budget: 8
```

The `--plan` flag and `--profile planning` are independent:
- `--plan` triggers Step 0 (question shaping).
- `--profile planning` sets posture/budget defaults.
- `/dialogue --plan --profile planning "how should we..."` uses both.
- Optional: `/plan` UX alias maps to `/dialogue --plan --profile planning`.

### 3.5 Step 0 Template

The Step 0 decomposition uses a structured template. Placement: inline in SKILL.md (not a separate reference document) — the template is small enough to include directly and benefits from being co-located with the pipeline steps.

```
Given this problem statement: "{raw_input}"

Decompose into:
1. A focused, answerable question (one sentence)
2. 2-5 testable assumptions (things that could be true or false about the codebase)
3. 3-8 search terms (function names, module names, file patterns, concepts)
4. Your confidence that this decomposition captures the user's intent (high/medium/low)
5. 0-3 ambiguities that could change the decomposition

Format:
planning_question: ...
assumptions:
- A1: "..."
- A2: "..."
key_terms: [term1, term2, ...]
shape_confidence: high|medium|low
ambiguities:
- ...
```

### 3.6 Versioning

| Version | Capability | Trigger |
|---------|-----------|---------|
| v1 (this spec) | Template decomposition — Claude-local question shaping | `--plan` flag |
| v1.5 (future) | Interactive shaping — user clarification of ambiguities before pipeline runs | `--plan --interactive` |
| v2 (future) | Multi-dialogue — Codex helps shape the question in a pre-dialogue turn | Explicit opt-in |

v1.5 and v2 are deferred. v1 validates the core value (better questions → better gatherer output → better dialogues) before adding complexity.

### 3.7 Files Modified

| File | Change |
|------|--------|
| `skills/dialogue/SKILL.md` | Add `--plan` flag, Step 0 section, template, shape_confidence handling |
| `references/consultation-profiles.yaml` | Add `planning` profile |

All paths relative to `packages/plugins/cross-model/`.

### 3.8 Open Questions

1. **`/plan` alias.** Whether to create a separate `/plan` command that maps to `/dialogue --plan --profile planning`. Pro: discoverable UX. Con: another skill file to maintain. Defer to user feedback.

2. **Interactive mode (v1.5).** When `shape_confidence` is `low`, should Step 0 pause and present ambiguities to the user via AskUserQuestion? Current design: surface ambiguities but don't block. v1.5 would add blocking clarification.

---

## 4. Enhancement 3: Consultation Analytics

### 4.1 Approach

Extend `~/.claude/.codex-events.jsonl` with `dialogue_outcome` event records. The writer is the `/dialogue` skill (has full pipeline visibility). No new infrastructure.

### 4.2 Writer Location

**Writer:** The `/dialogue` skill, at Step 6 (after receiving synthesis from `codex-dialogue`).

**Rationale:** The `/dialogue` skill has complete pipeline state:
- Gatherer metrics (line counts, parse results, retry counts)
- Assembly decisions (discards, dedup, cap, provenance violations)
- Health check results (seed_confidence, threshold pass/fail)
- Delegation parameters (posture, budget, scope_envelope)

The `codex-dialogue` agent has synthesis checkpoint data (RESOLVED/UNRESOLVED/EMERGED counts, confidence, basis), but this data is returned through the Task tool output — the skill can parse it without the agent needing to know about analytics.

**Why not `codex_guard.py`:** The hook only sees individual Codex tool calls (PreToolUse/PostToolUse), not the orchestration layer above. It lacks visibility into gatherer metrics, seed_confidence decisions, assumption counts, and synthesis outcomes.

**Why not `codex-dialogue` agent:** The agent should remain analytics-agnostic. It produces structured output (Synthesis Checkpoint); the consumer of that output (the skill) decides what to persist. This keeps the agent focused on dialogue quality, not persistence concerns.

### 4.3 Event Schema

```jsonc
{
  // Core
  "schema_version": "0.1.0",
  "consultation_id": "uuid-v4",     // Unique per /dialogue invocation
  "thread_id": "codex-thread-id",   // From codex-dialogue, nullable
  "session_id": "claude-session-id", // Current Claude Code session
  "event": "dialogue_outcome",
  "ts": "2026-02-19T18:43:44Z",

  // Dialogue parameters
  "posture": "collaborative",       // Resolved posture
  "turn_count": 5,                  // Actual turns used
  "turn_budget": 8,                 // Budgeted turns
  "profile_name": null,             // Profile used, nullable
  "mode": "server_assisted",        // "server_assisted" (with MCP) | "manual_legacy"

  // Outcome (parsed from codex-dialogue Synthesis Checkpoint)
  "converged": true,
  "convergence_reason_code": "all_resolved", // Enum: all_resolved | budget_exhausted | natural_convergence | error
  "termination_reason": "convergence",       // Enum: convergence | budget | error | scope_breach
  "resolved_count": 7,
  "unresolved_count": 0,
  "emerged_count": 3,

  // Context quality
  "seed_confidence": "normal",           // "normal" | "low"
  "low_seed_confidence_reasons": [],     // Array of enum: thin_citations | few_files | zero_output | provenance_violations
  "assumption_count": 4,
  "no_assumptions_fallback": false,

  // Gatherer metrics
  "gatherer_a_lines": 23,          // Parseable tagged lines from code explorer
  "gatherer_b_lines": 14,          // Parseable tagged lines from falsifier
  "gatherer_a_retry": false,       // Whether low-output retry fired
  "gatherer_b_retry": false,
  "citations_total": 34,           // Total lines with @ path:line
  "unique_files_total": 12,        // Unique file paths cited
  "counter_count": 3,              // After cap
  "confirm_count": 3,
  "open_count": 10,
  "claim_count": 24,

  // Scouting (from codex-dialogue output)
  "scout_count": 0,                // Evidence scouts executed during dialogue

  // Planning (nullable — populated when --plan is used, Enhancement 2)
  "question_shaped": null,          // boolean, null when --plan not used
  "shape_confidence": null,         // "high" | "medium" | "low", null when --plan not used
  "assumptions_generated_count": null,
  "ambiguity_count": null,

  // Provenance (nullable — populated when Enhancement 1 is active)
  "provenance_inferred_count": null, // Lines where SRC tag was inferred from path

  // Linkage (nullable — for future learning system integration)
  "episode_id": null                 // EP-XXXX when promoted to Episode
}
```

### 4.4 Schema Versioning

The `schema_version` field enables forward compatibility:
- `0.1.0`: Initial schema (this spec). Analytics enhancement only.
- `0.2.0`: Add provenance fields (Enhancement 1 ships).
- `0.3.0`: Add planning fields (Enhancement 2 ships).

Readers must handle missing fields gracefully (nullable fields may be absent in older records).

### 4.5 Emission Logic

In `/dialogue` SKILL.md Step 6, after presenting synthesis to user:

1. Generate `consultation_id` (UUID v4).
2. Parse `codex-dialogue` output for: `converged`, `resolved_count`, `unresolved_count`, `emerged_count`, `scout_count`, `thread_id`.
3. Assemble event from pipeline state + parsed synthesis data.
4. Append to `~/.claude/.codex-events.jsonl` using the same format as existing events (one JSON object per line, `_append_log` pattern from `codex_guard.py`).

**Error handling:** If event emission fails (file write error), log a warning but do not block the user from seeing the synthesis. Analytics is best-effort, never blocking.

### 4.6 Standalone `/codex` Analytics

The `/codex` skill should also emit analytics for standalone (non-`/dialogue`) consultations, but with a reduced schema:

```jsonc
{
  "schema_version": "0.1.0",
  "consultation_id": "uuid-v4",
  "thread_id": "codex-thread-id",
  "session_id": "claude-session-id",
  "event": "consultation_outcome",  // Different event type
  "ts": "...",
  "posture": "collaborative",
  "turn_count": 1,
  "turn_budget": 1,
  "profile_name": null,
  "mode": "server_assisted",
  "converged": null,                // Not applicable for single-turn
  "termination_reason": "complete"
}
```

This provides a unified analytics stream for all cross-model consultations, enabling comparison between `/codex` and `/dialogue` usage patterns.

### 4.7 Reading Analytics

A future `/consultation-stats` command (not in this spec) reads `~/.claude/.codex-events.jsonl`, filters for `dialogue_outcome` and `consultation_outcome` events, and computes:

- Total consultations by type and posture
- Convergence rate (converged / total dialogue_outcome)
- Average turn utilization (turn_count / turn_budget)
- seed_confidence distribution
- no_assumptions_fallback frequency (the V2 trigger for third gatherer)
- EMERGED items per dialogue (cross-model value metric)

### 4.8 Relationship to Learning System

Analytics and Episodes serve different purposes:

| Concern | Analytics | Episodes |
|---------|-----------|----------|
| What | Statistical outcome tracking | Knowledge capture |
| Granularity | Per-consultation metrics | Per-insight learning cards |
| Persistence | Append-only JSONL | Structured YAML+markdown |
| Lifecycle | Accumulate indefinitely | Curated, merged, deprecated |

They connect via shared identifiers:
- `consultation_id` links an analytics record to the dialogue that produced it.
- `episode_id` (nullable in analytics) links to a learning system Episode when a consultation is promoted via `/learn log`.
- `session_id` links both to the Claude Code session.

Analytics does NOT replace Episodes. It provides the quantitative data that Episodes lack (convergence rates, gatherer metrics, turn utilization). Episodes provide the qualitative data that analytics lacks (specific insights, design rationale, reusable knowledge).

### 4.9 Files Modified

| File | Change |
|------|--------|
| `skills/dialogue/SKILL.md` | Add Step 6 analytics emission after synthesis presentation |
| `skills/codex/SKILL.md` | Add analytics emission for standalone consultations |
| `README.md` | Add `dialogue_outcome` and `consultation_outcome` to event log table |

All paths relative to `packages/plugins/cross-model/`.

### 4.10 Open Questions

1. **Exact emission location in `/dialogue` skill.** Step 6 (after synthesis) is the logical place, but should the emission be a visible step in the pipeline documentation, or a silent side-effect? Current design: visible step to aid debugging. Revisit if users find the analytics emission noisy.

2. **Retention policy.** `codex-events.jsonl` has no retention policy currently. As analytics records accumulate, the file could grow large. Consider a 90-day rotation or size cap. Not blocking for v1 — the file is append-only JSONL and can be truncated manually.

---

## 5. Implementation Sequencing

| Order | Enhancement | Size | Rationale |
|-------|------------|------|-----------|
| 1 | Analytics (§4) | S | Establishes baseline metrics; other enhancements benefit from data |
| 2 | Gathering Agent Tuning (§2) | S | Self-contained; provenance validation measurable via analytics |
| 3 | Planning Mode (§3) | M | Reuses pre-created nullable analytics fields; validates quality improvement |

Each enhancement is independently shippable. Schema versioning (`schema_version` field) ensures forward compatibility as fields are added.

**Dependencies:**
- Enhancement 2 depends on Enhancement 3 for analytics fields (`question_shaped`, `shape_confidence`, etc.) but can ship without them — the fields are nullable.
- Enhancement 1 depends on Enhancement 3 for `provenance_inferred_count` field but can ship without it — same nullable pattern.
- Enhancement 3 has no dependencies.

---

## 6. Success Criteria

### 6.1 Enhancement 1 (Gathering Agent Tuning)

- No-assumptions fallback produces <20% content overlap between gatherers (measured by shared citation paths).
- Provenance tags present on >90% of CLAIM lines after 5+ `/dialogue` invocations.
- `provenance_inferred_count` trends toward 0 over time.

### 6.2 Enhancement 2 (Planning Mode)

- `--plan` Step 0 produces `shape_confidence: high` on >70% of planning questions.
- Planning-mode dialogues show higher convergence rate than non-planning dialogues on architectural questions (measurable via analytics).
- User does not need to rephrase question after Step 0 >80% of the time.

### 6.3 Enhancement 3 (Analytics)

- `dialogue_outcome` events emitted for 100% of `/dialogue` invocations.
- `consultation_outcome` events emitted for 100% of `/codex` invocations.
- V2 trigger measurable: `no_assumptions_fallback` frequency and `seed_confidence: low` rate computable from JSONL data.

---

## 7. What This Spec Does Not Cover

- **Learning system Phase 1+.** Episodes, Learning Cards, and the `learnings.retrieve` MCP server are separate work items defined in `docs/plans/2026-02-10-cross-model-learning-system.md`.
- **Third conditional gatherer (V2).** The trigger condition (`LOW_SEED_CONFIDENCE >30% over 10+ sessions`) is measurable after Enhancement 3 ships, but the gatherer design is future work.
- **`/consultation-stats` command.** Reading and summarizing analytics data is future work. The JSONL format is self-documenting and can be queried with `jq` in the interim.
- **Rolling escalation triggers.** Automatic mode switching between `/codex` and `/dialogue` based on question complexity is V2+ work.

---

## 8. References

| What | Where |
|------|-------|
| Dialogue skill orchestrator spec | `docs/plans/2026-02-19-dialogue-skill-orchestrator.md` |
| Cross-model learning system spec | `docs/plans/2026-02-10-cross-model-learning-system.md` |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` |
| Consultation profiles | `packages/plugins/cross-model/references/consultation-profiles.yaml` |
| Tag grammar | `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md` |
| Existing event log | `~/.claude/.codex-events.jsonl` (schema in `packages/plugins/cross-model/README.md`) |
| Codex dialogue (5-turn, collaborative) | 2026-02-19 session, thread archived in conversation |
