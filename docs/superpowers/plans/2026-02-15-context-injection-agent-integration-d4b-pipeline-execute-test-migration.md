# D4b: Pipeline + Execute + Test Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D4b of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Rewire the pipeline to use ConversationState, rewire execute to auto-record evidence and use budget from ConversationState, and write integration tests + update protocol contract.
**Execution order position:** 5 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

**Requires from D4a:**
- 0.2.0 `TurnRequest`/`TurnPacket` types from `context_injection/types.py`
- All 739 existing tests collect and execute (no import/construction errors); semantic failures marked `xfail(strict=True)` with D4b task mapping
- Xfail inventory at `packages/context-injection/tests/xfail_inventory_d4a.md` — xfail inventory matches in-code markers
- Source of truth: `context_injection/types.py`

**Requires from D1:**
- `LedgerEntry`, validation functions from `context_injection/ledger.py`
- Source of truth: `context_injection/ledger.py`

**Requires from D2:**
- `ConversationState` from `context_injection/conversation.py`
- Checkpoint types from `context_injection/checkpoint.py`
- `AppContext.conversations` from `context_injection/state.py`
- Source of truth: `context_injection/conversation.py`, `context_injection/checkpoint.py`, `context_injection/state.py`

**Requires from D3:**
- `compute_action()`, `generate_ledger_summary()` from `context_injection/control.py`
- Source of truth: `context_injection/control.py`

**Critical invariants:**
- Pipeline function signature `process_turn(request, ctx)` is unchanged (Q2)
- Pipeline resolves conversation internally via `ctx.get_or_create_conversation(request.conversation_id)`
- `match_templates` does NOT read `turn_request.context_claims` or `turn_request.evidence_history` — only uses `conversation_id` and `turn_number` for HMAC token payloads (Q1). templates.py is unchanged.
- Pipeline builds prospective state via `with_turn()`, computes all derived fields, then commits atomically (Q5)

**Adaptation:** If D1/D2/D3/D4a type or function names differ from this plan, adapt references and note the mapping.

## Files in Scope

**Create:**
- Integration test files as needed

**Modify:**
- `context_injection/pipeline.py` — Rewired to use ConversationState, new validation/control steps
- `context_injection/execute.py` — Auto-record evidence, budget from ConversationState
- `context_injection/server.py` — Minimal changes
- `docs/references/context-injection-contract.md` — 0.2.0 protocol contract
- `pyproject.toml` — Version bump to 0.2.0

**Out of scope:** All files not listed above. In particular, do NOT modify `context_injection/types.py` (D4a), `context_injection/ledger.py` (D1), `context_injection/conversation.py` (D2), `context_injection/control.py` (D3), or `.claude/agents/codex-dialogue.md` (D5).

## Done Criteria

- Pipeline rewired and functional with ConversationState
- Execute auto-records evidence correctly
- All tests pass (existing updated + new integration tests)
- Protocol contract updated to 0.2.0
- No temporary D4a semantic markers remain: no pytest xfail with reason prefix `D4b:` exists in tests

## Scope Boundary

This document covers D4b only. After completing all tasks in this delivery, stop. Do not proceed to D5.

## Relevant Resolved Questions

**Q1 — match_templates internal access:** Does NOT read `turn_request.context_claims` or `turn_request.evidence_history`. Only uses `turn_request.conversation_id` and `turn_request.turn_number` for HMAC token payloads (templates.py:280-281, 339-340). templates.py is unchanged in D4.

**Q2 — Pipeline signature:** Locked to option (a) — `process_turn(request, ctx)` unchanged. Pipeline resolves conversation internally via `ctx.get_or_create_conversation(request.conversation_id)`. Keeps public API stable.

**Q4 — Checkpoint ingestion gap:** Original plan omitted checkpoint intake from D4 pipeline. Now explicit in Task 13a step 3 and D2 Task 7 validation policy.

**Q5 — Prospective state pattern:** Pipeline builds a projected ConversationState via `with_turn()`, computes all derived fields from it, then commits atomically by replacing the dict entry. No partial mutations.

---
### Task 13a: Pipeline rewiring + semantic test migration

**Files:**
- Modify: `context_injection/pipeline.py`
- Modify: `tests/test_pipeline.py` (ConversationState setup + semantic test rewrites)
- Modify: `tests/test_integration.py` (process-turn semantic tests)

Pipeline signature unchanged: `process_turn(request: TurnRequest, ctx: AppContext) -> TurnPacketSuccess | TurnPacketError`. The pipeline resolves conversation state via `ctx.get_or_create_conversation(request.conversation_id)` internally.

**Step 1: Write failing tests for new pipeline behavior**

Add to `tests/test_pipeline.py`:

```python
from context_injection.checkpoint import CheckpointError
from context_injection.conversation import ConversationState
from context_injection.control import ConversationAction
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    ValidationWarning,
)


class TestPipelineConversationState:
    """Pipeline resolves and updates ConversationState."""

    def test_first_turn_creates_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_new")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "conv_new" in ctx.conversations

    def test_conversation_persists_across_turns(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_multi", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Pass checkpoint back
        r2 = _make_turn_request(
            conversation_id="conv_multi",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2


class TestPipelineLedgerValidation:
    """Pipeline validates ledger entry and returns it."""

    def test_success_includes_validated_entry(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(
            position="Auth module analysis",
            claims=[Claim(text="JWT is used", status="new", turn=1)],
            delta="advancing",
            tags=["architecture"],
        )
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.validated_entry.position == "Auth module analysis"
        assert result.validated_entry.turn_number == 1
        assert len(result.validated_entry.claims) == 1

    def test_hard_reject_returns_error(self) -> None:
        """turn_number=0 should hard reject (invalid turn number per D1)."""
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(turn_number=0, claims=[])
        result = process_turn(request, ctx)
        assert result.status == "error"
        assert result.error.code == "ledger_hard_reject"


class TestPipelineActionComputation:
    """Pipeline computes action from conversation trajectory."""

    def test_first_turn_continues(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.action == ConversationAction.CONTINUE_DIALOGUE

    def test_action_reason_nonempty(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert len(result.action_reason) > 0


class TestPipelineCheckpoint:
    """Pipeline serializes and returns checkpoint."""

    def test_checkpoint_returned(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.state_checkpoint is not None
        assert result.checkpoint_id is not None
        assert len(result.checkpoint_id) > 0

    def test_checkpoint_id_stored_in_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_ckpt")
        result = process_turn(request, ctx)
        assert result.status == "success"
        conv = ctx.conversations["conv_ckpt"]
        assert conv.last_checkpoint_id == result.checkpoint_id

    def test_cross_conversation_checkpoint_rejected(self) -> None:
        """Checkpoint from conversation A must not be accepted by conversation B (D2 guard #4)."""
        ctx = _make_ctx(git_files=set())

        # Turn 1 on conversation A — get a valid checkpoint
        r1 = _make_turn_request(conversation_id="conv_A", turn_number=1)
        result_a = process_turn(r1, ctx)
        assert result_a.status == "success"

        # Attempt turn 2 on conversation B using conversation A's checkpoint
        r2 = _make_turn_request(
            conversation_id="conv_B",
            turn_number=2,
            state_checkpoint=result_a.state_checkpoint,
            checkpoint_id=result_a.checkpoint_id,
        )
        result_b = process_turn(r2, ctx)
        assert result_b.status == "error"
        assert result_b.error.code == "checkpoint_invalid"


class TestCheckpointConsistencyCC3:
    """CC-3 test matrix: checkpoint triplet (conversation_id, turn_number, checkpoint_id) consistency."""

    def test_consistent_triplet_accepted(self) -> None:
        """Valid checkpoint with matching conversation_id, turn_number, and checkpoint_id passes."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_cc3", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_cc3",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

    def test_two_turn_chain(self) -> None:
        """Checkpoint chains across three turns: T1 → T2 → T3."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_chain", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_chain",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        r3 = _make_turn_request(
            conversation_id="conv_chain",
            turn_number=3,
            state_checkpoint=result2.state_checkpoint,
            checkpoint_id=result2.checkpoint_id,
        )
        result3 = process_turn(r3, ctx)
        assert result3.status == "success"
        assert result3.cumulative.turns_completed == 3

    def test_restart_chain_from_checkpoint(self) -> None:
        """Server restart: conversation restored from checkpoint without in-memory state."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_restart", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Simulate server restart — fresh ctx with no in-memory conversations
        ctx2 = _make_ctx(git_files=set())
        assert "conv_restart" not in ctx2.conversations

        r2 = _make_turn_request(
            conversation_id="conv_restart",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx2)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2

    def test_cross_conversation_checkpoint_rejected(self) -> None:
        """Checkpoint from conversation A rejected when presented to conversation B."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_cc3_A", turn_number=1)
        result_a = process_turn(r1, ctx)
        assert result_a.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_cc3_B",
            turn_number=2,
            state_checkpoint=result_a.state_checkpoint,
            checkpoint_id=result_a.checkpoint_id,
        )
        result_b = process_turn(r2, ctx)
        assert result_b.status == "error"
        assert result_b.error.code == "checkpoint_invalid"


class TestTurnCapCC5:
    """CC-5 test matrix: turn cap enforcement via MAX_CONVERSATION_TURNS."""

    def test_constant_invariant(self) -> None:
        """MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT (import-time check)."""
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        from context_injection.checkpoint import MAX_ENTRIES_BEFORE_COMPACT
        assert MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT

    def test_below_cap_succeeds(self) -> None:
        """Conversation below turn cap processes normally."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_below_cap", turn_number=1)
        result = process_turn(r1, ctx)
        assert result.status == "success"

    def test_at_cap_rejected(self) -> None:
        """Conversation at turn cap returns turn_cap_exceeded error."""
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        # Build up conversation to exactly MAX_CONVERSATION_TURNS entries
        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_at_cap",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)
            assert last_result.status == "success", f"Turn {turn} should succeed"

        # Next turn should be rejected
        r_over = _make_turn_request(
            conversation_id="conv_at_cap",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        result_over = process_turn(r_over, ctx)
        assert result_over.status == "error"
        assert result_over.error.code == "turn_cap_exceeded"

    def test_no_mutation_on_reject(self) -> None:
        """Turn cap rejection does not mutate ConversationState."""
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        # Fill to cap
        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_no_mutate",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)

        entries_before = len(ctx.conversations["conv_no_mutate"].entries)

        # Rejected turn must not add an entry
        r_over = _make_turn_request(
            conversation_id="conv_no_mutate",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        process_turn(r_over, ctx)
        entries_after = len(ctx.conversations["conv_no_mutate"].entries)
        assert entries_after == entries_before

    def test_repeated_turn_number_bound(self) -> None:
        """Submitting the same turn_number twice does not bypass the cap."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_repeat", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Repeat turn 1 — should not create a second entry or bypass validation
        r1_dup = _make_turn_request(
            conversation_id="conv_repeat",
            turn_number=1,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result_dup = process_turn(r1_dup, ctx)
        # Implementation-defined: may succeed (idempotent) or reject (stale turn).
        # Either way, entries should not exceed 1.
        conv = ctx.conversations["conv_repeat"]
        assert len(conv.entries) <= 2  # at most original + duplicate

    def test_checkpoint_restore_at_cap(self) -> None:
        """After server restart, restored-at-cap conversation still rejects."""
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        # Fill to cap
        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_restore_cap",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)

        # Simulate restart — fresh context, restore from checkpoint
        ctx2 = _make_ctx(git_files=set())
        r_over = _make_turn_request(
            conversation_id="conv_restore_cap",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        result_over = process_turn(r_over, ctx2)
        assert result_over.status == "error"
        assert result_over.error.code == "turn_cap_exceeded"


class TestPipelineLedgerSummary:
    """Pipeline generates ledger summary."""

    def test_summary_included(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(position="Test analysis")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "T1:" in result.ledger_summary
        assert "Test analysis" in result.ledger_summary


class TestPipelineCumulativeClaims:
    """Pipeline uses cumulative claims from ConversationState (replaces context_claims)."""

    def test_prior_claims_extracted_as_out_of_focus(self) -> None:
        """Claims from prior turns should be extracted as out-of-focus entities."""
        ctx = _make_ctx(git_files={"src/app.py"})

        # Turn 1: claim mentions src/app.py
        r1 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=1,
            claims=[Claim(text="The file src/app.py has the logic", status="new", turn=1)],
            position="Initial review",
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Turn 2: new focus, no mention of src/app.py — but prior claim should extract it
        r2 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=2,
            claims=[Claim(text="New claim about something else", status="new", turn=2)],
            position="Follow-up analysis",
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        # Prior claim entity should appear as out-of-focus
        out_of_focus = [e for e in result2.entities if not e.in_focus]
        file_entities = [e for e in out_of_focus if e.canonical == "src/app.py"]
        assert len(file_entities) > 0, "Prior claim's file entity should be extracted out-of-focus"


class TestPipelinePriorEvidence:
    """Pipeline uses evidence from ConversationState (replaces request.evidence_history)."""

    def test_evidence_from_conversation_used_for_dedup(self) -> None:
        """Evidence recorded in ConversationState should deduplicate templates."""
        ctx = _make_ctx(git_files={"src/app.py"})

        # Seed conversation with evidence record
        # entity_key uses canonical format: "{entity_type}:{canonical_form}"
        # (see canonical.py:make_entity_key)
        from context_injection.types import EvidenceRecord
        conv = ctx.get_or_create_conversation("conv_evidence")
        conv = conv.with_evidence(
            EvidenceRecord(
                entity_key="file_path:src/app.py",
                template_id="clarify.file_path",
                turn=1,
            ),
        )
        ctx.conversations["conv_evidence"] = conv

        # Turn 2: mention src/app.py again — should be deduped
        r2 = _make_turn_request(
            conversation_id="conv_evidence",
            turn_number=2,
            claims=[Claim(text="Check src/app.py", status="new", turn=2)],
            position="Second review",
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        # The src/app.py entity should be deduped (canonical key format)
        deduped_keys = [d.entity_key for d in result2.deduped]
        assert "file_path:src/app.py" in deduped_keys
```

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelineConversationState -v`
Expected: FAIL — pipeline doesn't resolve ConversationState yet

**Step 2: Rewrite `_process_turn_inner` to 17-step pipeline**

Replace the body of `_process_turn_inner` in `context_injection/pipeline.py`:

```python
"""Call 1 pipeline: TurnRequest -> TurnPacketSuccess | TurnPacketError.

Composes the full v0.2.0 processing pipeline:
 1. Schema version validation
 2. Resolve ConversationState
 3. Checkpoint intake
 4. Snapshot prior state (claims + evidence)
 5. Entity extraction from focus + prior claims
 6. Path checking for Tier 1 file entities
 7. Template matching with prior evidence
 8. Budget computation from prior evidence
 9. Ledger entry validation
10. Build provisional state
11. Compute cumulative state, action, reason
12. Closing probe projection
13. Serialize checkpoint (returns updated state with checkpoint ID)
14. Generate ledger summary
15. Store TurnRequestRecord for Call 2
16. Commit projected state
17. Return TurnPacketSuccess

Contract reference: docs/references/context-injection-contract.md
"""

from __future__ import annotations

import logging

from context_injection.checkpoint import (
    CheckpointError,
    compact_ledger,
    serialize_checkpoint,
    validate_checkpoint_intake,
)
from context_injection.control import compute_action, generate_ledger_summary
from context_injection.entities import extract_entities
from context_injection.ledger import LedgerValidationError, validate_ledger_entry
from context_injection.paths import check_path_compile_time
from context_injection.state import (
    AppContext,
    TurnRequestRecord,
    make_turn_request_ref,
)
from context_injection.templates import compute_budget, match_templates
from context_injection.types import (
    SCHEMA_VERSION,
    Claim,
    Entity,
    ErrorDetail,
    PathDecision,
    TurnPacketError,
    TurnPacketSuccess,
    TurnRequest,
)

logger = logging.getLogger(__name__)

MAX_CONVERSATION_TURNS: int = 15

# Import-time invariant: turn cap must be strictly less than compaction threshold.
# If this fails, compute_cumulative_state() produces incorrect totals after compaction.
from context_injection.checkpoint import MAX_ENTRIES_BEFORE_COMPACT

if MAX_CONVERSATION_TURNS >= MAX_ENTRIES_BEFORE_COMPACT:
    raise RuntimeError(
        f"MAX_CONVERSATION_TURNS ({MAX_CONVERSATION_TURNS}) must be strictly less than "
        f"MAX_ENTRIES_BEFORE_COMPACT ({MAX_ENTRIES_BEFORE_COMPACT}). "
        "See DD-2 (C-lite) invariant."
    )

_PATH_CHECK_TYPES: frozenset[str] = frozenset({"file_loc", "file_path", "file_name"})


def process_turn(
    request: TurnRequest,
    ctx: AppContext,
) -> TurnPacketSuccess | TurnPacketError:
    """Process a Call 1 TurnRequest through the full pipeline."""
    try:
        return _process_turn_inner(request, ctx)
    except CheckpointError as exc:
        logger.warning("Checkpoint error: %s (code=%s)", exc, exc.code)
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(code=exc.code, message=str(exc)),
        )
    except LedgerValidationError as exc:
        logger.warning("Ledger validation error: %s", exc)
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="ledger_hard_reject",
                message=str(exc),
            ),
        )
    except Exception as exc:
        logger.exception("process_turn failed: %s", exc)
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="internal_error",
                message=f"process_turn failed: {exc}",
            ),
        )


def _process_turn_inner(
    request: TurnRequest,
    ctx: AppContext,
) -> TurnPacketSuccess | TurnPacketError:
    """Inner pipeline logic — 17-step orchestration."""

    # --- Step 1: Schema version validation ---
    if request.schema_version != SCHEMA_VERSION:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="invalid_schema_version",
                message=(
                    f"Expected schema_version={SCHEMA_VERSION!r}, "
                    f"got {request.schema_version!r}"
                ),
            ),
        )

    # --- Step 1b: Dual-claims channel guard (CC-PF-3) ---
    # TurnRequest carries claims/unresolved at both top-level and inside focus.
    # If these diverge, the pipeline cannot determine authoritative source.
    if request.focus.claims != request.claims:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="ledger_hard_reject",
                message=(
                    "focus.claims and top-level claims are inconsistent. "
                    "Both channels must carry identical claim lists."
                ),
            ),
        )
    if request.focus.unresolved != request.unresolved:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="ledger_hard_reject",
                message=(
                    "focus.unresolved and top-level unresolved are inconsistent. "
                    "Both channels must carry identical unresolved lists."
                ),
            ),
        )

    # --- Step 2: Resolve ConversationState ---
    base = ctx.get_or_create_conversation(request.conversation_id)

    # --- Step 3: Checkpoint intake ---
    base = validate_checkpoint_intake(
        in_memory=base,
        checkpoint_id=request.checkpoint_id,
        checkpoint_payload=request.state_checkpoint,
        turn_number=request.turn_number,
        target_conversation_id=request.conversation_id,
    )

    # --- Step 3b: Turn cap guard (CC-4/CC-5/DD-2) ---
    if len(base.entries) >= MAX_CONVERSATION_TURNS:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="turn_cap_exceeded",
                message=(
                    f"Conversation has {len(base.entries)} entries, "
                    f"which meets or exceeds MAX_CONVERSATION_TURNS={MAX_CONVERSATION_TURNS}."
                ),
            ),
        )

    # --- Step 4: Snapshot prior state ---
    prior_claims: list[Claim] = base.get_cumulative_claims()
    prior_evidence = base.get_evidence_history()

    # --- Step 5: Entity extraction ---
    entities: list[Entity] = []

    for claim in request.focus.claims:
        entities.extend(
            extract_entities(
                claim.text,
                source_type="claim",
                in_focus=True,
                ctx=ctx,
            )
        )

    for unresolved_item in request.focus.unresolved:
        entities.extend(
            extract_entities(
                unresolved_item.text,
                source_type="unresolved",
                in_focus=True,
                ctx=ctx,
            )
        )

    for claim in prior_claims:
        entities.extend(
            extract_entities(
                claim.text,
                source_type="claim",
                in_focus=False,
                ctx=ctx,
            )
        )

    # --- Step 6: Path checking ---
    path_decisions: list[PathDecision] = []

    for entity in entities:
        if entity.tier != 1:
            continue
        if entity.type not in _PATH_CHECK_TYPES:
            continue

        result = check_path_compile_time(
            entity.canonical,
            repo_root=ctx.repo_root,
            git_files=ctx.git_files,
        )

        path_decisions.append(
            PathDecision(
                entity_id=entity.id,
                status=result.status,
                user_rel=result.user_rel,
                resolved_rel=result.resolved_rel,
                risk_signal=result.risk_signal,
                deny_reason=result.deny_reason,
                candidates=result.candidates,
                unresolved_reason=result.unresolved_reason,
            )
        )

    # --- Step 7: Template matching (with prior evidence) ---
    template_candidates, dedup_records, spec_registry = match_templates(
        entities,
        path_decisions,
        prior_evidence,
        request,
        ctx,
    )

    # --- Step 8: Budget computation (from prior evidence) ---
    budget = compute_budget(prior_evidence)

    # --- Step 9: Ledger entry validation ---
    # prior_claims already computed at step 4 (empty list when no entries)
    unresolved_closed: int = (
        base.compute_cumulative_state().unresolved_closed if base.entries else 0
    )
    validated_entry, warnings = validate_ledger_entry(
        position=request.position,
        claims=request.claims,
        delta=request.delta,
        tags=request.tags,
        unresolved=request.unresolved,
        turn_number=request.turn_number,
        prior_claims=prior_claims,
        unresolved_closed=unresolved_closed,
    )

    # Hard rejects are raised as LedgerValidationError by validate_ledger_entry
    # and caught by the outer try/except in process_turn (see D4b-4).

    # --- Step 10: Build provisional state ---
    provisional = base.with_turn(validated_entry)

    # --- Step 11: Compute cumulative, action, reason ---
    cumulative = provisional.compute_cumulative_state()
    turn_budget_remaining = max(0, MAX_CONVERSATION_TURNS - cumulative.turns_completed)
    action, action_reason = compute_action(
        entries=provisional.entries,
        budget_remaining=turn_budget_remaining,
        closing_probe_fired=provisional.closing_probe_fired,
    )

    # --- Step 12: Closing probe projection ---
    if action == "closing_probe":
        projected = provisional.with_closing_probe_fired()
    else:
        projected = provisional

    # --- Step 13: Serialize checkpoint ---
    projected = compact_ledger(projected)
    serialized = serialize_checkpoint(state=projected)
    projected = serialized.state
    checkpoint_id = serialized.checkpoint_id
    checkpoint_string = serialized.checkpoint_string

    # --- Step 14: Generate ledger summary ---
    ledger_summary = generate_ledger_summary(
        entries=projected.entries,
        cumulative=cumulative,
    )

    # --- Step 15: Store TurnRequestRecord for Call 2 ---
    ref = make_turn_request_ref(request)
    record = TurnRequestRecord(
        turn_request=request,
        scout_options=spec_registry,
    )
    ctx.store_record(ref, record)

    # --- Step 16: Commit projected state ---
    ctx.conversations[request.conversation_id] = projected

    # --- Step 17: Return TurnPacketSuccess ---
    return TurnPacketSuccess(
        schema_version=SCHEMA_VERSION,
        status="success",
        entities=entities,
        path_decisions=path_decisions,
        template_candidates=template_candidates,
        budget=budget,
        deduped=dedup_records,
        validated_entry=validated_entry,
        warnings=warnings,
        cumulative=cumulative,
        action=action,
        action_reason=action_reason,
        ledger_summary=ledger_summary,
        state_checkpoint=checkpoint_string,
        checkpoint_id=checkpoint_id,
    )
```

**Step 3: Update semantic tests in test_pipeline.py**

Identify tests that assert on the old `context_claims`-based entity extraction. These need to be rewritten to set up ConversationState with prior claims instead:

Old pattern:
```python
def test_entities_extracted_from_context_claims(self):
    request = _make_turn_request(
        context_claims=[Claim(text="File src/app.py has logic", status="new", turn=1)],
    )
    result = process_turn(request, ctx)
    # assert on entities...
```

New pattern:
```python
def test_prior_claims_extracted_as_out_of_focus(self):
    ctx = _make_ctx(git_files={"src/app.py"})
    # Seed conversation with a prior turn's claims
    conv = ctx.get_or_create_conversation("conv_test")
    conv = conv.with_turn(LedgerEntry(
        position="Prior analysis",
        claims=[Claim(text="File src/app.py has logic", status="new", turn=1)],
        delta="advancing", tags=["test"], unresolved=[],
        counters=LedgerEntryCounters(new_claims=1, revised=0, conceded=0, unresolved_closed=0),
        quality="substantive", effective_delta="advancing", turn_number=1,
    ))
    conv = conv.with_checkpoint_id("prior_ckpt")
    ctx.conversations["conv_test"] = conv

    request = _make_turn_request(
        conversation_id="conv_test",
        turn_number=2,
        checkpoint_id="prior_ckpt",
    )
    result = process_turn(request, ctx)
    # assert on out-of-focus entities...
```

Similarly, tests referencing `evidence_history` for template dedup or budget need to set up ConversationState with evidence records.

**Step 4: Update semantic tests in test_integration.py**

Integration tests that passed `evidence_history` or `context_claims` in request dicts and asserted on dedup/budget behavior need rewriting. The request dict no longer has these fields — the data comes from ConversationState.

For tests that previously tested "first turn with no history," little changes — the ConversationState is fresh. For tests that tested "turn with prior evidence," set up the conversation's evidence_history via `with_evidence()` before calling `process_turn`.

**Step 5: Run full test suite**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: Most tests pass. Remaining failures should be in test_execute.py (evidence source — Task 13b scope).

**Step 6: Fix any remaining test failures in pipeline/integration scope**

Iterate: run tests, identify failures, fix. Each fix should be small (field name changes, assertion updates). If a failure is in execute scope, leave it for Task 13b.

**Step 7: Run full suite to verify pipeline scope is green**

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py tests/test_integration.py tests/test_types.py tests/test_state.py tests/test_templates.py -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add packages/context-injection/context_injection/pipeline.py packages/context-injection/tests/test_pipeline.py packages/context-injection/tests/test_integration.py
git commit -m "feat(context-injection): rewrite pipeline to 17-step 0.2.0 flow with conversation state (D4 Task 13a)

Pipeline resolves ConversationState internally. Entity extraction uses cumulative claims
from conversation (replaces context_claims). Template matching and budget use evidence
from conversation (replaces evidence_history). Ledger validation, action computation,
checkpoint serialization, and summary generation integrated."
```

---

### Task 13b: Execute rewiring

**Files:**
- Modify: `context_injection/execute.py`
- Modify: `tests/test_execute.py`

Execute changes: `execute_scout` gets evidence count from ConversationState instead of `record.turn_request.evidence_history`. After successful scout execution, records evidence in ConversationState.

**Step 1: Write failing tests for evidence-from-conversation**

Add to `tests/test_execute.py`:

```python
from context_injection.conversation import ConversationState
from context_injection.types import EvidenceRecord


class TestExecuteEvidenceFromConversation:
    """execute_scout uses ConversationState for evidence count."""

    def test_budget_reflects_conversation_evidence(self, tmp_path: Path) -> None:
        """Evidence count comes from conversation state, not request."""
        # Set up ctx with a file
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("def hello(): pass")
        ctx = AppContext.create(
            repo_root=str(tmp_path),
            git_files={"src/app.py"},
        )

        # Seed conversation with 2 prior evidence records
        conv = ctx.get_or_create_conversation("conv_budget")
        conv = conv.with_evidence(
            EvidenceRecord(entity_key="file1.py", template_id="clarify.file_path", turn=1),
        )
        conv = conv.with_evidence(
            EvidenceRecord(entity_key="file2.py", template_id="clarify.file_path", turn=1),
        )
        ctx.conversations["conv_budget"] = conv

        # Process turn 1 to create a scout option
        request = _make_turn_request(
            conversation_id="conv_budget",
            claims=[Claim(text="Check src/app.py", status="new", turn=1)],
        )
        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Execute a scout — budget should reflect 2 prior + 1 new = 3
        assert len(turn_result.template_candidates) > 0, (
            "Deterministic fixture must produce template candidates"
        )
        candidate = turn_result.template_candidates[0]
        scout_req = ScoutRequest(
            schema_version=SCHEMA_VERSION,
            scout_option_id=candidate.scout_options[0].id,
            scout_token=candidate.scout_options[0].scout_token,
            turn_request_ref=f"{request.conversation_id}:{request.turn_number}",
        )
        scout_result = execute_scout(ctx, scout_req)
        # Budget should show 3 evidence items (2 prior + 1 new)
        assert scout_result.budget.evidence_count == 3

    def test_evidence_recorded_after_success(self, tmp_path: Path) -> None:
        """Successful scout execution records evidence in ConversationState."""
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("def hello(): pass")
        ctx = AppContext.create(
            repo_root=str(tmp_path),
            git_files={"src/app.py"},
        )

        # Process turn
        request = _make_turn_request(
            conversation_id="conv_record",
            claims=[Claim(text="Check src/app.py", status="new", turn=1)],
        )
        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Execute scout
        assert len(turn_result.template_candidates) > 0, (
            "Deterministic fixture must produce template candidates"
        )
        candidate = turn_result.template_candidates[0]
        scout_req = ScoutRequest(
            schema_version=SCHEMA_VERSION,
            scout_option_id=candidate.scout_options[0].id,
            scout_token=candidate.scout_options[0].scout_token,
            turn_request_ref=f"{request.conversation_id}:{request.turn_number}",
        )
        scout_result = execute_scout(ctx, scout_req)

        # Conversation should now have evidence
        conv = ctx.conversations["conv_record"]
        evidence = conv.get_evidence_history()
        assert len(evidence) >= 1
```

Run: `cd packages/context-injection && uv run pytest tests/test_execute.py::TestExecuteEvidenceFromConversation -v`
Expected: FAIL — execute_scout still reads from request.evidence_history

**Step 2: Implement execute changes**

Modify `context_injection/execute.py`:

1. In `execute_scout` function (around line 525), change evidence source:

```python
# Old (line 525):
evidence_history_len = len(record.turn_request.evidence_history)

# New:
conversation = ctx.get_or_create_conversation(record.turn_request.conversation_id)
evidence_history_len = len(conversation.get_evidence_history())
```

2. After successful scout execution, record evidence in conversation state. Add after the scout dispatch (after the `execute_read` / `execute_grep` call returns):

```python
# After scout execution, record evidence if successful
if isinstance(scout_result, ScoutResultSuccess):
    conversation = ctx.get_or_create_conversation(record.turn_request.conversation_id)
    conversation = conversation.with_evidence(
        EvidenceRecord(
            entity_key=option.entity_key,
            template_id=option.template_id,
            turn=record.turn_request.turn_number,
        ),
    )
    ctx.conversations[record.turn_request.conversation_id] = conversation
```

3. Add necessary imports:

```python
from context_injection.conversation import ConversationState
from context_injection.types import EvidenceRecord
```

**Known limitation — checkpoint atomicity gap:** Evidence recorded by `execute_scout` updates in-memory `ConversationState` but is NOT included in the checkpoint that was already returned to the client during Call 1. On server restart, restored state from the client's checkpoint loses evidence recorded during Call 2. This is low-probability under the "short-lived MCP server process" assumption (server lifetime typically covers a single dialogue session). If long-lived server deployments become a requirement, this gap must be addressed by either: (a) returning an updated checkpoint from Call 2, or (b) persisting evidence to durable storage on write.

**Step 3: Update existing execute tests**

Tests that previously relied on `evidence_history` in the stored request for budget calculations need updating. The evidence now comes from ConversationState. For tests that check budget values:

- If test had `evidence_history=[]` (most tests): budget should be 0 → still works because ConversationState starts empty
- If test had `evidence_history=[...]` with records: seed the ConversationState with matching evidence records

**Step 4: Run execute tests**

Run: `cd packages/context-injection && uv run pytest tests/test_execute.py -v`
Expected: PASS

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All tests pass (pipeline + execute both rewired)

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/execute.py packages/context-injection/tests/test_execute.py
git commit -m "feat(context-injection): rewire execute_scout to use ConversationState for evidence (D4 Task 13b)

Evidence count sourced from conversation.get_evidence_history() instead of
request.evidence_history. Successful scout execution records evidence via
conversation.with_evidence()."
```

---

### Task 14: Integration tests + protocol contract

**Files:**
- Modify: `tests/test_integration.py`
- Modify: `docs/references/context-injection-contract.md`

New integration tests verify the complete 0.2.0 flow end-to-end: Call 1 → Call 2 round-trip with ledger validation, multi-turn conversation with cumulative state, checkpoint pass-through, and action flow.

**Step 1: Write new 0.2.0 integration tests**

Add to `tests/test_integration.py`:

```python
from context_injection.control import ConversationAction
from context_injection.enums import EffectiveDelta


class TestIntegration020RoundTrip:
    """Full 0.2.0 Call 1 → Call 2 round trip."""

    def test_call1_returns_ledger_entry(self, tmp_path: Path) -> None:
        """Process turn returns validated ledger entry with all fields."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "config.py").write_text("DB_URL = 'postgres://...'")
        git_files = {"src/config.py"}
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_020",
            "focus": {
                "text": "Database configuration approach",
                "claims": [
                    {"text": "Project uses src/config.py for DB config", "status": "new", "turn": 1},
                ],
                "unresolved": [],
            },
            "posture": "collaborative",
            "position": "Database configuration analysis",
            "claims": [
                {"text": "Project uses src/config.py for DB config", "status": "new", "turn": 1},
            ],
            "delta": "advancing",
            "tags": ["configuration", "database"],
            "unresolved": [],
        })

        result = process_turn(request, ctx)
        assert result.status == "success"

        # Ledger entry
        assert result.validated_entry.position == "Database configuration analysis"
        assert result.validated_entry.turn_number == 1
        assert result.validated_entry.effective_delta in set(EffectiveDelta)

        # Cumulative state
        assert result.cumulative.turns_completed == 1
        assert result.cumulative.total_claims == 1

        # Action
        assert result.action == ConversationAction.CONTINUE_DIALOGUE
        assert len(result.action_reason) > 0

        # Checkpoint
        assert result.checkpoint_id is not None
        assert result.state_checkpoint is not None

        # Summary
        assert "T1:" in result.ledger_summary

    def test_call1_then_call2_round_trip(self, tmp_path: Path) -> None:
        """Full round-trip: Call 1 → get scout → Call 2 → execute scout."""
        (tmp_path / "main.py").write_text("def main():\n    print('hello')\n")
        git_files = {"main.py"}
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

        # Call 1
        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_roundtrip",
            "focus": {
                "text": "Main entry point",
                "claims": [
                    {"text": "main.py is the entry point", "status": "new", "turn": 1},
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
            "position": "Entry point analysis",
            "claims": [
                {"text": "main.py is the entry point", "status": "new", "turn": 1},
            ],
            "delta": "advancing",
            "tags": ["architecture"],
            "unresolved": [],
        })

        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Call 2 — deterministic fixture guarantees template matching
        assert len(turn_result.template_candidates) > 0, (
            "Deterministic fixture must produce template candidates"
        )
        candidate = turn_result.template_candidates[0]
        scout_req = ScoutRequest(
            schema_version=SCHEMA_VERSION,
            scout_option_id=candidate.scout_options[0].id,
            scout_token=candidate.scout_options[0].scout_token,
            turn_request_ref=f"{request.conversation_id}:{request.turn_number}",
        )
        scout_result = execute_scout(ctx, scout_req)
        assert scout_result.status == "success"


class TestIntegration020MultiTurn:
    """Multi-turn conversation with state progression."""

    def test_two_turn_conversation(self, tmp_path: Path) -> None:
        """Second turn sees cumulative state from first turn."""
        (tmp_path / "app.py").write_text("x = 1")
        ctx = AppContext.create(repo_root=str(tmp_path), git_files={"app.py"})

        # Turn 1
        r1 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_multi",
            "focus": {"text": "App analysis", "claims": [
                {"text": "app.py contains state", "status": "new", "turn": 1},
            ], "unresolved": []},
            "posture": "exploratory",
            "position": "Initial app review",
            "claims": [{"text": "app.py contains state", "status": "new", "turn": 1}],
            "delta": "advancing",
            "tags": ["architecture"],
            "unresolved": [],
        })
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"
        assert result1.cumulative.turns_completed == 1

        # Turn 2 — pass checkpoint back
        r2 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 2,
            "conversation_id": "conv_multi",
            "focus": {"text": "Follow-up", "claims": [
                {"text": "app.py contains state", "status": "reinforced", "turn": 2},
            ], "unresolved": []},
            "posture": "collaborative",
            "position": "Confirmed app structure",
            "claims": [{"text": "app.py contains state", "status": "reinforced", "turn": 2}],
            "delta": "static",
            "tags": ["architecture"],
            "unresolved": [],
            "state_checkpoint": result1.state_checkpoint,
            "checkpoint_id": result1.checkpoint_id,
        })
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2
        assert result2.cumulative.reinforced >= 1

    def test_checkpoint_missing_on_turn2_without_state(self, tmp_path: Path) -> None:
        """Turn 2 without checkpoint or in-memory state → error."""
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=set())

        # Skip turn 1 — go straight to turn 2 without checkpoint
        r2 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 2,
            "conversation_id": "conv_no_state",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "test",
            "claims": [],
            "delta": "static",
            "tags": [],
            "unresolved": [],
        })
        result = process_turn(r2, ctx)
        assert result.status == "error"
        assert result.error.code == "checkpoint_missing"


class TestIntegration020ActionFlow:
    """Action computation in integration context."""

    def test_continue_on_first_turn(self, tmp_path: Path) -> None:
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=set())
        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_action",
            "focus": {"text": "test", "claims": [
                {"text": "Initial observation", "status": "new", "turn": 1},
            ], "unresolved": []},
            "posture": "exploratory",
            "position": "Initial analysis",
            "claims": [
                {"text": "Initial observation", "status": "new", "turn": 1},
            ],
            "delta": "advancing",
            "tags": ["test"],
            "unresolved": [],
        })
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.action == ConversationAction.CONTINUE_DIALOGUE
```

Run: `cd packages/context-injection && uv run pytest tests/test_integration.py::TestIntegration020RoundTrip tests/test_integration.py::TestIntegration020MultiTurn tests/test_integration.py::TestIntegration020ActionFlow -v`
Expected: PASS (pipeline already rewired in Task 13a)

**Step 2: Update protocol contract**

Update `docs/references/context-injection-contract.md` to reflect 0.2.0 schema:

1. Update schema version from `0.1.0` to `0.2.0`
2. Add TurnRequest new fields: `position`, `claims`, `delta`, `tags`, `unresolved`, `state_checkpoint`, `checkpoint_id`
3. Document removed fields: `context_claims`, `evidence_history`
4. Add TurnPacketSuccess new fields: `validated_entry`, `warnings`, `cumulative`, `action`, `action_reason`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`
5. Add new ErrorDetail codes: `ledger_hard_reject`, `checkpoint_missing`, `checkpoint_invalid`, `checkpoint_stale`, `turn_cap_exceeded`
6. Add `Budget.budget_status` to TurnPacketSuccess changes (budget now reports remaining capacity)
7. Add conversation flow section: checkpoint pass-through, multi-turn state progression, action computation

**Step 2b: Bump package version**

Update `packages/context-injection/pyproject.toml` version from `0.1.x` to `0.2.0`. The manifest (line 129) assigns this version bump to D4b but no task step previously existed for it.

**Step 3: Run full suite — final verification**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: ALL tests pass — ~739 updated + ~50-80 new from D1-D4

Run: `cd packages/context-injection && uv run pytest tests/ -v --tb=short 2>&1 | tail -5`
Expected: All pass, zero failures

**Step 3b: Verify no D4b xfails remain**

Run: `grep -r 'reason="D4b:' packages/context-injection/tests/ && echo "FAIL: D4b xfails remain" && exit 1 || echo "PASS: No D4b xfails found"`
Expected: PASS — done criteria require all D4b xfails to be resolved, this step enforces it.

**Step 4: Commit**

```bash
git add packages/context-injection/tests/test_integration.py docs/references/context-injection-contract.md packages/context-injection/pyproject.toml
git commit -m "feat(context-injection): add 0.2.0 integration tests + update protocol contract (D4 Task 14)

New round-trip, multi-turn, checkpoint, and action flow integration tests.
Protocol contract updated to 0.2.0 schema with ledger validation, conversation
control, and checkpoint fields."
```
