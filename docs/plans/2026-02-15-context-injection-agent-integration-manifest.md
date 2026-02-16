# Context Injection Agent Integration — Plan Manifest

**Goal:** Upgrade the context injection MCP server from "scout executor" to "conversation controller" — server owns ledger state, validates entries, computes derived fields, and makes continue/conclude decisions.

**Architecture:** Server-owned ledger state with "separate language from state" principle. Agent becomes the language layer (semantic extraction + judgment), server becomes the state layer (validation + derivation + decisions).

**Tech Stack:** Python 3.12, Pydantic v2 (frozen/strict/forbid-extra), FastMCP, pytest, ripgrep

**References:**
- Planning brief: `docs/plans/2026-02-15-context-injection-agent-integration-planning-brief.md`
- Decisions (5 locked): `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md`
- Exploration: `docs/plans/2026-02-15-context-injection-agent-integration.md`
- Design spec: `docs/plans/2026-02-11-conversation-aware-context-injection.md`
- Protocol contract (0.1.0): `docs/references/context-injection-contract.md`
- Original plan (archive): `2026-02-15-context-injection-agent-integration-plan.md` (commit `34c4f2c`)

**Branch:** Create `feature/context-injection-agent-integration` from `main`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Dependency Graph

```
D1 (Ledger Validation) ─────┬──→ D4a (Schema 0.2.0) ──→ D4b (Pipeline + Test Migration) ──→ D5 (Agent Rewrite)
D2 (Conversation State) ────┤
D3 (Conversation Control) ──┘
```

- D1: independent (new modules + one extraction in `types.py`)
- D2: depends on D1 (uses LedgerEntry, CumulativeState types)
- D3: depends on D1 only (pure functions on D1 types — NOT on D2's ConversationState)
- D4a: depends on D1 + D2 + D3 (incorporates all new types into 0.2.0 schema)
- D4b: depends on D4a (pipeline uses 0.2.0 types)
- D5: depends on D4b (agent uses 0.2.0 protocol)

## Execution Order

D1 → D3 → D2 → D4a → D4b → D5

D3 before D2: momentum ordering — D3 is smaller/simpler and provides early validation of D1 types.

## Delivery Index

| Order | Delivery | Document | Tasks | Status |
|-------|----------|----------|-------|--------|
| 1 | D1: Ledger Validation | [`...-d1-ledger-validation.md`](2026-02-15-context-injection-agent-integration-d1-ledger-validation.md) | 1-4 | Pending |
| 2 | D3: Conversation Control | [`...-d3-conversation-control.md`](2026-02-15-context-injection-agent-integration-d3-conversation-control.md) | 9-10 | Pending |
| 3 | D2: Conversation State | [`...-d2-conversation-state.md`](2026-02-15-context-injection-agent-integration-d2-conversation-state.md) | 5-8 | Pending |
| 4 | D4a: Schema 0.2.0 | [`...-d4a-schema-020.md`](2026-02-15-context-injection-agent-integration-d4a-schema-020.md) | 11-12 | Pending |
| 5 | D4b: Pipeline + Execute | [`...-d4b-pipeline-execute-test-migration.md`](2026-02-15-context-injection-agent-integration-d4b-pipeline-execute-test-migration.md) | 13a, 13b, 14 | Pending |
| 6 | D5: Agent Rewrite | [`...-d5-agent-rewrite.md`](2026-02-15-context-injection-agent-integration-d5-agent-rewrite.md) | 15 | Pending |

## Review Gates

| After | Verify |
|-------|--------|
| D1 | Ledger types compile, all D1 tests pass, counter/quality/delta computation is deterministic |
| D3 | Control functions work on D1 types, D3 tests pass, functions are pure (no side effects) |
| D2 | ConversationState works, checkpoint chain validates, compaction preserves invariants, compaction contract documented, D2 tests pass |
| D4a | 0.2.0 types defined; all new type tests pass; all 739 existing tests collect and execute (no import/construction errors); remaining semantic failures marked `xfail(strict=True)` with D4b task mapping; xfail inventory committed; no pipeline/execute/server changes |
| D4b | Pipeline rewired, turn-cap invariant enforced, guard tested, all tests pass (existing + new), protocol contract updated |
| D5 | Agent rewrite complete, Phase 2 uses `process_turn` and `execute_scout`, Phase 1/3 preserved |

## Contingency: D4c Split

If D4b (~971 lines) exceeds subagent context budget during execution, split Task 14 (Integration tests + protocol contract) into a separate D4c delivery.

**Trigger criteria:**
- After Tasks 13a + 13b complete, first full test run has >25 failures across 4+ modules
- Two consecutive fix passes still miss items from a fixed checklist: checkpoint ingestion, prospective-state commit, evidence auto-recording, contract doc, integration assertions

**D4c scope (if triggered):** Task 14 only (~241 lines), run after D4b Tasks 13a + 13b complete.

## Resolved Questions (Canonical)

These were resolved during Codex consultation (thread `019c62da`):

1. **match_templates internal access:** Does NOT read `turn_request.context_claims` or `turn_request.evidence_history`. Only uses `turn_request.conversation_id` and `turn_request.turn_number` for HMAC token payloads (templates.py:280-281, 339-340). **templates.py is unchanged in D4.**

2. **Pipeline signature:** Locked to option (a) — `process_turn(request, ctx)` unchanged. Pipeline resolves conversation internally via `ctx.get_or_create_conversation(request.conversation_id)`. Keeps public API stable.

3. **D3 parameter design:** Keep D3 functions pure on D1 types (not ConversationState). Pipeline extracts data and passes it. Decoupling enables D2/D3 parallelism.

4. **Checkpoint ingestion gap:** Original plan omitted checkpoint intake from D4 pipeline. Now explicit in Task 13a step 3 and D2 Task 7 validation policy.

5. **Prospective state pattern:** Pipeline builds a projected ConversationState via `with_turn()`, computes all derived fields from it, then commits atomically by replacing the dict entry. No partial mutations.

## Operational Assumptions

This plan assumes the following runtime characteristics. If any assumption changes, the affected design decisions and guards must be revisited.

| Assumption | Implication | Revisit trigger |
|------------|-------------|-----------------|
| **Single-agent** | One Claude Code agent per MCP session; no concurrent agents sharing server state | Multi-agent orchestration |
| **Single-flight** | One `process_turn` or `execute_scout` call in flight at a time per conversation | Parallel tool calls within a conversation |
| **Short-lived MCP server process** | Server process lifetime matches the Claude Code session (~5-30 min); `AppContext.conversations` dict stays small (1-3 entries) | Cross-session process reuse, persistent MCP servers |

These assumptions justify: no conversation eviction policy (DD-3), no disk persistence for state (Decision 1), and the compaction non-trigger invariant (DD-2).

## Final Verification

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All tests pass (~739 existing updated + ~400-580 new)

Run: `cd packages/context-injection && ruff check context_injection/ tests/`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `context_injection/base_types.py` | New | Shared base types (`ProtocolModel`, `Claim`, `Unresolved`) — breaks import cycle between `types.py` and `ledger.py` |
| `context_injection/ledger.py` | New | Ledger types, validation, counter/quality/delta computation |
| `context_injection/conversation.py` | New | ConversationState (per-conversation ledger + claim registry) |
| `context_injection/checkpoint.py` | New | Checkpoint serialization, chain validation, compaction |
| `context_injection/control.py` | New | Conversation action computation, ledger summary generation |
| `context_injection/types.py` | Modified | D1: extract base types + re-export; D4a: TurnRequest/TurnPacket 0.2.0 schema |
| `context_injection/enums.py` | Modified | EffectiveDelta, QualityLabel, ValidationTier, new error codes |
| `context_injection/pipeline.py` | Modified | Rewired to use ConversationState, new validation/control steps |
| `context_injection/execute.py` | Modified | Auto-record evidence, budget from ConversationState |
| `context_injection/state.py` | Modified | AppContext.conversations dict |
| `context_injection/server.py` | Modified | Minimal — pipeline resolves conversation internally |
| `tests/test_ledger.py` | New | D1 validation tests |
| `tests/test_conversation.py` | New | D2 state management tests |
| `tests/test_checkpoint.py` | New | D2 checkpoint tests |
| `tests/test_control.py` | New | D3 control + summary tests |
| `tests/test_types.py` | Modified | D1: re-export identity tests; D4a: schema 0.2.0 migration |
| `tests/test_*.py` (5 other existing) | Modified | Schema 0.2.0 migration |
| `pyproject.toml` | Modified | D4b: package version bump to 0.2.0, Python floor annotation |
| `docs/references/context-injection-contract.md` | Modified | 0.2.0 protocol contract |
| `.claude/agents/codex-dialogue.md` | Modified | Phase 2 rewrite (7-step loop) |
