# Context Injection Agent Integration — Planning Brief

**Date:** 2026-02-15
**Status:** Exploration complete, ready for plan writing
**Purpose:** Captures all findings from the pre-planning exploration session. The next session reads this document plus the decisions and exploration docs, then writes the implementation plan.
**Builds on:**
- Exploration document: `docs/plans/2026-02-15-context-injection-agent-integration.md`
- Decisions document: `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md`
- Protocol contract: `docs/references/context-injection-contract.md`
- Design spec: `docs/plans/2026-02-11-conversation-aware-context-injection.md`
- Codex-dialogue agent: `.claude/agents/codex-dialogue.md`

---

## 1. Server Codebase Architecture

### Module Organization (16 source modules, ~4,900 LOC)

| Module | Lines | Purpose |
|--------|-------|---------|
| `types.py` | 439 | Pydantic protocol models (frozen, strict, forbid extra) |
| `enums.py` | 123 | Protocol enum types (EntityType, Confidence, TemplateId, etc.) |
| `server.py` | 109 | FastMCP entry point, tool handlers, lifespan |
| `state.py` | 215 | AppContext, TurnRequestRecord, HMAC token gen/verify, bounded store |
| `pipeline.py` | 190 | Call 1 orchestration: schema validation → extract → paths → templates → budget → store |
| `templates.py` | 625 | Template matching, ranking, scout option synthesis, dedupe |
| `entities.py` | 495 | Regex-based entity extraction, span tracking, canonicalization |
| `execute.py` | 535 | Call 2 execution: read & grep pipelines, redaction, truncation |
| `paths.py` | 476 | Path canonicalization, denylist, git ls-files gating |
| `grep.py` | 342 | Ripgrep subprocess, JSON parsing, match grouping |
| `redact.py` | 223 | Redaction dispatcher: format classification → format-specific |
| `redact_formats.py` | 730 | JSON, YAML, TOML, PEM format-specific redaction |
| `truncate.py` | 222 | Excerpt truncation by char/line limits; block truncation for grep |
| `classify.py` | 82 | File type classification (extension-based) for redaction |
| `canonical.py` | 84 | Canonical JSON serialization (HMAC payload), entity keys |
| `__main__.py` / `__init__.py` | 6 | Entry points |

**Package location:** `packages/context-injection/context_injection/`

### Request Flow

**Call 1 (`process_turn`):** 7-step pipeline in `pipeline.py`:
1. Schema version validation (exact match for 0.x)
2. Entity extraction from `focus.claims` (in_focus=True) + `context_claims` (in_focus=False)
3. Path checking (compile-time: canonicalize → containment → denylist → git ls-files)
4. Template matching (hard gates: Tier 1 + high/medium confidence + in_focus + path allowed)
5. Budget computation (evidence_count from evidence_history)
6. Store TurnRequest + spec_registry for Call 2
7. Assemble TurnPacketSuccess

**Entry:** `server.process_turn_tool()` → `pipeline.process_turn(request, app_ctx)`

**Call 2 (`execute_scout`):** Atomic verification then action-specific execution in `execute.py`:
1. Lookup turn_request_ref in store
2. Lookup scout_option_id in registry
3. HMAC verify (constant-time comparison)
4. Check replay (used bit)
5. Mark used
6. Execute read (redact → truncate → evidence) or grep (rg subprocess → filter → redact → truncate → evidence)

**Entry:** `server.execute_scout_tool()` → `execute.execute_scout(app_ctx, request)`

### State Management

```
AppContext:
  hmac_key: bytes (32 bytes, random per process)
  repo_root: str
  store: OrderedDict[str, TurnRequestRecord] (max 200, oldest-eviction)
  git_files: set[str] (from git ls-files at startup)
  entity_counter: int (monotonic)

TurnRequestRecord:
  turn_request: TurnRequest (frozen)
  scout_options: dict[option_id → ScoutOptionRecord]
  used: bool (one-shot)

ScoutOptionRecord (frozen):
  spec: ReadSpec | GrepSpec
  token: str (HMAC)
  template_id, entity_id, entity_key, risk_signal, path_display, action
```

### Test Structure (20 modules, 675 test functions)

| Category | Files | Tests |
|----------|-------|-------|
| Redaction pipeline | 6 (test_redact*.py) | 229 |
| Core pipeline | 3 (test_pipeline, entities, templates) | 108 |
| Scout execution | 2 (test_execute, test_grep) | 108 |
| Path handling | 1 (test_paths) | 74 |
| Types & enums | 2 (test_types, test_enums) | 53 |
| State/HMAC | 3 (test_state, test_server, test_single_flight) | 29 |
| Utilities | 4 (canonical, classify, truncate, integration) | 94 |

**Test patterns:**
- Helper constructors: `_make_turn_request(**overrides)`, `_make_ctx(**overrides)`
- Heavy parametrization for redaction format coverage
- Footgun tests: verify security boundaries
- Integration tests: full Call 1 → Call 2 round trips
- Mock subprocess (grep), file I/O (redaction)

---

## 2. Agent Structure (324 lines)

Three-phase architecture in `.claude/agents/codex-dialogue.md`:

- **Phase 1 (Setup):** Parse prompt → choose posture → assemble briefing → send to Codex
- **Phase 2 (Loop — rewrite target):** Per-turn: update ledger → choose follow-up → decide continue/conclude
- **Phase 3 (Synthesis):** Walk ledger entries → build confidence-annotated output

### Phase 2 Current Mechanics

**Ledger entry (8 fields per turn):**
- position (1-2 sentence summary of Codex's key point)
- claims (each with status: new/reinforced/revised/conceded)
- delta (advancing/shifting/static — single-label, required)
- tags (0-2 from: challenge, concession, tangent, new_reasoning, expansion, restatement)
- counters (new_claims, revised, conceded, unresolved_closed — mechanically derived)
- quality (derived: any counter > 0 → substantive; all zero → shallow)
- next (what to probe/challenge/build on)
- unresolved (questions opened or left unanswered)

**Continue/conclude rules:**
- Continue if: last turn advancing/shifting AND unresolved non-empty, OR unprobed claims exist, OR budget remaining AND last 2 not both static
- Conclude if: last 2 both static AND unresolved empty/stable AND closing probe fired, OR budget exhausted
- Closing probe: before concluding on plateau, fire "final position on [highest-priority unresolved]?"

**Follow-up priority:**
1. Unresolved items from current turn
2. Claims tagged `new` not yet probed
3. Weakest claim in ledger
4. Posture-driven probe

**What changes in 0.2.0:**
- Agent extracts semantic fields only (position, claims, delta, tags, unresolved)
- Server validates, derives counters/quality/effective_delta, stores cumulative state
- Server returns action (continue/closing_probe/conclude) — agent doesn't decide
- Agent adds `process_turn` and `execute_scout` MCP calls to the loop
- Agent passes checkpoint opaquely each turn

---

## 3. Critical Coupling: Entity Extraction and context_claims

The entity extraction pipeline (`entities.py`) currently gets its inputs from:
- `request.focus.claims` → entities with `in_focus: True`
- `request.context_claims` → entities with `in_focus: False`

In 0.2.0, `context_claims` is removed from TurnRequest. Entity extraction must instead read cumulative claims from server-internal state (ConversationState). This means:

- `pipeline.py` step 2 must change: pass `conversation_state.get_cumulative_claims()` instead of `request.context_claims`
- `entities.py` interface: accepts claims list directly, not field from TurnRequest
- **The schema migration and pipeline integration are tightly coupled** — can't change types without changing pipeline logic simultaneously

### Implication for Delivery Sequencing

New modules (ledger validation, conversation state, conversation control) can be built as pure additive modules with no existing code changes. But the final integration delivery (D4) must do the schema swap + pipeline rewiring + test migration together. This is the concentrated risk.

---

## 4. Resolved Design Questions

### Follow-up priority selection — Keep agent-side

The TurnPacket already returns `validated_entry` (claims/unresolved lists) and `cumulative` (running totals). The agent reconstructs the priority list from these fields. Adding explicit `follow_up_candidates` to TurnPacket would be redundant. The final selection requires conversational judgment (agent's strength).

### Ledger summary design — Structured text block

One line per turn + state line + trajectory:

```
T1: [position summary] (effective_delta, tags) — [key claim/outcome]
T2: ...
State: 12 claims (5 reinforced, 2 revised, 1 conceded), 3 unresolved
Trajectory: advancing → advancing → shifting → static
```

~30-50 tokens per turn summary line. 8 turns ≈ 300-400 tokens. Generated from stored ledger history.

### Focus selection ownership — Stay with agent for MVP

The server provides ranked unresolved items (by age and mention frequency) in the cumulative state. The agent decides which to focus on based on conversational judgment. Can move server-side later if ranking proves sufficient.

### Checkpoint emission timing — In TurnPacket (after process_turn)

Accept the two-call atomicity gap as non-critical. If the server restarts between `process_turn` and `execute_scout`:
- Checkpoint preserves the ledger entry
- Loses the in-flight scout
- Budget off by at most 1 (conservative direction — agent can do one more scout than expected)
- The ScoutResult already returns updated budget from the server's perspective

---

## 5. Proposed Delivery Structure

Five deliveries, sequenced by dependency:

### D1: Ledger Validation (~200-300 new tests)
**Risk: Low — pure additive**

New `ledger.py` module:
- Pydantic types: `LedgerEntry`, `ValidationWarning`, `CumulativeState`
- New enums: `EffectiveDelta`, `ValidationTier`
- `validate_ledger_entry()`: three-tier validation
  - Hard reject: missing fields, wrong types, invalid enums, turn sequencing errors
  - Soft warn: empty position, delta/counter mismatch, suspicious tag combos
  - Referential warn: claim marked "reinforced" but no prior similar claim
- `compute_counters()`: derive new_claims, revised, conceded, unresolved_closed from claim statuses
- `compute_quality()`: any counter > 0 → substantive; all zero → shallow
- `compute_effective_delta()`: new_claims > 0 → advancing; revised/conceded > 0 → shifting; else → static
- Tests: test_ledger.py covering all validation tiers, counter derivation, effective_delta rules

**No existing code changes.** Pure new module.

### D2: Conversation State Management (~100-150 new tests)
**Risk: Low — pure additive**

Extend `state.py` with `ConversationState`:
- Per-conversation claim registry (cumulative, ordered by insertion)
- Evidence history tracking (auto-recorded from successful scouts)
- Turn sequence (list of validated LedgerEntry per turn)
- Methods: `record_turn()`, `get_cumulative_claims()`, `get_evidence_history()`, `compute_cumulative_state()`

New `checkpoint.py` module:
- `StateCheckpoint` model: checkpoint_id, parent_checkpoint_id, format_version, payload, size
- `serialize_checkpoint()`: compact JSON with 8-16 KB size cap
- `deserialize_checkpoint()`: with chain validation
  - Verify parent_checkpoint_id matches expected chain
  - Reject stale/replay (checkpoint_id already seen)
  - Verify format_version compatibility
- Recovery error codes: `checkpoint_missing`, `checkpoint_invalid`, `checkpoint_stale`
- `compact_ledger()`: rolling aggregation when approaching size cap

Extend `AppContext` with `conversations: dict[str, ConversationState]` (keyed by conversation_id).

**No existing code changes.** Additive to state.py + new checkpoint.py module.

### D3: Conversation Control + Ledger Summary (~50-80 new tests)
**Risk: Low — pure additive**

New `conversation_control.py` module:
- `ConversationAction` enum: `continue`, `closing_probe`, `conclude`
- `compute_action()`: decision logic from effective_delta sequence + unresolved state + turn budget
  - Last 2 effective_deltas both static → plateau detected
  - Plateau + unresolved empty/stable + closing probe fired → conclude
  - Budget exhausted → conclude
  - Otherwise → continue
  - Plateau detected but closing probe not fired → closing_probe
- `format_action_reason()`: human-readable explanation

Ledger summary generation (in `ledger.py` or separate):
- `generate_ledger_summary()`: compact text from stored turn history
- One line per turn: position + effective_delta + tags + key outcome
- State line: cumulative counters
- Trajectory line: effective_delta sequence
- Target: 300-400 tokens for 8 turns

**No existing code changes.** Pure new module(s).

### D4: Schema 0.2.0 + Pipeline Integration (~50 new tests + update ~739 existing)
**Risk: HIGH — big integration delivery**

#### Types changes (`types.py`, `enums.py`):
- TurnRequest 0.2.0: add `position`, `claims` (top-level), `delta`, `tags`, `unresolved` (top-level), `state_checkpoint`, `checkpoint_id`, `parent_checkpoint_id`; remove `context_claims`, `evidence_history`
- TurnPacketSuccess 0.2.0: add `validated_entry`, `warnings`, `cumulative`, `action`, `action_reason`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`
- ScoutRequest 0.2.0: update schema_version
- Schema version constant: `"0.1.0"` → `"0.2.0"`
- New Literal type alias for 0.2.0

#### Pipeline changes (`pipeline.py`):
- Step 2 (entity extraction): use `conversation_state.get_cumulative_claims()` for in_focus=False entities instead of `request.context_claims`
- Step 4 (template matching): use `conversation_state.get_evidence_history()` for dedupe instead of `request.evidence_history`
- Step 5 (budget): use `conversation_state.evidence_count` instead of `len(request.evidence_history)`
- New step after entity extraction: validate ledger entry (call D1 validation)
- New step: compute conversation control action (call D3)
- New step: generate checkpoint (call D2)
- New step: generate ledger summary (call D3)
- Enhanced TurnPacketSuccess response with all new fields

#### Execute changes (`execute.py`):
- After successful scout: auto-record in `conversation_state.evidence_history`
- Budget computation from conversation_state instead of request

#### Test migration:
- All existing tests: update `schema_version` to `"0.2.0"`
- Tests using `context_claims`: replace with ConversationState setup (pre-populate claims in server state)
- Tests using `evidence_history`: replace with ConversationState setup
- Tests constructing TurnRequest: add required new fields (position, delta, tags, etc.)
- Helper function: `_make_turn_request_v2(**overrides)` with sensible defaults
- New integration tests: full 0.2.0 round-trip with ledger entries

#### Protocol contract update:
- `docs/references/context-injection-contract.md`: update schemas, add new sections for ledger validation, conversation control, checkpoints

### D5: Agent Rewrite
**Risk: Medium — high-stakes but small surface**

Rewrite `.claude/agents/codex-dialogue.md` Phase 2:
- Add `mcp__context-injection__process_turn` and `mcp__context-injection__execute_scout` to tool list
- Replace 3-step loop with server-assisted loop:
  1. Get Codex response
  2. Extract semantic data (position, claims, delta, tags, unresolved) — agent's strength
  3. Call `process_turn` with extracted data + checkpoint
  4. Receive: validated_entry + cumulative + action + scout options + ledger summary + new checkpoint
  5. If scout warranted: call `execute_scout`
  6. Compose follow-up based on action, scout evidence, posture, ledger summary
  7. Send follow-up to Codex
- Remove rule-following instructions for counters, quality, continue/conclude
- Replace with semantic extraction instructions (what to extract, not how to derive)
- Add checkpoint pass-through (store from TurnPacket, send in next TurnRequest)
- Update Phase 3 synthesis with evidence trajectory

---

## 6. Modules Unchanged by This Work

The following modules have no logic changes across all 5 deliveries:
- `redact.py`, `redact_formats.py` — all redaction
- `paths.py` — path checking (compile-time and runtime)
- `truncate.py` — excerpt truncation
- `grep.py` — ripgrep subprocess execution
- `classify.py` — file type classification
- `canonical.py` — JSON serialization, entity keys
- `templates.py` — template matching (still operates on entities + evidence, just sourced differently)

---

## 7. Estimated New Test Coverage

| Delivery | New Tests | Test Module(s) |
|----------|-----------|----------------|
| D1 | 200-300 | `test_ledger.py` |
| D2 | 100-150 | `test_conversation_state.py`, `test_checkpoint.py` |
| D3 | 50-80 | `test_conversation_control.py` |
| D4 | ~50 new + ~739 updated | `test_integration.py` updates, existing test migrations |
| D5 | Manual testing | Agent behavior validation |
| **Total** | ~400-580 new + ~739 updated | |

---

## 8. Key Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| D4 test migration is large (739 tests) | Mechanical change: schema_version string + helper constructor. Script-assisted. |
| Entity extraction coupling with context_claims removal | D4 handles both together — pipeline rewiring and type changes in same delivery |
| Agent rewrite (D5) breaks conversation quality | D5 is last — server is proven before agent changes. Agent tested against real Codex dialogues. |
| Checkpoint size grows beyond context budget | 8-16 KB hard limit with rolling compaction. Estimated 200-500 tokens for 5-8 turn conversation. |
| effective_delta rules too coarse | Rules are mechanical starting point. Agent's advisory delta stored for future refinement. |

---

## 9. References

| What | Where |
|------|-------|
| Decisions (5 locked) | `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md` |
| Exploration (problem + architecture) | `docs/plans/2026-02-15-context-injection-agent-integration.md` |
| Protocol contract (0.1.0) | `docs/references/context-injection-contract.md` |
| Design spec (scouting loop) | `docs/plans/2026-02-11-conversation-aware-context-injection.md` |
| Codex-dialogue agent | `.claude/agents/codex-dialogue.md` |
| MCP server codebase | `packages/context-injection/` |
| Cross-model learning spec | `docs/plans/2026-02-10-cross-model-learning-system.md` |
