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

    # --- Step 2: Resolve ConversationState ---
    base = ctx.get_or_create_conversation(request.conversation_id)

    # --- Step 3: Checkpoint intake ---
    base = validate_checkpoint_intake(
        in_memory=base,
        checkpoint_id=request.checkpoint_id,
        checkpoint_payload=request.state_checkpoint,
        turn_number=request.turn_number,
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
        (tmp_path / "src" / "app.py").mkdir(parents=True, exist_ok=True)
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
        scout_req = ScoutRequest(
            schema_version=SCHEMA_VERSION,
            scout_option_id=turn_result.template_candidates[0].scout_option_id,
            scout_token=turn_result.template_candidates[0].scout_token,
            turn_request_ref=turn_result.template_candidates[0].turn_request_ref,
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
        scout_req = ScoutRequest(
            schema_version=SCHEMA_VERSION,
            scout_option_id=turn_result.template_candidates[0].scout_option_id,
            scout_token=turn_result.template_candidates[0].scout_token,
            turn_request_ref=turn_result.template_candidates[0].turn_request_ref,
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
            scout_option_id=candidate.scout_option_id,
            scout_token=candidate.scout_token,
            turn_request_ref=candidate.turn_request_ref,
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
5. Add new ErrorDetail codes: `ledger_hard_reject`, `checkpoint_missing`, `checkpoint_invalid`, `checkpoint_stale`
6. Add conversation flow section: checkpoint pass-through, multi-turn state progression, action computation

**Step 3: Run full suite — final verification**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: ALL tests pass — ~739 updated + ~50-80 new from D1-D4

Run: `cd packages/context-injection && uv run pytest tests/ -v --tb=short 2>&1 | tail -5`
Expected: All pass, zero failures

**Step 4: Commit**

```bash
git add packages/context-injection/tests/test_integration.py docs/references/context-injection-contract.md
git commit -m "feat(context-injection): add 0.2.0 integration tests + update protocol contract (D4 Task 14)

New round-trip, multi-turn, checkpoint, and action flow integration tests.
Protocol contract updated to 0.2.0 schema with ledger validation, conversation
control, and checkpoint fields."
```
