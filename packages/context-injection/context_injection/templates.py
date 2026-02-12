"""Template matching, ranking, and scout option synthesis.

Implements the 3-step decision tree for scout templates:
- Step A (Hard gates): MVP Tier 1 entities at high/medium confidence, in_focus=True
- Step B (Prefer closers): Rank by anchor type, confidence
- Step C (Best anchor): Pick best anchor by same ranking

Plus:
- Clarifier template routing (Tier 2 entities, unresolved file_name)
- Scout option synthesis (ReadOption/GrepOption with HMAC tokens)
- Dedupe via entity_key and template_id from evidence_history
- Resolved-key dedupe for file_name entities that resolve to file_path

Contract reference: docs/references/context-injection-contract.md
"""

from __future__ import annotations

import re
from typing import Literal

from context_injection.canonical import (
    ScoutTokenPayload,
    make_entity_key,
)
from context_injection.state import AppContext, generate_token
from context_injection.types import (
    Budget,
    Clarifier,
    DedupRecord,
    Entity,
    EvidenceRecord,
    GrepOption,
    GrepSpec,
    PathDecision,
    ReadOption,
    ReadSpec,
    TemplateCandidate,
    TurnRequest,
)

# --- Budget constants ---

MAX_EVIDENCE_ITEMS: int = 5
"""Maximum evidence items per conversation."""

MAX_LINES_NORMAL: int = 40
MAX_CHARS_NORMAL: int = 2000
MAX_LINES_RISK: int = 20
MAX_CHARS_RISK: int = 1000
GREP_CONTEXT_LINES: int = 2
GREP_MAX_RANGES: int = 5

# --- Anchor type ranking (lower = better) ---

_ANCHOR_RANK: dict[str, int] = {
    "file_loc": 1,
    "file_path": 2,
    "file_name": 3,
    "symbol": 4,
}

# --- Confidence ranking (lower = better) ---

_CONFIDENCE_RANK: dict[str, int] = {
    "high": 1,
    "medium": 2,
    "low": 3,
}

# --- MVP Tier 1 entity types eligible for probe templates ---

_MVP_TIER1_TYPES: frozenset[str] = frozenset(
    {"file_loc", "file_path", "file_name", "symbol"}
)

# --- Tier 2 entity types for clarifier routing ---

_CLARIFIER_FILE_TYPES: frozenset[str] = frozenset({"file_hint", "file_name"})
_CLARIFIER_SYMBOL_TYPES: frozenset[str] = frozenset({"symbol_hint"})


# --- Line number extraction from raw entity text ---

_COLON_LINE_RE = re.compile(r":(\d+)(?::\d+)?$")
_ANCHOR_LINE_RE = re.compile(r"#L(\d+)$")


def _extract_line_number(raw: str) -> int | None:
    """Extract line number from a file_loc entity's raw text.

    Supports:
    - Colon anchor: config.py:42, src/app.py:10:5
    - GitHub anchor: config.py#L42
    """
    m = _ANCHOR_LINE_RE.search(raw)
    if m:
        return int(m.group(1))
    m = _COLON_LINE_RE.search(raw)
    if m:
        return int(m.group(1))
    return None


# --- Budget computation ---


def compute_budget(evidence_history: list[EvidenceRecord]) -> Budget:
    """Compute budget state from evidence history.

    evidence_count = len(evidence_history) — this IS the floor invariant.
    The history list length reflects reality even if items were evicted from store.
    """
    evidence_count = len(evidence_history)
    evidence_remaining = max(0, MAX_EVIDENCE_ITEMS - evidence_count)
    scout_available = evidence_remaining > 0
    return Budget(
        evidence_count=evidence_count,
        evidence_remaining=evidence_remaining,
        scout_available=scout_available,
    )


# --- Dedupe logic ---


def _compute_effective_key(
    entity: Entity,
    entities_by_id: dict[str, Entity],
) -> str:
    """Compute the effective entity key for dedupe purposes.

    For entities with resolved_to, use the resolved entity's type and canonical form.
    This implements resolved-key dedupe: if file_name:config.yaml resolves to
    file_path:src/config.yaml, dedupe checks against file_path:src/config.yaml.
    """
    if entity.resolved_to is not None:
        resolved = entities_by_id.get(entity.resolved_to)
        if resolved is not None:
            return make_entity_key(resolved.type, resolved.canonical)
    return make_entity_key(entity.type, entity.canonical)


def _check_dedupe(
    entity: Entity,
    template_id: str,
    evidence_history: list[EvidenceRecord],
    entities_by_id: dict[str, Entity],
) -> DedupRecord | None:
    """Check if an entity/template combination is deduped.

    Returns a DedupRecord if deduped, None otherwise.

    Check order (specific first):
    1. template_already_used: Same (entity_key + template_id) pair
    2. entity_already_scouted: Same entity_key with a different template

    For probe templates, uses the resolved key (effective probed target).
    """
    effective_key = _compute_effective_key(entity, entities_by_id)

    # Check template_already_used first (more specific: same entity + same template)
    for record in evidence_history:
        if record.entity_key == effective_key and record.template_id == template_id:
            return DedupRecord(
                entity_key=effective_key,
                template_id=template_id,
                reason="template_already_used",
                prior_turn=record.turn,
            )

    # Check entity_already_scouted (more general: same entity, any template)
    for record in evidence_history:
        if record.entity_key == effective_key:
            return DedupRecord(
                entity_key=effective_key,
                template_id=None,
                reason="entity_already_scouted",
                prior_turn=record.turn,
            )

    return None


# --- Template matching ---


def _get_path_decision(
    entity_id: str,
    path_decisions: list[PathDecision],
) -> PathDecision | None:
    """Look up the PathDecision for an entity by ID."""
    for pd in path_decisions:
        if pd.entity_id == entity_id:
            return pd
    return None


def _resolve_scout_target(
    entity: Entity,
    pd: PathDecision | None,
    entities_by_id: dict[str, Entity],
) -> str:
    """Resolve the display target for a scout option.

    For file_name entities with resolved_to, use the resolved entity's canonical.
    For others, use resolved_rel from PathDecision, falling back to canonical.
    """
    if entity.resolved_to is not None:
        resolved = entities_by_id.get(entity.resolved_to)
        if resolved is not None:
            return resolved.canonical
    if pd is not None and pd.resolved_rel is not None:
        return pd.resolved_rel
    return entity.canonical


def _resolve_scout_path(
    entity: Entity,
    pd: PathDecision | None,
    entities_by_id: dict[str, Entity],
) -> str:
    """Resolve the file path for ReadSpec (the actual path to read).

    Uses resolved_rel from PathDecision when available, otherwise falls back
    to the resolved entity's canonical or the entity's own canonical.
    """
    if pd is not None and pd.resolved_rel is not None:
        return pd.resolved_rel
    if entity.resolved_to is not None:
        resolved = entities_by_id.get(entity.resolved_to)
        if resolved is not None:
            return resolved.canonical
    return entity.canonical


def _make_read_option(
    entity: Entity,
    pd: PathDecision,
    turn_request: TurnRequest,
    ctx: AppContext,
    entities_by_id: dict[str, Entity],
    so_counter: list[int],
    spec_registry: dict[str, tuple[ReadSpec | GrepSpec, str]],
) -> ReadOption:
    """Create a ReadOption with HMAC token for a file entity.

    Side effect: registers (spec, token) in spec_registry for Call 2 validation.
    """
    risk = pd.risk_signal
    max_lines = MAX_LINES_RISK if risk else MAX_LINES_NORMAL
    max_chars = MAX_CHARS_RISK if risk else MAX_CHARS_NORMAL

    # Determine strategy and center_line
    if entity.type == "file_loc":
        strategy: Literal["first_n", "centered"] = "centered"
        center_line = _extract_line_number(entity.raw)
    else:
        strategy = "first_n"
        center_line = None

    target_display = _resolve_scout_target(entity, pd, entities_by_id)
    resolved_path = _resolve_scout_path(entity, pd, entities_by_id)

    so_counter[0] += 1
    so_id = f"so_{so_counter[0]:03d}"

    # Build spec for HMAC signing
    spec = ReadSpec(
        action="read",
        resolved_path=resolved_path,
        strategy=strategy,
        max_lines=max_lines,
        max_chars=max_chars,
        center_line=center_line,
    )
    payload = ScoutTokenPayload(
        v=1,
        conversation_id=turn_request.conversation_id,
        turn_number=turn_request.turn_number,
        scout_option_id=so_id,
        spec=spec,
    )
    token = generate_token(ctx.hmac_key, payload)

    spec_registry[so_id] = (spec, token)

    return ReadOption(
        id=so_id,
        scout_token=token,
        action="read",
        target_display=target_display,
        strategy=strategy,
        max_lines=max_lines,
        max_chars=max_chars,
        risk_signal=risk,
        center_line=center_line,
    )


def _make_grep_option(
    entity: Entity,
    turn_request: TurnRequest,
    ctx: AppContext,
    so_counter: list[int],
    spec_registry: dict[str, tuple[ReadSpec | GrepSpec, str]],
) -> GrepOption:
    """Create a GrepOption with HMAC token for a symbol entity.

    Side effect: registers (spec, token) in spec_registry for Call 2 validation.
    """
    so_counter[0] += 1
    so_id = f"so_{so_counter[0]:03d}"

    spec = GrepSpec(
        action="grep",
        pattern=entity.canonical,
        strategy="match_context",
        max_lines=MAX_LINES_NORMAL,
        max_chars=MAX_CHARS_NORMAL,
        context_lines=GREP_CONTEXT_LINES,
        max_ranges=GREP_MAX_RANGES,
    )
    payload = ScoutTokenPayload(
        v=1,
        conversation_id=turn_request.conversation_id,
        turn_number=turn_request.turn_number,
        scout_option_id=so_id,
        spec=spec,
    )
    token = generate_token(ctx.hmac_key, payload)

    spec_registry[so_id] = (spec, token)

    return GrepOption(
        id=so_id,
        scout_token=token,
        action="grep",
        target_display=entity.canonical,
        strategy="match_context",
        max_lines=MAX_LINES_NORMAL,
        max_chars=MAX_CHARS_NORMAL,
        context_lines=GREP_CONTEXT_LINES,
        max_ranges=GREP_MAX_RANGES,
    )


def _make_clarifier(
    entity: Entity,
    pd: PathDecision | None,
) -> Clarifier:
    """Build a clarifier question for a clarifier template."""
    if pd is not None and pd.candidates:
        return Clarifier(
            question=f"Which file do you mean by '{entity.raw}'?",
            choices=list(pd.candidates),
        )
    if entity.type == "file_hint" or entity.type == "file_name":
        return Clarifier(
            question=f"Which file do you mean by '{entity.raw}'?",
            choices=None,
        )
    # symbol_hint
    return Clarifier(
        question=f"Which symbol do you mean by '{entity.raw}'?",
        choices=None,
    )


def _sort_key(entity: Entity) -> tuple[int, int]:
    """Sort key for ranking: (anchor_rank, confidence_rank). Lower = better."""
    anchor = _ANCHOR_RANK.get(entity.type, 99)
    confidence = _CONFIDENCE_RANK.get(entity.confidence, 99)
    return (anchor, confidence)


def _rank_factors_str(entity: Entity) -> str:
    """Build human-readable rank factors string."""
    anchor = _ANCHOR_RANK.get(entity.type, 99)
    return f"anchor_type={entity.type}(rank={anchor}), confidence={entity.confidence}"


# --- Public API ---


def match_templates(
    entities: list[Entity],
    path_decisions: list[PathDecision],
    evidence_history: list[EvidenceRecord],
    turn_request: TurnRequest,
    ctx: AppContext,
) -> tuple[
    list[TemplateCandidate],
    list[DedupRecord],
    dict[str, tuple[ReadSpec | GrepSpec, str]],
]:
    """Match entities to templates, rank, synthesize scout options.

    Returns (template_candidates, dedup_records, spec_registry).

    spec_registry maps scout_option_id -> (frozen ScoutSpec, HMAC token).
    Used by pipeline.py to populate TurnRequestRecord.scout_options for Call 2.

    Decision tree:
    1. Clarifier routing: Tier 2 entities and unresolved file_name → clarify templates
    2. Hard gate (Step A): MVP Tier 1, high/medium confidence, in_focus=True
    3. Path decision gating: Only status=allowed entities get probe templates
    4. Budget gating: No probes if budget exhausted
    5. Dedupe: Filter already-scouted entities
    6. Ranking (Steps B+C): Sort by anchor type, confidence
    7. Scout option synthesis: Create ReadOption/GrepOption with HMAC tokens
    """
    if not entities:
        return [], [], {}

    budget = compute_budget(evidence_history)
    entities_by_id: dict[str, Entity] = {e.id: e for e in entities}

    tc_counter = 0
    so_counter = [0]  # Mutable for nested function access
    spec_registry: dict[str, tuple[ReadSpec | GrepSpec, str]] = {}
    candidates: list[TemplateCandidate] = []
    dedup_records: list[DedupRecord] = []

    # --- Phase 1: Clarifier routing ---

    clarifier_entities: list[Entity] = []
    probe_entities: list[Entity] = []

    for entity in entities:
        # Tier 2 entities always route to clarifiers
        if entity.tier == 2:
            clarifier_entities.append(entity)
            continue

        # Unresolved file_name entities route to clarifiers
        if entity.type == "file_name":
            pd = _get_path_decision(entity.id, path_decisions)
            if pd is not None and pd.status == "unresolved":
                clarifier_entities.append(entity)
                continue
            # file_name without resolved_to and no path_decision also clarifies
            if entity.resolved_to is None and pd is None:
                clarifier_entities.append(entity)
                continue

        # Everything else goes to probe consideration
        probe_entities.append(entity)

    # Build clarifier candidates
    for entity in clarifier_entities:
        pd = _get_path_decision(entity.id, path_decisions)

        if entity.type in _CLARIFIER_FILE_TYPES:
            template_id = "clarify.file_path"
        elif entity.type in _CLARIFIER_SYMBOL_TYPES:
            template_id = "clarify.symbol"
        else:
            # Unknown Tier 2 type — skip
            continue

        tc_counter += 1
        clarifier = _make_clarifier(entity, pd)
        candidates.append(
            TemplateCandidate(
                id=f"tc_{tc_counter:03d}",
                template_id=template_id,
                entity_id=entity.id,
                focus_affinity=entity.in_focus,
                rank=tc_counter,  # Clarifiers ranked after probes, but in order
                rank_factors=f"clarifier for {entity.type}",
                scout_options=[],
                clarifier=clarifier,
            )
        )

    # --- Phase 2: Probe template matching ---

    # Collect eligible entities after applying gates
    eligible: list[tuple[Entity, PathDecision | None]] = []

    for entity in probe_entities:
        # Step A: Hard gate — MVP Tier 1 only
        if entity.type not in _MVP_TIER1_TYPES:
            continue

        # Step A: Confidence gate — high/medium only
        if entity.confidence == "low":
            continue

        # Step A: Focus-affinity gate — must be in_focus
        if not entity.in_focus:
            continue

        # Budget gate — no probes if budget exhausted
        if not budget.scout_available:
            continue

        # Path decision gating for file entities
        if entity.type in ("file_loc", "file_path", "file_name"):
            pd = _get_path_decision(entity.id, path_decisions)
            if pd is None:
                continue
            if pd.status != "allowed":
                continue
        else:
            pd = None

        # Dedupe check
        if entity.type == "symbol":
            template_id = "probe.symbol_repo_fact"
        else:
            template_id = "probe.file_repo_fact"

        dedup = _check_dedupe(entity, template_id, evidence_history, entities_by_id)
        if dedup is not None:
            dedup_records.append(dedup)
            continue

        eligible.append((entity, pd))

    # Step B+C: Sort by anchor type, then confidence
    eligible.sort(key=lambda pair: _sort_key(pair[0]))

    # Build probe candidates with ranking
    for rank_idx, (entity, pd) in enumerate(eligible, start=1):
        if entity.type == "symbol":
            template_id = "probe.symbol_repo_fact"
            scout_option = _make_grep_option(
                entity, turn_request, ctx, so_counter, spec_registry
            )
            scout_options: list[ReadOption | GrepOption] = [scout_option]
        else:
            template_id = "probe.file_repo_fact"
            assert pd is not None  # Guaranteed by gating above
            scout_option = _make_read_option(
                entity,
                pd,
                turn_request,
                ctx,
                entities_by_id,
                so_counter,
                spec_registry,
            )
            scout_options = [scout_option]

        tc_counter += 1
        candidates.append(
            TemplateCandidate(
                id=f"tc_{tc_counter:03d}",
                template_id=template_id,
                entity_id=entity.id,
                focus_affinity=entity.in_focus,
                rank=rank_idx,
                rank_factors=_rank_factors_str(entity),
                scout_options=scout_options,
                clarifier=None,
            )
        )

    # Re-rank: probes get ranks 1..N, clarifiers get ranks N+1..
    # Reassign ranks to ensure probes come first
    probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
    clarifier_candidates = [
        c for c in candidates if c.template_id.startswith("clarify.")
    ]

    final_candidates: list[TemplateCandidate] = []
    rank = 0
    for c in probe_candidates:
        rank += 1
        # Reconstruct with correct rank (models are frozen)
        final_candidates.append(
            TemplateCandidate(
                id=c.id,
                template_id=c.template_id,
                entity_id=c.entity_id,
                focus_affinity=c.focus_affinity,
                rank=rank,
                rank_factors=c.rank_factors,
                scout_options=c.scout_options,
                clarifier=c.clarifier,
            )
        )
    for c in clarifier_candidates:
        rank += 1
        final_candidates.append(
            TemplateCandidate(
                id=c.id,
                template_id=c.template_id,
                entity_id=c.entity_id,
                focus_affinity=c.focus_affinity,
                rank=rank,
                rank_factors=c.rank_factors,
                scout_options=c.scout_options,
                clarifier=c.clarifier,
            )
        )

    return final_candidates, dedup_records, spec_registry
