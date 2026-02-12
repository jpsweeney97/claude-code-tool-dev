"""Call 1 pipeline: TurnRequest -> TurnPacketSuccess | TurnPacketError.

Composes the full v0a processing pipeline:
1. Schema version validation
2. Entity extraction from focus.claims, focus.unresolved, context_claims
3. Path checking for Tier 1 file entities
4. Template matching and ranking
5. Budget computation
6. TurnRequest storage for Call 2 validation

This is the top-level orchestration module. It imports from entities, paths,
templates, state, and types but contains no domain logic of its own.

Contract reference: docs/references/context-injection-contract.md
"""

from __future__ import annotations

import logging

from context_injection.entities import extract_entities
from context_injection.paths import check_path_compile_time
from context_injection.state import (
    AppContext,
    TurnRequestRecord,
    make_turn_request_ref,
)
from context_injection.templates import compute_budget, match_templates
from context_injection.types import (
    SCHEMA_VERSION,
    Entity,
    ErrorDetail,
    PathDecision,
    TurnPacketError,
    TurnPacketSuccess,
    TurnRequest,
)

logger = logging.getLogger(__name__)

# Entity types that require compile-time path checking.
# file_loc, file_path, file_name have file paths; symbol is grep-based (no path).
_PATH_CHECK_TYPES: frozenset[str] = frozenset({"file_loc", "file_path", "file_name"})


def process_turn(
    request: TurnRequest,
    ctx: AppContext,
) -> TurnPacketSuccess | TurnPacketError:
    """Process a Call 1 TurnRequest through the full pipeline.

    Steps:
    1. Validate schema_version (exact match for 0.x)
    2. Extract entities from focus.claims, focus.unresolved, context_claims
    3. Check paths for Tier 1 file entities (file_loc, file_path, file_name)
    4. Match templates + rank
    5. Compute budget from evidence_history
    6. Store TurnRequest + spec_registry for Call 2 validation
    7. Return TurnPacketSuccess

    Any unhandled exception produces TurnPacketError with internal_error code.
    """
    try:
        return _process_turn_inner(request, ctx)
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
    """Inner pipeline logic, not exception-wrapped."""

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

    # --- Step 2: Entity extraction ---
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

    for unresolved in request.focus.unresolved:
        entities.extend(
            extract_entities(
                unresolved.text,
                source_type="unresolved",
                in_focus=True,
                ctx=ctx,
            )
        )

    for claim in request.context_claims:
        entities.extend(
            extract_entities(
                claim.text,
                source_type="claim",
                in_focus=False,
                ctx=ctx,
            )
        )

    # --- Step 3: Path checking for Tier 1 file entities ---
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

    # --- Step 4: Template matching ---
    template_candidates, dedup_records, spec_registry = match_templates(
        entities,
        path_decisions,
        request.evidence_history,
        request,
        ctx,
    )

    # --- Step 5: Budget computation ---
    budget = compute_budget(request.evidence_history)

    # --- Step 6: Store TurnRequest for Call 2 ---
    ref = make_turn_request_ref(request)
    record = TurnRequestRecord(
        turn_request=request,
        scout_options=spec_registry,
    )
    ctx.store_record(ref, record)

    # --- Step 7: Assemble success response ---
    return TurnPacketSuccess(
        schema_version=SCHEMA_VERSION,
        status="success",
        entities=entities,
        path_decisions=path_decisions,
        template_candidates=template_candidates,
        budget=budget,
        deduped=dedup_records,
    )
