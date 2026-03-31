---
date: 2026-03-31
time: "17:04"
created_at: "2026-03-31T21:04:20Z"
session_id: bf48266b-f57b-4296-8a5f-5ea7bab67212
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_13-56_t03-safety-substrate-second-review-and-merge.md
project: claude-code-tool-dev
branch: main
commit: 851560f6
title: "codex.consult resolution and persistence hardening design"
type: handoff
files:
  - docs/superpowers/specs/codex-collaboration/decisions.md
  - docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md
  - packages/plugins/codex-collaboration/server/turn_store.py
  - packages/plugins/codex-collaboration/server/lineage_store.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/server/runtime.py
---

# codex.consult resolution and persistence hardening design

## Goal

Two objectives this session: (1) resolve the open question about whether `codex.consult` should be retired from the codex-collaboration spec, and (2) design the persistence replay hardening (I2/I3/I4) and type narrowing (F4/F6) work deferred from the T-03 second review.

**Trigger:** User loaded the prior handoff (`2026-03-31_13-56_t03-safety-substrate-second-review-and-merge.md`) which listed three next steps. The `codex.consult` evaluation was item #1. User then requested proceeding to items #2 and #3 (persistence hardening and type improvements) after the consult question was resolved.

**Stakes:** The `codex.consult` question is an architectural decision that affects the spec's MCP tool surface — keeping vs retiring a first-class tool. The persistence hardening addresses correctness debt on delivered R2 infrastructure where one malformed JSONL record can crash an entire store's replay.

**Success criteria:** (1) `codex.consult` open question closed with evidence-backed rationale. (2) Complete design spec for persistence replay hardening and type narrowing, reviewed and approved.

**Connection to project arc:** The `codex.consult` resolution closes the last open question in `decisions.md` that was blocking clarity on the spec's tool surface. The persistence hardening design is the input for the next implementation session — it produces the implementation plan and then code on `fix/persistence-replay-hardening` and `chore/type-narrowing` branches.

## Session Narrative

Session began by loading the prior handoff, which described the T-03 safety substrate's second review, 3 fix slices, and squash merge of PR #90 to main. The handoff's next steps listed: (1) evaluate `codex.consult` open question, (2) persistence replay hardening, (3) type improvements. User confirmed starting with the `codex.consult` evaluation.

Read `decisions.md:115-117` to understand the open question: "Whether `codex.consult` should eventually be retired in favor of native review and task patterns plus a lighter structured wrapper remains open." The question was terse — it named three things without defining the comparison criteria.

Proposed a 6-item evidence gathering plan. User refined this into 3 ranked hypotheses with a recommended sequence: (1) compare consult vs dialogue code paths, (2) inspect `/codex` skill coupling, (3) compare against official plugin native review — with the rationale that internal redundancy should be tested before external alternatives.

Launched two parallel research agents:

**Agent 1 (consult vs dialogue):** Traced 9 dimensions across `control_plane.py:codex_consult()` and `dialogue.py`. Found that bootstrap, context assembly, prompt building, output schema, turn dispatch, and response parsing are all fully shared. The divergences are in lifecycle/persistence: consult keeps ephemeral handles (no lineage write), zero journal entries, stale-marker integration, and fork-from-parent support. Agent concluded: "Feasible but not worth it in R1/R2" — consult's ephemerality is a feature.

**Agent 2 (skill coupling):** Found ~85% of the consultation contract is portable (briefing, safety, continuity, relay, governance). The tight coupling is in orchestration (~100 lines: invocation strategy, analytics events, mode determination), not semantics. `/codex` is designed one-shot but permits multi-turn via `codex-reply` in the allowlist.

Key pivot: User provided structured triage of the agent results, identifying the core tension: "H1's migration is technically clean but produces one of two outcomes" — either dialogue gains a lightweight mode that reimplements consult, or callers accept unnecessary persistence overhead. User directed proceeding to step 3 (native review comparison) with stricter gates: native review must *beat* consult, not merely match it.

**Agent 3 (native review evaluation):** Tested 5 gates. Native review failed 4/5: (1) Schema — doesn't return the structured consult result natively; (2) Complexity — all control-plane components remain; (3) Features — fork is native but post-promotion coherence is local glue; (4) Maintenance — ~150 lines saved on 2000+ spec. Only the overhead gate partially passed.

User then manually updated `decisions.md` to close the question as resolved: keep `codex.consult`. I reviewed the update and confirmed no findings.

User then redirected to the canonical roadmap at `delivery.md`, mapping the remaining handoff items against the build sequence. User classified I2/I3/I4 as "roadmap-adjacent debt" and F4/F6 as "cleanup outside the main build sequence" — neither advances a delivery milestone. Notably, AC6 analytics (which was buried in the handoff's deferred items) is actual roadmap work in packet 2b.

User chose to proceed with I2/I3/I4 + F4/F6 design, deferring AC6. This triggered the brainstorming skill.

The brainstorming phase involved 7 clarifying questions and design iterations:

1. **I3 corruption classification** — User recommended structured option A+: warning for mid-file corruption, structured replay diagnostics, no hard failure. Added the distinction: trailing truncation is parse failures after the last valid JSON line; mid-file is parse failures followed by valid lines.

2. **Diagnostics persistence** — Applied making-recommendations skill. Return-only won (verifiably best) because stores replay on every read — retained diagnostics would be overwritten constantly.

3. **Shared vs local replay** — Shared generic helper with per-store callbacks won. The deferred trailing-truncation algorithm is non-trivial and must be consistent across 3 stores.

4. **Per-store callback design** — User caught that lineage's accumulator pattern needed special handling. Initially proposed splitting into `decode_jsonl` + `replay_jsonl`, but user's P2 finding identified this as recreating divergence one layer higher. Resolution: lineage uses `replay_jsonl` with a closure-captured accumulator.

5. **Schema validation depth** — User's P1 finding: catching `KeyError` alone is insufficient. Records with wrong types (e.g., `"context_size": "big"`) pass key checks. All callbacks need explicit type validation.

6. **Type narrowing scope** — User expanded F4 to cover all stringly-typed fields: `posture`, `effort`, `sandbox`, and `approval_policy`. Also caught that `resolve_profile()` parameters should be typed end-to-end, not just the return type.

7. **Final contract tightening** — User identified 3 more gaps in the last review round: (a) `type(x) is int` not `isinstance` (bool subclasses int), (b) extra-field policy needed explicit rule, (c) `turn_budget` needed positive integer validation. Then in formal review: (d) all-corrupt-file heuristic was too permissive, (e) compatibility policy needed semantic-change boundary, (f) `check_health()` needed demotion to test/support hook.

Design spec written, reviewed, revised, and merged to main.

## Decisions

### Keep `codex.consult` as first-class MCP tool

**Choice:** `codex.consult` remains a first-class tool in the codex-collaboration spec. Not retired into `codex.dialogue` or native upstream review.

**Driver:** Three-step evidence-based analysis. User structured the evaluation as hypothesis testing with ranked alternatives.

**Alternatives considered:**
- **Retire into `codex.dialogue` with `turn_budget=1`** — Rejected. Code-path overlap is real (bootstrap, assembly, prompt, schema, dispatch, parsing all shared), but divergences are contract-level design properties: ephemeral handles, zero persistence, stale-marker integration, fork support. User stated: "`codex.consult` should not retire into `codex.dialogue` just because the code paths overlap. The overlap is real, but the remaining differences are contract-level differences, not cleanup opportunities."
- **Retire into native upstream review wrapper** — Rejected. Failed 4/5 gates. User's evaluation framework: "the burden is now on native review to beat 'keep consult,' not merely to match it."

**Trade-offs accepted:** Maintaining a separate MCP tool surface (`codex.consult` alongside `codex.dialogue.*`) when ~70% of the code path is shared. The shared code is already factored into reusable helpers, so the maintenance cost is the ~30% that's consult-specific (ephemeral handle, stale-marker, fork, audit semantics).

**Confidence:** High (E2) — two independent analysis methods (internal code-path comparison + external gate evaluation) converge on the same conclusion.

**Reversibility:** Medium — retiring `codex.consult` later is additive (route through dialogue), but the current `/codex` skill is shaped around consult semantics, requiring ~100 lines of orchestration rewrite.

**Change trigger:** Upstream Codex adds native structured output enforcement matching the consult advisory contract, OR the advisory domain drops ephemeral-handle/stale-context/fork requirements.

### Two branches with incremental migration (Approach B + C)

**Choice:** `fix/persistence-replay-hardening` for I2/I3/I4, `chore/type-narrowing` for F4/F6. Within the fix branch, incremental store migration: helper first, then turn_store, lineage_store, journal.

**Driver:** User stated: "The persistence work changes replay semantics on delivered R2 substrate. That is real correctness debt and deserves its own revert boundary." And: "F4/F6 are behavior-preserving cleanup. Bundling them with replay hardening weakens review clarity for no gain."

**Alternatives considered:**
- **Approach A (single branch)** — Rejected. Larger diff (~15 files), mixes risk profiles.
- **Approach C alone (incremental within one branch)** — Adopted as internal execution pattern within the fix branch, not as the overall strategy.

**Trade-offs accepted:** Two branches means two merges. But each is smaller and independently reviewable.

**Confidence:** High (E2) — matches standard git hygiene. User confirmed branch names align with repo convention.

**Reversibility:** High — branch organization, not functional decision.

**Change trigger:** None — process preference.

### Shared replay helper with per-store callbacks

**Choice:** Single `replay_jsonl()` function in `server/replay.py` handles line decoding and trailing-truncation classification. Per-store callbacks handle schema validation and record application.

**Driver:** The deferred trailing-truncation classification algorithm is non-trivial (accumulate corrupt indices, classify at EOF) and must be consistent across all 3 stores. User's P2 finding on the initial split proposal: "If lineage bypasses `replay_jsonl()` and implements its own apply loop, then schema-violation and unknown-op conversion become custom again in one store."

**Alternatives considered:**
- **Shared diagnostic model only** — Rejected. Classification algorithm reimplemented 3 times → inconsistency risk.
- **Full shared replay with schema validation** — Rejected. Over-abstraction for 3 consumers with different schemas.
- **decode_jsonl + replay_jsonl split** — Initially proposed, then rejected after user's P2 finding. Lineage uses `replay_jsonl` with closure-captured accumulator instead.

**Trade-offs accepted:** The callback contract is slightly abstract (returns `T | None`, raises `SchemaViolation` / `UnknownOperation`). Lineage's closure pattern (callback captures and mutates external dict, returns `None`) is a non-obvious usage of the generic interface.

**Confidence:** High (E2) — all three stores' replay loops are structurally identical. The callback isolates the only variation (schema + application logic).

**Reversibility:** High — internal refactoring, no external API change.

**Change trigger:** If a fourth store with a fundamentally different replay pattern is added, the helper may need redesign.

### Diagnostics return-only, not retained on store instances

**Choice:** `replay_jsonl()` returns `(results, ReplayDiagnostics)`. No `self.diagnostics` on store instances.

**Driver:** Stores replay on every `get()`/`list()`/`get_all()` call — no caching. Retained diagnostics would be overwritten on every read, creating misleading stale state.

**Alternatives considered:**
- **Return + retain** — Rejected. Staleness risk on a store that replays on every read.
- **Retain-only** — Rejected. Worst of both worlds.
- **Logging only (null option)** — Rejected. Untestable, unstructured.

**Confidence:** High (E3) — replay-on-every-read is a code fact verified at `turn_store.py:43`, `lineage_store.py:37`, `journal.py:93`.

**Reversibility:** High — adding instance retention later is additive.

**Change trigger:** If stores add an in-memory cache (replay once, serve from memory), retained diagnostics become viable.

### Trailing truncation requires valid prefix

**Choice:** If no valid JSON line exists in a non-empty file, all parse failures are `mid_file_corruption`, not `trailing_truncation`.

**Driver:** Review finding F2: "The most destructive replay outcome can be normalized as expected crash recovery behavior." User agreed and stated the original "all-corrupt = crash tail" was "a convenient default during design closure," not an intentional design choice.

**Alternatives considered:**
- **Original rule (all-corrupt = trailing)** — Rejected after review. Total-file corruption is the most severe outcome; normalizing it as benign is wrong.

**Trade-offs accepted:** A file that was genuinely created by a single partial append (1 corrupt trailing line, no valid lines) will be classified as `mid_file_corruption` instead of `trailing_truncation`. This is a false positive in an edge case, but the alternative (false negative on total corruption) is worse.

**Confidence:** High (E2) — the spec at `contracts.md:119-121` says "Incomplete trailing records (from crash mid-write) are discarded on load." A trailing record is relative to a valid prefix.

**Reversibility:** High — classification rule is in one function.

**Change trigger:** None — this corrects a heuristic error.

### Single-value Literal types for R1 policy fields (F5 kept)

**Choice:** `SandboxPolicy = Literal["read-only"]` and `ApprovalPolicy = Literal["never"]` — single-value literals reflecting the R1 validation gate.

**Driver:** Review finding F5 asked whether this bakes phase gating into the type surface. User confirmed intentional: type churn when freeze-and-rotate lands is the desired signal — forces callers to acknowledge the new capability.

**Alternatives considered:**
- **Broader string types with runtime gate** — Rejected. This is exactly the current bug F4 fixes. A typo in YAML silently propagates because `posture: str` accepts anything.

**Trade-offs accepted:** When freeze-and-rotate lands, widening `SandboxPolicy` from `Literal["read-only"]` to `Literal["read-only", "workspace-write"]` is a caller-visible type change.

**Confidence:** High (E2) — the validation gate at `profiles.py:119-128` already rejects everything except these values. The type now mirrors runtime behavior.

**Reversibility:** High — changing a type alias.

**Change trigger:** None — this is the intended evolution path.

## Changes

### Modified files

| File | Change | Commit |
|------|--------|--------|
| `docs/superpowers/specs/codex-collaboration/decisions.md:115-141` | Closed `codex.consult` open question as resolved. Both retirement paths rejected. Re-evaluation triggers documented. | `851560f6` |
| `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` (NEW) | Full design spec: 330 lines. Shared replay helper, per-store callbacks, diagnostic model, type narrowing, test plans, deferred work. | `82b47191`, `851560f6` |

### Files read but not modified (key understanding gained)

| File | Why read | What was learned |
|------|----------|------------------|
| `server/turn_store.py` | I2 bug site | `_replay()` at line 70: bare `record['collaboration_id']` crashes on malformed records. No type validation after `json.loads`. |
| `server/lineage_store.py` | I4 bug site | `_apply_record` at lines 110-127: `if op == "create" ... elif ...` with no else branch. Unknown ops silently dropped. `__dataclass_fields__` filter at line 117 silently ignores extra keys on create records. |
| `server/journal.py` | I3 shared pattern | `_terminal_phases()` at lines 129-146: same replay loop as other stores. `OperationJournalEntry(**record)` at line 144 would raise `TypeError` on missing fields — a third failure class distinct from `KeyError`. |
| `server/profiles.py` | F4 target | `ResolvedProfile` at lines 22-29: `posture: str`, `effort: str | None`, `sandbox: str`, `approval_policy: str`. Validation gate at lines 119-128 rejects non-default sandbox/approval but doesn't catch posture/effort typos. |
| `server/models.py` | F6 target | `AdvisoryRuntimeState` at line 123: `session: Any`. The concrete type `AppServerRuntimeSession` exists at `runtime.py:12`. Circular import (`models → runtime → models`) resolved via `TYPE_CHECKING` guard. |
| `server/control_plane.py:130-199` | Consult code path | `codex_consult()`: bootstrap, context assembly, prompt building, turn dispatch, response parsing, audit event. Ephemeral handle, stale-marker integration, fork support, network policy gate. |
| `server/dialogue.py` | Dialogue code path | `start()`, `turn()`: same shared infrastructure as consult. Additional: lineage store writes, 3-phase journal, turn store, handle quarantine, best-effort repair, crash recovery. |
| `server/runtime.py:12` | F6 concrete type | `AppServerRuntimeSession` class — the type that `session: Any` should be. |
| Cross-model `/codex` skill | Coupling analysis | `allowed-tools` includes `codex-reply`. Multi-turn permitted but one-shot by default. ~85% of consultation contract portable. Tight coupling in invocation strategy (~50 lines) and analytics schema. |

## Codebase Knowledge

### JSONL Replay Pattern (shared across 3 stores)

All three stores (`turn_store.py`, `lineage_store.py`, `journal.py`) share the same replay pattern:

```
open file → iterate lines → skip blank → json.loads → apply record
                                           ↓ fail: continue (silent discard)
```

They diverge on post-parse behavior:

| Store | Post-parse | Failure mode |
|-------|-----------|--------------|
| `turn_store.py:70` | `record['collaboration_id']` — bare key access | `KeyError` crashes entire replay |
| `lineage_store.py:110-127` | `if op == "create" ... elif ...` — no else | Unknown ops silently dropped |
| `journal.py:144` | `OperationJournalEntry(**record)` | `TypeError` on missing fields |

All three use `json.JSONDecodeError: continue` for corrupt lines — correct for trailing truncation but silent for mid-file corruption.

### Consult vs Dialogue Shared Infrastructure

| Dimension | Shared? | Evidence |
|-----------|---------|----------|
| Runtime bootstrap | Yes | Both use `_bootstrap_runtime` / `_probe_runtime` |
| Context assembly | Yes | `assemble_context_packet(profile="advisory")` |
| Prompt building | Yes | `build_consult_turn_text(payload, posture=posture)` |
| Output schema | Yes | `CONSULT_OUTPUT_SCHEMA` |
| Turn dispatch | Yes | `runtime.session.run_turn()` |
| Response parsing | Yes | `parse_consult_response()` |
| Profile resolution | Yes | `profiles.resolve_profile()` |

### Consult-Only Properties

| Property | Location | Purpose |
|----------|----------|---------|
| Ephemeral handle | `control_plane.py:188` — `collaboration_id = self._uuid_factory()` after turn, no lineage write | Fire-and-forget advisory |
| Zero journal writes | `control_plane.py:130-199` — no `write_phase()` calls | No crash recovery needed for one-shot |
| Stale-marker integration | `control_plane.py:145-153` — loads marker, injects summary, clears after success | Post-promotion coherence consumer |
| Fork-from-parent | `control_plane.py:169-170` — `fork_thread(parent_id)` if parent_id set | Branch from prior consultation's thread |
| Network policy gate | `control_plane.py:136-140` — pre-bootstrap enforcement | One-time advisory widening check |
| Policy fingerprint in audit | `control_plane.py:199` — `policy_fingerprint` in consult audit event | One-time snapshot context |

### Store Ownership Architecture

| Store | Owner | Location |
|-------|-------|----------|
| `OperationJournal` (journal + audit) | `ControlPlane` | `control_plane.py` — initialized at construction |
| `LineageStore` | `DialogueManager` | `dialogue.py:55` — initialized at construction |
| `TurnStore` | `DialogueManager` | `dialogue.py:55` — initialized at construction |

This ownership split means the control plane cannot directly call `check_health()` on lineage/turn stores without going through the dialogue layer or refactoring ownership. The design spec explicitly defers wiring a production health consumer because of this.

### Codex-Collaboration Spec Module Authority

| Authority | Module | Key files |
|-----------|--------|-----------|
| Delivery roadmap | `delivery.md` | Build sequence, milestones R1/R2, post-R2 packets, acceptance gates |
| Design decisions | `decisions.md` | Greenfield rules, tradeoffs, resolved/open questions |
| Interface contracts | `contracts.md` | MCP tool surface, data model, audit events, response shapes |
| Benchmark contract | `dialogue-supersession-benchmark.md` | Fixed-corpus benchmark for dialogue retirement decision |

`README.md:35` assigns authority. `delivery.md` is the canonical "what to build next, in what order, what counts as done" file.

### Roadmap Position of Deferred Items

| Item | Roadmap position | Classification |
|------|-----------------|----------------|
| I2/I3/I4 (persistence replay) | Adjacent to delivered R2 lineage/journal/turn-store | Debt work — not in any post-R2 packet |
| F4/F6 (type improvements) | Near packet 2b code areas but outside scope | Cleanup — not in any delivery milestone |
| AC6 (analytics emission) | Packet 2b in `delivery.md:255` and ticket T-20260330-03 | **Actual roadmap work** |

## Context

### Mental Model

This session was a **two-phase architectural evaluation** problem. Phase 1 tested whether a first-class tool should be retired — a convergence question with three hypothesis paths. Phase 2 designed a shared persistence substrate — a factoring question about where to draw the boundary between shared mechanism and per-store policy.

The core insight in Phase 1: shared code paths are necessary but not sufficient evidence for retirement. The consult/dialogue overlap (~70%) is real and already factored into shared helpers. The remaining ~30% consists of intentional contract-level properties, not accidental duplication. Retirement would either recreate those properties under a different name or force callers to accept inappropriate overhead.

The core insight in Phase 2: the three JSONL stores have identical *mechanism* (line iteration, parse, classify) but different *policy* (what's a valid record, how to apply it). The shared replay helper encodes this separation: mechanism in the helper, policy in callbacks.

### Project State

- **Branch:** `main` at `851560f6`
- **All T-03 deferred items classified:** persistence hardening (debt), type narrowing (cleanup), analytics (roadmap)
- **`codex.consult` open question:** Closed — last open question in `decisions.md` from the original spec compilation
- **Design spec ready:** `2026-03-31-persistence-hardening-and-type-narrowing-design.md` reviewed and merged
- **Tests:** 359/359 passing (unchanged from T-03 landing)

## Learnings

### Second review findings split into debt, cleanup, and roadmap work

**Mechanism:** The T-03 second review produced 4C/14I/16S findings. After fixing criticals and importants in the same session, the deferred items appeared homogeneous — all "things the review found." But mapping them against the canonical delivery roadmap at `delivery.md` reveals three distinct categories with different priority profiles.

**Evidence:** User mapped each item: I2/I3/I4 are "roadmap-adjacent debt on delivered R2 infrastructure," F4/F6 are "cleanup outside the main build sequence," and AC6 is "actual roadmap work in packet 2b." The handoff's next-steps ordering reflected session touch order, not roadmap priority.

**Implication:** When a review produces a batch of deferred items, classify each against the delivery roadmap before sequencing. The item with delivery milestone standing (AC6) was buried in the deferred items table despite being the only one that advances the build plan.

**Watch for:** Handoff next-steps lists that order by "what we just discussed" rather than "what matters to the build plan."

### Shared code paths are necessary but not sufficient evidence for tool retirement

**Mechanism:** `codex.consult` and `codex.dialogue` share ~70% of their code path (bootstrap, assembly, prompt, schema, dispatch, parsing). But the ~30% divergence consists of intentional contract-level properties: ephemeral handles, zero persistence, stale-marker integration, fork support, consultation-specific audit semantics.

**Evidence:** The code-path comparison agent found full sharing on 7 of 9 dimensions. But the step 2 analysis (skill coupling) and step 3 analysis (native review gates) both confirmed that retiring consult would either recreate those properties or degrade the caller experience.

**Implication:** When evaluating whether to merge two surfaces, test whether the divergences are accidental duplication (merge target) or intentional contract properties (keep separate). The merge question is about lifecycle and persistence semantics, not lines of code.

**Watch for:** Future proposals to "simplify" by merging consult into dialogue. The shared helpers are already factored — further unification would move semantics, not eliminate them.

### JSONL replay stores need explicit corruption classification, not blanket `continue`

**Mechanism:** All three stores use `except JSONDecodeError: continue` — correct for trailing truncation (crash-safe append semantics) but wrong for mid-file corruption. The spec at `contracts.md:119-121` only blesses "incomplete trailing records" as expected crash behavior. Non-trailing corruption is a data integrity signal being silently swallowed.

**Evidence:** `turn_store.py:68`, `lineage_store.py:99`, `journal.py:141` all use the same pattern. The distinction between trailing and mid-file requires knowing whether valid lines follow the corrupt one — a deferred classification that the current inline `continue` cannot express.

**Implication:** The shared replay helper's deferred classification algorithm (accumulate corrupt indices, classify at EOF based on last-valid-JSON position) is the minimum complexity needed to correctly implement the spec's trailing-record contract.

**Watch for:** Future stores that use append-only JSONL — they should use the shared helper rather than reimplementing the `try/except JSONDecodeError: continue` pattern.

## Next Steps

### 1. Write implementation plan from design spec

**Dependencies:** Design spec at `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` is merged and reviewed.

**What to read first:** The design spec itself. It contains the full replay contract, per-store callback specifications, diagnostic model, type narrowing details, and test plans.

**Approach suggestion:** Invoke the `writing-plans` skill against the design spec. The plan should produce two implementation sequences matching the two branches: `fix/persistence-replay-hardening` (incremental: helper → turn_store → lineage_store → journal) and `chore/type-narrowing` (F4 literals + F6 session type).

**Acceptance criteria:** Plan with numbered steps, file-level changes, and test verification gates. Each step independently verifiable (tests pass after each migration).

### 2. Implement persistence replay hardening (`fix/persistence-replay-hardening`)

**Dependencies:** Implementation plan from step 1.

**What to read first:**
- Design spec (full replay contract and per-store callbacks)
- `server/turn_store.py` (simplest store — migrate first)
- `server/lineage_store.py` (adds unknown-op handling)
- `server/journal.py` (adds dataclass construction validation)

**Approach suggestion:** Create `fix/persistence-replay-hardening` branch. Implement `server/replay.py` + `tests/test_replay.py` first (shared helper). Then migrate stores one at a time with tests. Run full suite after each migration.

**Acceptance criteria:** All existing 359 tests pass. New tests cover: trailing truncation, mid-file corruption, schema violation (missing fields, wrong types, bool-as-int, non-dict JSON), unknown operations, programmer-bug propagation, `check_health()` returns structured diagnostics.

### 3. Implement type narrowing (`chore/type-narrowing`)

**Dependencies:** Fix branch should be merged first (different revert boundaries).

**What to read first:**
- Design spec (F4 and F6 sections)
- `server/profiles.py:22-29` (current stringly-typed fields)
- `server/models.py:111-127` (current `session: Any`)

**Approach suggestion:** Create `chore/type-narrowing` branch. Define literal types, narrow `ResolvedProfile` and `resolve_profile()`, add runtime validation for YAML-loaded values (`posture`, `effort`, `turn_budget`). Then fix F6 with `TYPE_CHECKING` guard.

**Acceptance criteria:** All existing tests pass. New tests for: unknown posture rejection, unknown effort rejection, non-positive turn_budget, string turn_budget, bool turn_budget. Type checker passes on `session: AppServerRuntimeSession`.

### 4. (Future) Wire diagnostics consumer

**Dependencies:** Fix branch merged. Spec amendment to `contracts.md` §RuntimeHealth.

**What to read first:** Design spec's Deferred Work section. Store ownership architecture (control plane owns journal; dialogue owns lineage/turn stores).

**Approach suggestion:** Decide ownership model for cross-store health checks. Either push health checks through the dialogue layer, or promote store ownership to the control plane.

## In Progress

Clean stopping point. Design spec merged to main. No implementation branches exist yet. No code changes in flight. Working tree clean.

## Open Questions

### AC6 analytics emission

Deferred from T-03. Actual roadmap work in packet 2b (`delivery.md:255`). Not addressed this session — user chose persistence hardening first to solidify the R2 substrate.

### Diagnostics consumer architecture

The design spec defers wiring `check_health()` to a production surface. The store ownership split (control plane owns journal; dialogue owns lineage/turn stores) means no single component can call all three without refactoring. This needs a design decision before the consumer is wired.

### Deferred review suggestions (S1-S16)

16 suggestions from the T-03 second review agents were not independently validated by the user. They may contain false positives. Unchanged from prior handoff.

## Risks

### Design spec may need revision during implementation

The design spec was reviewed and approved, but implementation may surface gaps not visible at the design level. Particularly: the closure-captured accumulator pattern for lineage's callback, and the deferred trailing-truncation classification algorithm's behavior on edge cases.

### `check_health()` has no production consumer

Replay diagnostics are structured and testable, but operationally invisible. Mid-file corruption in production would be survivable (no crash) but undetected until behavior drifts. The design explicitly defers the consumer, but the gap should be closed before the stores handle real production data.

## References

| What | Where |
|------|-------|
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| `codex.consult` decision | `docs/superpowers/specs/codex-collaboration/decisions.md:115-141` |
| Delivery roadmap | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| Lineage store spec | `docs/superpowers/specs/codex-collaboration/contracts.md` §Lineage Store |
| Recovery/journal spec | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` |
| Prior handoff | `docs/handoffs/archive/2026-03-31_13-56_t03-safety-substrate-second-review-and-merge.md` |
| PR #90 (T-03) | jpsweeney97/claude-code-tool-dev#90 — squash-merged at `43fa3ba5` |

## Gotchas

### Store ownership split prevents centralized health checks

`ControlPlane` owns the `OperationJournal`. `DialogueManager` owns `LineageStore` and `TurnStore`. There is no single component that can call `check_health()` on all three stores. The design spec explicitly defers the consumer wiring because of this architectural constraint.

### `type(x) is int` not `isinstance(x, int)` for replay validation

Python's `bool` subclasses `int`. `isinstance(True, int)` returns `True`. JSON `true`/`false` would pass integer validation if `isinstance` is used. The design spec locks `type(x) is int` for all integer field checks in replay callbacks.

### Extra fields on known lineage ops are silently ignored (intentional)

This is forward-compatibility, not a bug. `lineage_store.py:117` already filters through `__dataclass_fields__`. The design spec adds the rule: "extra fields on known ops are additive metadata only; semantic changes require a new op value."

### `resolve_profile()` parameters are now typed — callers must use literals

After F4, passing `explicit_posture="adversrial"` (typo) to `resolve_profile()` will be a type error, not a runtime error. Code callers get static checking; YAML-loaded values get runtime validation. This is the intended split.

## User Preferences

**Hypothesis-driven evaluation:** User structured the `codex.consult` analysis as ranked hypotheses with evidence requirements and tests. Format: (1) hypothesis ranked by likelihood, (2) evidence needed, (3) tests to run. This matches the root cause analysis pattern in global CLAUDE.md.

**Tight evaluation gates:** User provided 5 specific gates for the native review comparison rather than leaving the criteria open-ended. "the burden is now on native review to beat 'keep consult,' not merely to match it."

**Roadmap-first prioritization:** User redirected from the handoff's next-steps ordering to the canonical delivery roadmap. "The canonical roadmap is delivery.md" — handoff next-steps are session-local recommendations, not roadmap authority.

**Incremental design review:** User reviewed each design section individually, providing findings with priority markers (P1/P2) and explicit locking instructions. Each round produced specific corrections rather than "looks good" responses.

**Design rigor over speed:** User caught 7+ gaps across the design iterations that would have been bugs in implementation: bool-as-int, extra-field policy, turn_budget validation, all-corrupt heuristic, compatibility boundary, check_health role, non-dict JSON. Pattern: user validates assumptions at the design level rather than discovering issues during implementation.
