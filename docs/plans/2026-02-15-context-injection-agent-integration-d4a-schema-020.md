# D4a: Schema 0.2.0 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D4a of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Define TurnRequest/TurnPacket 0.2.0 types incorporating D1/D2/D3 types, and migrate existing test shapes to the new schema.
**Execution order position:** 4 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

**Requires from D1:**
- `LedgerEntry`, `CumulativeState`, `LedgerEntryCounters`, `EffectiveDelta`, `QualityLabel`, `ValidationTier` from `context_injection/ledger.py`
- Enums from `context_injection/enums.py`
- `ProtocolModel`, `Claim`, `Unresolved` extracted to `context_injection/base_types.py` (DD-1: import cycle resolution). `types.py` re-exports these — existing import paths unchanged.
- Source of truth: `context_injection/base_types.py`, `context_injection/ledger.py`, `context_injection/enums.py`

**Requires from D2 (runtime/semantic dependency — D4a does not import D2 modules directly, but 0.2.0 types embed D2-defined types as fields):**
- `ConversationState` from `context_injection/conversation.py` — embedded in TurnPacketSuccess
- Checkpoint types from `context_injection/checkpoint.py` — checkpoint serialization contract
- Source of truth: `context_injection/conversation.py`, `context_injection/checkpoint.py`

**Requires from D3:**
- `ConversationAction` from `context_injection/control.py`
- `generate_ledger_summary(entries, cumulative) -> str` function from `context_injection/control.py`
- Source of truth: `context_injection/control.py`

**Critical invariants:**
- All D1/D2/D3 modules must be complete and tested before this delivery
- No wire-level backward compatibility: only 0.2.0 is accepted. Compatibility goal is test infrastructure migration (existing helpers compile with new fields), not dual-schema runtime support.

**Adaptation:** If D1/D2/D3 type names differ from this plan, adapt type references and note the mapping.

## Files in Scope

**Create:** None.

**Modify:**
- `context_injection/types.py` — TurnRequest/TurnPacket 0.2.0 schema
- `context_injection/enums.py` — Additional enums if needed
- `tests/test_*.py` (6 existing test files) — Test shape migration to 0.2.0

**Out of scope:** All files not listed above. In particular, do NOT modify `context_injection/pipeline.py`, `context_injection/execute.py`, or `context_injection/server.py` (those are D4b).

## Done Criteria

- All new 0.2.0 type tests pass
- All 739 existing tests collect and execute (no import errors, no construction errors)
- Semantic failures marked with `pytest.mark.xfail(strict=True, reason="D4b: <cause> (Task 13a|13b|14)")`
- Xfail inventory committed at `packages/context-injection/tests/xfail_inventory_d4a.md`
- No changes to `pipeline.py`, `execute.py`, or `server.py`

## Scope Boundary

This document covers D4a only. After completing all tasks in this delivery, stop. Do not proceed to D4b or subsequent deliveries.

---

Two tasks: 11 (0.2.0 types) and 12 (test shape migration). Tasks 13a/13b/14 are in D4b.

**Estimated:** ~50 new tests + ~739 updated
**Depends on:** D1 + D2 + D3 complete
**Risk:** MEDIUM — type changes are self-contained; semantic failures deferred to D4b

**Commit strategy:** Tasks 11+12 commit together (type changes + test helpers are inseparable).

### Task 11: TurnRequest/TurnPacket 0.2.0 types

**Files:**
- Modify: `context_injection/types.py`
- Modify: `tests/test_types.py`

This task changes the wire protocol types. TurnRequest gains ledger fields (position, claims, delta, tags, unresolved) and checkpoint fields, loses context_claims and evidence_history. TurnPacketSuccess gains validated_entry, warnings, cumulative state, action/summary, and checkpoint. ErrorDetail gains codes for ledger validation and checkpoint errors.

**Step 1: Write failing tests for new TurnRequest fields**

Add to `tests/test_types.py`:

```python
class TestTurnRequest020:
    """0.2.0 TurnRequest field changes."""

    def test_new_required_fields(self) -> None:
        """TurnRequest requires position, claims, delta, tags, unresolved."""
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Initial analysis",
            claims=[],
            delta="static",
            tags=["architecture"],
            unresolved=[],
        )
        assert request.position == "Initial analysis"
        assert request.claims == []
        assert request.delta == "static"
        assert request.tags == ["architecture"]
        assert request.unresolved == []

    def test_checkpoint_fields_optional(self) -> None:
        """Checkpoint fields default to None."""
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Initial analysis",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
        )
        assert request.state_checkpoint is None
        assert request.checkpoint_id is None

    def test_checkpoint_fields_set(self) -> None:
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=2,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Follow-up",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
            state_checkpoint='{"checkpoint_id":"abc"}',
            checkpoint_id="abc",
        )
        assert request.state_checkpoint == '{"checkpoint_id":"abc"}'
        assert request.checkpoint_id == "abc"

    def test_context_claims_removed(self) -> None:
        """context_claims field no longer accepted (extra=forbid)."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version=SCHEMA_VERSION,
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="static",
                tags=[],
                unresolved=[],
                context_claims=[],
            )

    def test_evidence_history_removed(self) -> None:
        """evidence_history field no longer accepted (extra=forbid)."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version=SCHEMA_VERSION,
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="static",
                tags=[],
                unresolved=[],
                evidence_history=[],
            )
    def test_invalid_delta_rejected(self) -> None:
        """Pre-canonical delta values (high/medium/low) are no longer valid."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version=SCHEMA_VERSION,
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="static",
                tags=[],
                unresolved=[],
            )
```

Add tests for TurnPacketSuccess changes:

```python
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    ValidationWarning,
)


class TestTurnPacketSuccess020:
    """0.2.0 TurnPacketSuccess new fields."""

    def test_new_fields_present(self) -> None:
        """TurnPacketSuccess includes validated_entry, warnings, cumulative, action, checkpoint."""
        entry = LedgerEntry(
            position="test",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
            counters=LedgerEntryCounters(
                new_claims=0, revised=0, conceded=0, unresolved_closed=0,
            ),
            quality="substantive",
            effective_delta="advancing",
            turn_number=1,
        )
        cumulative = CumulativeState(
            total_claims=0, reinforced=0, revised=0, conceded=0,
            unresolved_open=0, unresolved_closed=0, turns_completed=1,
            effective_delta_sequence=["advancing"],
        )
        packet = TurnPacketSuccess(
            schema_version=SCHEMA_VERSION,
            status="success",
            entities=[],
            path_decisions=[],
            template_candidates=[],
            budget=Budget(
                evidence_count=0, evidence_remaining=3,
                scout_available=True, budget_status="under_budget",
            ),
            deduped=[],
            validated_entry=entry,
            warnings=[],
            cumulative=cumulative,
            action="continue_dialogue",
            action_reason="Conversation active",
            ledger_summary="T1: test (advancing)\nState: 0 claims",
            state_checkpoint='{"checkpoint_id":"abc"}',
            checkpoint_id="abc",
        )
        assert packet.validated_entry == entry
        assert packet.warnings == []
        assert packet.cumulative == cumulative
        assert packet.action == "continue_dialogue"
        assert packet.checkpoint_id == "abc"


class TestTurnPacketCheckpointRequired:
    """TurnPacketSuccess requires state_checkpoint and checkpoint_id with no defaults."""

    def test_turn1_checkpoint_required(self) -> None:
        """Even turn 1 must produce a checkpoint — no defaults on these fields."""
        with pytest.raises(ValidationError):
            TurnPacketSuccess(
                schema_version=SCHEMA_VERSION,
                status="success",
                entities=[],
                path_decisions=[],
                template_candidates=[],
                budget=Budget(
                    evidence_count=0, evidence_remaining=3,
                    scout_available=True, budget_status="under_budget",
                ),
                deduped=[],
                validated_entry=LedgerEntry(
                    position="test", claims=[], delta="static", tags=[],
                    unresolved=[], counters=LedgerEntryCounters(
                        new_claims=0, revised=0, conceded=0, unresolved_closed=0,
                    ),
                    quality="substantive", effective_delta="advancing", turn_number=1,
                ),
                warnings=[],
                cumulative=CumulativeState(
                    total_claims=0, reinforced=0, revised=0, conceded=0,
                    unresolved_open=0, unresolved_closed=0, turns_completed=1,
                    effective_delta_sequence=["advancing"],
                ),
                action="continue_dialogue",
                action_reason="Conversation active",
                ledger_summary="T1: test (advancing)",
                # state_checkpoint and checkpoint_id omitted — should fail
            )


class TestErrorDetail020:
    """0.2.0 ErrorDetail new codes."""

    @pytest.mark.parametrize("code", [
        "ledger_hard_reject",
        "checkpoint_missing",
        "checkpoint_invalid",
        "checkpoint_stale",
        "turn_cap_exceeded",
    ])
    def test_new_error_codes_accepted(self, code: str) -> None:
        error = ErrorDetail(code=code, message="test")
        assert error.code == code

    def test_existing_codes_still_work(self) -> None:
        for code in ["invalid_schema_version", "missing_required_field",
                      "malformed_json", "internal_error"]:
            error = ErrorDetail(code=code, message="test")
            assert error.code == code
```

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestTurnRequest020 tests/test_types.py::TestTurnPacketSuccess020 tests/test_types.py::TestErrorDetail020 -v`
Expected: FAIL — fields don't exist yet

**Step 2: Write failing test for schema version change**

Add to `tests/test_types.py`:

```python
class TestSchemaVersion020:
    """Schema version updated to 0.2.0."""

    def test_schema_version_constant(self) -> None:
        assert SCHEMA_VERSION == "0.2.0"

    def test_valid_version_accepted(self) -> None:
        request = TurnRequest(
            schema_version="0.2.0",
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="test",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
        )
        assert request.schema_version == "0.2.0"

    def test_old_version_rejected(self) -> None:
        """0.1.0 is no longer valid."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version="0.1.0",
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="static",
                tags=[],
                unresolved=[],
            )
```

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestSchemaVersion020 -v`
Expected: FAIL

**Step 3: Implement type changes**

Modify `context_injection/types.py`:

1. Update schema version:
```python
SchemaVersionLiteral = Literal["0.2.0"]
SCHEMA_VERSION: SchemaVersionLiteral = "0.2.0"
```

2. Update TurnRequest — add new fields, remove old:
```python
class TurnRequest(ProtocolModel):
    """Call 1 input: agent sends focus-scoped ledger data."""

    schema_version: SchemaVersionLiteral
    turn_number: int
    conversation_id: str
    focus: Focus
    posture: Literal["adversarial", "collaborative", "exploratory", "evaluative"]

    # --- 0.2.0: Ledger fields (top-level for validation) ---
    position: str
    claims: list[Claim]
    delta: Literal["advancing", "shifting", "static"]
    tags: list[str]
    unresolved: list[Unresolved]

    # --- 0.2.0: Checkpoint fields (optional — absent on turn 1) ---
    state_checkpoint: str | None = None
    checkpoint_id: str | None = None
```

Note: `context_claims` and `evidence_history` are REMOVED (not defaulted). Since ProtocolModel uses `extra="forbid"`, sending them will error.

3. Update ErrorDetail — add new codes:
```python
class ErrorDetail(ProtocolModel):
    """Error details in a TurnPacket error response."""

    code: Literal[
        "invalid_schema_version",
        "missing_required_field",
        "malformed_json",
        "internal_error",
        "ledger_hard_reject",
        "checkpoint_missing",
        "checkpoint_invalid",
        "checkpoint_stale",
        "turn_cap_exceeded",
    ]
    message: str
    details: dict | None = None
```

4. Update Budget — add `budget_status` field:
```python
class Budget(ProtocolModel):
    """Evidence budget status."""

    evidence_count: int
    evidence_remaining: int
    scout_available: bool
    budget_status: Literal["under_budget", "at_budget", "over_budget"]
```

5. Update TurnPacketSuccess — add new fields:

> **Import cycle note (DD-1):** This `types.py → ledger.py` import is cycle-safe because `ledger.py` imports `ProtocolModel`, `Claim`, and `Unresolved` from `base_types.py` (not from `types.py`). The import DAG is: `base_types.py` → `ledger.py` + `types.py` — no cycles.

```python
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    ValidationWarning,
)

class TurnPacketSuccess(ProtocolModel):
    """Successful TurnPacket response."""

    schema_version: SchemaVersionLiteral
    status: Literal["success"]
    entities: list[Entity]
    path_decisions: list[PathDecision]
    template_candidates: list[TemplateCandidate]
    budget: Budget
    deduped: list[DedupRecord]

    # --- 0.2.0: Ledger validation results ---
    validated_entry: LedgerEntry
    warnings: list[ValidationWarning]
    cumulative: CumulativeState

    # --- 0.2.0: Conversation control ---
    action: Literal["continue_dialogue", "closing_probe", "conclude"]
    action_reason: str
    ledger_summary: str

    # --- 0.2.0: Checkpoint ---
    state_checkpoint: str
    checkpoint_id: str
```

**Step 4: Run new type tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestTurnRequest020 tests/test_types.py::TestTurnPacketSuccess020 tests/test_types.py::TestErrorDetail020 tests/test_types.py::TestSchemaVersion020 -v`
Expected: PASS

**Step 5: Update existing version validation tests**

In `tests/test_types.py`, find existing tests that use `"0.2.0"` as an invalid version. Change the invalid version string from `"0.2.0"` to `"0.3.0"`. The test asserting `"0.1.0"` is valid should now assert it's invalid — but this is already covered by `TestSchemaVersion020.test_old_version_rejected`. Update the existing test to use `"0.3.0"` as the invalid version.

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: PASS (all type tests). Many other test files will now FAIL because they still construct TurnRequest with old fields — that's expected and fixed in Task 12.

---

### Task 12: Test shape migration

**Scope:** Mechanical changes ONLY — update request builders, version literals, and response field access. Semantic test rewrites (assertions about pipeline behavior that changed) go in Task 13a.

**Files:**
- Modify: `tests/test_pipeline.py` (`_make_turn_request` + callers)
- Modify: `tests/test_templates.py` (`_make_turn_request` + callers)
- Modify: `tests/test_execute.py` (TurnRequest construction)
- Modify: `tests/test_state.py` (`_make_turn_request` + callers)
- Modify: `tests/test_integration.py` (4 `TurnRequest.model_validate()` calls)

**Step 1: Update `_make_turn_request` in test_pipeline.py**

Current helper (line 34):
```python
def _make_turn_request(**overrides: Any) -> TurnRequest:
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=[], unresolved=[]),
        "context_claims": [],
        "evidence_history": [],
        "posture": "exploratory",
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)
```

Updated helper:
```python
def _make_turn_request(**overrides: Any) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=[], unresolved=[]),
        "posture": "exploratory",
        # 0.2.0 ledger fields
        "position": "Test position",
        "claims": [],
        "delta": "static",
        "tags": ["test"],
        "unresolved": [],
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)
```

Then update callers that passed `context_claims=` or `evidence_history=` overrides:
- `context_claims=[...]` → remove (cumulative claims now come from ConversationState — semantic change handled in Task 13a)
- `evidence_history=[...]` → remove (evidence now comes from ConversationState — semantic change handled in Task 13a)

**Step 2: Update `_make_turn_request` in test_templates.py**

Current helper (line 42):
```python
def _make_turn_request(
    conversation_id: str = "conv_1",
    turn_number: int = 1,
    evidence_history: list[EvidenceRecord] | None = None,
) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        evidence_history=evidence_history or [],
        posture="exploratory",
    )
```

Updated helper:
```python
def _make_turn_request(
    conversation_id: str = "conv_1",
    turn_number: int = 1,
) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        posture="exploratory",
        position="Test position",
        claims=[],
        delta="static",
        tags=["test"],
        unresolved=[],
    )
```

Update callers that pass `evidence_history=`: remove the argument. The evidence source migrates to ConversationState in Task 13a.

**Step 3: Update `_make_turn_request` in test_state.py**

Current helper (line 30):
```python
def _make_turn_request(
    conversation_id: str = "conv_1", turn_number: int = 1
) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        evidence_history=[],
        posture="exploratory",
    )
```

Updated helper:
```python
def _make_turn_request(
    conversation_id: str = "conv_1", turn_number: int = 1,
) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        posture="exploratory",
        position="Test position",
        claims=[],
        delta="static",
        tags=["test"],
        unresolved=[],
    )
```

**Step 4: Update TurnRequest construction in test_execute.py**

test_execute.py doesn't have a `_make_turn_request` helper — it constructs TurnRequest inline in test setup. Find all `TurnRequest(` constructors and add the new required fields, remove `context_claims` and `evidence_history`.

Pattern for each TurnRequest constructor:
```python
# Old:
TurnRequest(
    schema_version=SCHEMA_VERSION,
    turn_number=1,
    conversation_id="conv_1",
    focus=Focus(text="test", claims=[...], unresolved=[...]),
    context_claims=[...],
    evidence_history=[...],
    posture="exploratory",
)

# New — add 0.2.0 fields, remove old fields:
TurnRequest(
    schema_version=SCHEMA_VERSION,
    turn_number=1,
    conversation_id="conv_1",
    focus=Focus(text="test", claims=[...], unresolved=[...]),
    posture="exploratory",
    position="Test position",
    claims=[...],         # same claims as focus.claims (or appropriate defaults)
    delta="advancing",
    tags=["test"],
    unresolved=[...],     # same as focus.unresolved (or appropriate defaults)
)
```

**Step 5: Update test_integration.py model_validate calls**

Four `TurnRequest.model_validate()` calls at lines 32, 191, 262, 317. Each needs:
1. Add: `"position"`, `"claims"`, `"delta"`, `"tags"`, `"unresolved"` keys
2. Remove: `"context_claims"`, `"evidence_history"` keys

Example (line 32 call):
```python
# Old:
request = TurnRequest.model_validate({
    "schema_version": SCHEMA_VERSION,
    "turn_number": 3,
    "conversation_id": "conv_abc123",
    "focus": { ... },
    "context_claims": [...],
    "evidence_history": [...],
    "posture": "collaborative",
})

# New:
request = TurnRequest.model_validate({
    "schema_version": SCHEMA_VERSION,
    "turn_number": 3,
    "conversation_id": "conv_abc123",
    "focus": { ... },
    "posture": "collaborative",
    "position": "Whether the project uses YAML or TOML for configuration",
    "claims": [
        {"text": "The project uses settings.yaml", "status": "new", "turn": 3},
        {"text": "YAML chosen over TOML", "status": "new", "turn": 3},
    ],
    "delta": "advancing",
    "tags": ["configuration"],
    "unresolved": [
        {"text": "Whether config.yaml is the only config file", "turn": 3},
    ],
})
```

Repeat for all 4 calls. Keep focus unchanged (it still carries the full text + nested claims/unresolved for entity extraction). The new top-level fields carry the same data in a flat structure for ledger validation.

**Step 6: Update TurnPacketSuccess assertions in tests**

Tests that assert on TurnPacketSuccess fields need updating. The response now includes additional fields. For mechanical migration, tests that check `result.entities`, `result.path_decisions`, etc. don't need changes — those fields still exist. Tests that construct TurnPacketSuccess directly (if any) need the new fields added.

Focus on making the TurnRequest construction compile. Pipeline semantic tests that will fail because the pipeline doesn't yet produce the new response fields are deferred to Task 13a.

**Step 7: Run tests and apply xfail markers**

Run: `cd packages/context-injection && uv run pytest tests/ -v 2>&1 | tail -50`

Expected: Many tests pass (request construction now works). Some tests FAIL.

**Categorize each failure:**

1. **Shape failures** (Task 12 missed something) — fix immediately:
   - Missing required field in a constructor
   - Import path not updated
   - Removed field still referenced

2. **Semantic failures** (D4b scope) — mark with xfail:
   - Pipeline tests assert old behavior (e.g., `context_claims` entity extraction)
   - Pipeline doesn't yet produce new TurnPacketSuccess fields (validated_entry, etc.)
   - Execute tests reference `evidence_history` from stored request

**Xfail workflow:**
```python
@pytest.mark.xfail(strict=True, reason="D4b: pipeline uses context_claims for entity extraction (Task 13a)")
def test_entity_extraction_from_claims(self) -> None:
    ...
```

Each xfail reason MUST:
- Start with `D4b:` prefix
- Name the specific cause
- Reference the D4b task (Task 13a, 13b, or 14)

**Re-run after marking:** `cd packages/context-injection && uv run pytest tests/ -v`
Expected: No FAIL or ERROR results. Only PASS and XFAIL.

**Commit inventory:** Create `packages/context-injection/tests/xfail_inventory_d4a.md` listing all xfail-marked tests with their reasons and target D4b tasks.

**Step 8: Commit Tasks 11+12 together**

```bash
git add packages/context-injection/context_injection/types.py packages/context-injection/tests/test_types.py packages/context-injection/tests/test_pipeline.py packages/context-injection/tests/test_templates.py packages/context-injection/tests/test_execute.py packages/context-injection/tests/test_state.py packages/context-injection/tests/test_integration.py
git commit -m "feat(context-injection): update wire types to 0.2.0 schema + migrate test helpers (D4 Tasks 11-12)

TurnRequest: add position, claims, delta, tags, unresolved, checkpoint fields; remove context_claims, evidence_history.
TurnPacketSuccess: add validated_entry, warnings, cumulative, action, ledger_summary, checkpoint fields.
ErrorDetail: add ledger_hard_reject, checkpoint_missing, checkpoint_invalid, checkpoint_stale, turn_cap_exceeded codes.

All 739 existing tests collect and execute. Semantic failures marked xfail(strict=True) with D4b task mapping. Xfail inventory committed."
```

---
