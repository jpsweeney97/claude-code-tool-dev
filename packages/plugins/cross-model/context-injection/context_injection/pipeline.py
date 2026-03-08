"""Call 1 pipeline: TurnRequest -> TurnPacketSuccess | TurnPacketError.

Composes the full v0.2.0 processing pipeline (17 steps per contract):
 1. Schema version validation
 2. Dual-claims channel guard (CC-PF-3)
 3. Resolve ConversationState (in-memory or create)
 4. Checkpoint intake (restore from checkpoint if needed)
 5. Turn cap guard
 6. Snapshot prior state (claims + evidence from conversation state)
 7. Entity extraction (regex on focus claims/unresolved + prior claims)
 8. Entity type disambiguation
 9. Path canonicalization and denylist check
10. Template matching (with prior evidence for dedupe)
11. Budget computation (from prior evidence)
12. Ledger entry validation (compute counters, quality, effective_delta)
13. Build provisional state (append entry)
14. Compute cumulative state, action, reason
15. Closing probe projection
16. Serialize checkpoint
17. Generate ledger summary, store record, commit state, return TurnPacketSuccess

Contract reference: packages/plugins/cross-model/references/context-injection-contract.md
"""

from __future__ import annotations

import logging

from context_injection.checkpoint import (
    MAX_ENTRIES_BEFORE_COMPACT,
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
if MAX_CONVERSATION_TURNS >= MAX_ENTRIES_BEFORE_COMPACT:
    raise RuntimeError(
        f"MAX_CONVERSATION_TURNS ({MAX_CONVERSATION_TURNS}) must be strictly less than "
        f"MAX_ENTRIES_BEFORE_COMPACT ({MAX_ENTRIES_BEFORE_COMPACT}). "
        "See DD-2 (C-lite) invariant."
    )

# Entity types that require compile-time path checking.
# file_loc, file_path, file_name have file paths; symbol is grep-based (no path).
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
    """Inner pipeline logic -- 17-step orchestration."""

    # --- Step 1: Schema version validation (contract step 1) ---
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

    # --- Step 2: Dual-claims channel guard (CC-PF-3) ---
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

    # --- Step 3: Resolve ConversationState ---
    base = ctx.get_or_create_conversation(request.conversation_id)

    # --- Step 4: Checkpoint intake ---
    base = validate_checkpoint_intake(
        in_memory=base,
        checkpoint_id=request.checkpoint_id,
        checkpoint_payload=request.state_checkpoint,
        turn_number=request.turn_number,
        target_conversation_id=request.conversation_id,
    )

    # --- Step 5: Turn cap guard (CC-4/CC-5/DD-2) ---
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

    # --- Step 6: Snapshot prior state ---
    prior_claims: list[Claim] = base.get_cumulative_claims()
    prior_evidence = base.get_evidence_history()

    # --- Steps 7-8: Entity extraction + disambiguation ---
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

    # --- Step 9: Path canonicalization and denylist check ---
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

    # --- Step 10: Template matching (with prior evidence for dedupe) ---
    template_candidates, dedup_records, spec_registry = match_templates(
        entities,
        path_decisions,
        prior_evidence,
        request,
        ctx,
    )

    # --- Step 11: Budget computation (from prior evidence) ---
    budget = compute_budget(prior_evidence)

    # --- Step 12: Ledger entry validation ---
    # Compute per-turn unresolved closures: items in the previous turn's
    # unresolved list that are absent from the current turn's list.
    if base.entries:
        prior_unresolved_texts = frozenset(u.text for u in base.entries[-1].unresolved)
        current_unresolved_texts = frozenset(u.text for u in request.unresolved)
        unresolved_closed = len(prior_unresolved_texts - current_unresolved_texts)
    else:
        unresolved_closed = 0
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

    # --- Step 13: Build provisional state ---
    provisional = base.with_turn(validated_entry)

    # --- Step 14: Compute cumulative, action, reason ---
    cumulative = provisional.compute_cumulative_state()
    turn_budget_remaining = max(0, MAX_CONVERSATION_TURNS - cumulative.turns_completed)

    # Reconcile posture metadata — track phase boundaries
    current_posture = request.posture
    if provisional.last_posture is None:
        # First turn with posture tracking — set initial posture
        provisional = provisional.with_posture_change(
            current_posture, phase_start_index=0
        )
    elif current_posture != provisional.last_posture:
        # Posture changed — new phase starts at the latest entry
        provisional = provisional.with_posture_change(
            current_posture, phase_start_index=len(provisional.entries) - 1
        )

    # Always derive phase window after posture reconciliation
    phase_entries = provisional.get_phase_entries()

    action, action_reason = compute_action(
        entries=provisional.entries,
        budget_remaining=turn_budget_remaining,
        closing_probe_fired=provisional.closing_probe_fired,
        phase_entries=phase_entries,
    )

    # --- Step 15: Closing probe projection ---
    if action == "closing_probe":
        projected = provisional.with_closing_probe_fired()
    else:
        projected = provisional

    # --- Step 16: Serialize checkpoint ---
    projected = compact_ledger(projected)
    serialized = serialize_checkpoint(state=projected)
    projected = serialized.state
    checkpoint_id = serialized.checkpoint_id
    checkpoint_string = serialized.checkpoint_string

    # --- Step 17: Generate ledger summary, store record, commit state, return ---
    ledger_summary = generate_ledger_summary(
        entries=projected.entries,
        cumulative=cumulative,
    )

    ref = make_turn_request_ref(request)
    record = TurnRequestRecord(
        turn_request=request,
        scout_options=spec_registry,
    )
    ctx.store_record(ref, record)

    ctx.conversations[request.conversation_id] = projected
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
