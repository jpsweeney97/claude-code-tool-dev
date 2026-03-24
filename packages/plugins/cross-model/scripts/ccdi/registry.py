"""CCDI session registry — Phase A + Phase B deferred/TTL + hints + consecutive-medium.

Manages per-topic state transitions: load, inject, suppress, defer, persist.
Atomic file writes via temp+rename. Fingerprint normalization for
deduplication. TTL lifecycle for deferred entries. Semantic hint processing
and consecutive-medium tracking.

Import pattern:
    from scripts.ccdi.registry import (
        load_registry, mark_injected, write_suppressed, write_deferred,
        decrement_deferred_ttl, apply_ttl_transitions,
        update_redetections, process_semantic_hints,
    )
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from typing import Callable

from scripts.ccdi.config import CCDIConfig
from scripts.ccdi.types import (
    ClassifierResult,
    CompiledInventory,
    InjectionCandidate,
    RegistrySeed,
    ResolvedTopic,
    SemanticHint,
    TopicRegistryEntry,
)

logger = logging.getLogger(__name__)

# Attempt-local states that must not survive persistence
_ATTEMPT_STATES: frozenset[str] = frozenset({"looked_up", "built"})

# Confidence ordering for scheduling tiebreaker (higher = earlier)
_CONFIDENCE_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

# Whitespace collapse pattern
_WS_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Fingerprint normalization
# ---------------------------------------------------------------------------


def normalize_fingerprint(query: str, docs_epoch: str | None) -> str:
    """Normalize query + docs_epoch into a stable fingerprint.

    - query: lowercase + collapse whitespace
    - docs_epoch: null becomes literal string 'null'
    """
    normalized_query = _WS_RE.sub(" ", query.lower()).strip()
    epoch_str = "null" if docs_epoch is None else str(docs_epoch)
    return f"{normalized_query}|{epoch_str}"


# ---------------------------------------------------------------------------
# Suppression re-entry check
# ---------------------------------------------------------------------------


def check_suppression_reentry(
    entries: list[TopicRegistryEntry],
    current_docs_epoch: str | None,
) -> list[TopicRegistryEntry]:
    """Check which suppressed entries should re-enter detected state.

    Only applies to suppression_reason == "weak_results".
    Re-entry occurs when suppressed_docs_epoch differs from current_docs_epoch,
    with null-handling:
    - null == null -> no re-entry
    - null != non-null -> re-entry
    - non-null != null -> re-entry
    - non-null A != non-null B -> re-entry
    """
    reentry: list[TopicRegistryEntry] = []
    for entry in entries:
        if entry.state != "suppressed":
            continue
        if entry.suppression_reason != "weak_results":
            continue

        suppressed_epoch = entry.suppressed_docs_epoch
        # Both null -> no change
        if suppressed_epoch is None and current_docs_epoch is None:
            continue
        # Both non-null and equal -> no change
        if suppressed_epoch == current_docs_epoch:
            continue
        # Any other combo -> re-entry
        reentry.append(entry)

    return reentry


# ---------------------------------------------------------------------------
# Scheduling tiebreaker
# ---------------------------------------------------------------------------


def sort_candidates(
    candidates: list[tuple[TopicRegistryEntry, str]],
) -> list[tuple[TopicRegistryEntry, str]]:
    """Sort candidate entries for scheduling.

    Order:
    1. Confidence descending (high > medium > low)
    2. first_seen_turn ascending
    3. topic_key lexicographic ascending
    """
    return sorted(
        candidates,
        key=lambda pair: (
            _CONFIDENCE_ORDER.get(pair[1], 99),
            pair[0].first_seen_turn,
            pair[0].topic_key,
        ),
    )


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------


def _write_registry(path: str, seed: RegistrySeed) -> None:
    """Atomic write: temp file + rename. Uses RegistrySeed.to_json()."""
    data = seed.to_json()
    dir_path = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_registry(path: str) -> RegistrySeed:
    """Load registry file. Strip transport fields, validate entries.

    - Strip results_file and inventory_snapshot_path (warn if present)
    - Validate family-kind entries have consecutive_medium_count=0 (reset + warn if not)
    - Handle attempt-local states (looked_up, built) by reinitializing to detected
    - Handle inventory_snapshot_version null/empty/absent as version mismatch (warn)
    - On corrupt JSON: reinitialize empty registry, warn
    - On missing file: return empty registry
    """
    if not os.path.exists(path):
        logger.info("Registry file not found at %s — initializing empty", path)
        return RegistrySeed(
            entries=[],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )

    try:
        with open(path) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        logger.warning(
            "Registry file corrupt at %s — reinitializing empty: %s",
            path,
            exc,
        )
        return RegistrySeed(
            entries=[],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )

    # RegistrySeed.from_json handles transport stripping and ISV warnings
    seed = RegistrySeed.from_json(raw)

    # Post-load validation on entries
    for entry in seed.entries:
        # Attempt-local states -> detected
        if entry.state in _ATTEMPT_STATES:
            logger.warning(
                "Registry entry %r has attempt-local state %r — resetting to detected",
                entry.topic_key,
                entry.state,
            )
            entry.state = "detected"

        # Family-kind entries must have consecutive_medium_count=0
        if entry.kind == "family" and entry.consecutive_medium_count != 0:
            logger.warning(
                "Registry entry %r (family) has consecutive_medium_count=%d — resetting to 0",
                entry.topic_key,
                entry.consecutive_medium_count,
            )
            entry.consecutive_medium_count = 0

    return seed


# ---------------------------------------------------------------------------
# Mark injected
# ---------------------------------------------------------------------------


def mark_injected(
    path: str,
    topic_key: str,
    facet: str,
    coverage_target: str,
    chunk_ids: list[str],
    query_fingerprint: str,
    turn: int,
) -> None:
    """Commit injection for a topic entry.

    Updates: state->injected, last_injected_turn, last_query_fingerprint,
    coverage.injected_chunk_ids (append, dedupe), coverage.facets_injected
    (append, dedupe), coverage.pending_facets (remove served facet),
    consecutive_medium_count->0, deferred_reason->null, deferred_ttl->null.

    If coverage_target=family and facet=overview: set coverage.overview_injected=true.
    Propagates family_context_available to same-family leaf entries when overview injected.
    Idempotent: double-call doesn't corrupt.
    """
    seed = load_registry(path)

    entry = _find_entry(seed, topic_key)
    if entry is None:
        logger.warning("mark_injected: topic_key %r not found in registry", topic_key)
        return

    # State transition
    entry.state = "injected"
    entry.last_injected_turn = turn
    entry.consecutive_medium_count = 0
    entry.deferred_reason = None
    entry.deferred_ttl = None

    # Fingerprint
    entry.last_query_fingerprint = normalize_fingerprint(
        query_fingerprint, seed.docs_epoch
    )

    # Coverage: injected_chunk_ids — dedupe (handle corrupt input too)
    existing_ids = set(entry.coverage_injected_chunk_ids)
    for cid in chunk_ids:
        if cid not in existing_ids:
            entry.coverage_injected_chunk_ids.append(cid)
            existing_ids.add(cid)
    # Enforce uniqueness on the full list (handles pre-existing duplicates)
    seen: set[str] = set()
    deduped: list[str] = []
    for cid in entry.coverage_injected_chunk_ids:
        if cid not in seen:
            deduped.append(cid)
            seen.add(cid)
    entry.coverage_injected_chunk_ids = deduped

    # Coverage: facets_injected — dedupe
    if facet not in entry.coverage_facets_injected:
        entry.coverage_facets_injected.append(facet)

    # Coverage: pending_facets — remove served facet
    entry.coverage_pending_facets = [
        f for f in entry.coverage_pending_facets if f != facet
    ]

    # Coverage: overview_injected
    if coverage_target == "family" and facet == "overview":
        entry.coverage_overview_injected = True

    # Propagate family_context_available to leaves
    _propagate_family_context(seed, entry)

    _write_registry(path, seed)


# ---------------------------------------------------------------------------
# Write suppressed
# ---------------------------------------------------------------------------


def write_suppressed(
    path: str,
    topic_key: str,
    reason: str,
    docs_epoch: str | None,
) -> None:
    """Record suppression for a topic entry.

    Sets state->suppressed, suppression_reason, suppressed_docs_epoch.
    """
    seed = load_registry(path)

    entry = _find_entry(seed, topic_key)
    if entry is None:
        logger.warning("write_suppressed: topic_key %r not found in registry", topic_key)
        return

    entry.state = "suppressed"
    entry.suppression_reason = reason
    entry.suppressed_docs_epoch = docs_epoch

    _write_registry(path, seed)


# ---------------------------------------------------------------------------
# Write deferred
# ---------------------------------------------------------------------------


def write_deferred(
    path: str,
    topic_key: str,
    reason: str,
    deferred_ttl: int,
) -> None:
    """Record deferral for a topic.

    reason: 'cooldown' | 'scout_priority' | 'target_mismatch'.
    Sets state -> deferred, deferred_reason, deferred_ttl.
    consecutive_medium_count is preserved (not reset by deferral).
    """
    seed = load_registry(path)
    entry = _find_entry(seed, topic_key)
    if entry is None:
        logger.warning("write_deferred: topic_key %r not found in registry", topic_key)
        return
    entry.state = "deferred"
    entry.deferred_reason = reason
    entry.deferred_ttl = deferred_ttl
    _write_registry(path, seed)


# ---------------------------------------------------------------------------
# TTL lifecycle
# ---------------------------------------------------------------------------


def decrement_deferred_ttl(seed: RegistrySeed) -> None:
    """Decrement deferred_ttl by 1 for all deferred entries.

    Per registry.md#ttl-lifecycle: each dialogue-turn invocation decrements
    deferred_ttl by 1 for all entries in deferred state.

    This is a low-level primitive. For full per-turn processing, use
    apply_ttl_transitions() instead -- it handles TTL=0 transitions,
    high-confidence bypass, AND the per-turn decrement in one call.
    Do NOT call both apply_ttl_transitions() and decrement_deferred_ttl()
    in the same turn -- that would double-decrement.
    """
    for entry in seed.entries:
        if entry.state == "deferred" and entry.deferred_ttl is not None:
            entry.deferred_ttl -= 1


def apply_ttl_transitions(
    seed: RegistrySeed,
    classifier_topic_keys: set[str],
    classifier_confidences: dict[str, str],
    config: CCDIConfig,
) -> list[TopicRegistryEntry]:
    """Apply TTL transition rules to deferred entries. Returns transitioned entries.

    Processing order per registry.md:
    1. High-confidence bypass: deferred entries re-detected at high confidence
       transition to detected immediately, regardless of TTL value.
    2. Load-time recovery (TTL=0): apply transition rule BEFORE per-turn
       decrement. TTL=0 + classifier presence -> detected.
       TTL=0 + absent -> reset TTL, stay deferred.
    3. Per-turn decrement: decrement all remaining deferred entries by 1.

    consecutive_medium_count initialization on deferred -> detected:
    - 1 if medium confidence AND leaf-kind
    - 0 otherwise (high, low, family-kind, absent-from-classifier)
    """
    transitioned: list[TopicRegistryEntry] = []

    for entry in seed.entries:
        if entry.state != "deferred":
            continue

        topic_key = entry.topic_key
        confidence = classifier_confidences.get(topic_key)

        # Step 1: High-confidence bypass (any TTL value)
        if topic_key in classifier_topic_keys and confidence == "high":
            entry.state = "detected"
            entry.deferred_reason = None
            entry.deferred_ttl = None
            entry.consecutive_medium_count = 0
            transitioned.append(entry)
            continue

        # Step 2: TTL=0 transition (load-time recovery)
        if entry.deferred_ttl == 0:
            if topic_key in classifier_topic_keys:
                # deferred -> detected
                entry.state = "detected"
                entry.deferred_reason = None
                entry.deferred_ttl = None
                # consecutive_medium_count: 1 if medium AND leaf, else 0
                if confidence == "medium" and entry.kind == "leaf":
                    entry.consecutive_medium_count = 1
                else:
                    entry.consecutive_medium_count = 0
                transitioned.append(entry)
            else:
                # deferred -> deferred (TTL reset)
                entry.deferred_ttl = config.injection_deferred_ttl_turns
                # consecutive_medium_count -> 0 (absent from classifier)
                entry.consecutive_medium_count = 0
            continue

        # Step 3: Per-turn decrement for TTL > 0
        if entry.deferred_ttl is not None:
            entry.deferred_ttl -= 1

    return transitioned


# ---------------------------------------------------------------------------
# Consecutive-medium tracking
# ---------------------------------------------------------------------------


def update_redetections(
    seed: RegistrySeed,
    classifier_results: list[ResolvedTopic],
    current_turn: int,
) -> None:
    """Update existing registry entries based on classifier re-detection.

    In-memory function — mutates seed.entries directly. Does NOT handle new
    topic creation (absent → detected). Only updates fields on EXISTING entries.

    Per registry.md field update rules:
    - Re-detection at medium (leaf-kind only): increment consecutive_medium_count
    - Re-detection at non-medium: reset consecutive_medium_count to 0
    - Re-detection on injected: update last_seen_turn only
    - Re-detection on suppressed: no update
    - Topic absent from classifier (non-suppressed): reset consecutive_medium_count to 0
    """
    # Build lookup of classifier results by topic_key
    classifier_by_key: dict[str, ResolvedTopic] = {}
    for rt in classifier_results:
        classifier_by_key[rt.topic_key] = rt

    classifier_keys = set(classifier_by_key.keys())

    for entry in seed.entries:
        topic_key = entry.topic_key

        # Suppressed entries: no update from re-detection
        if entry.state == "suppressed":
            continue

        if topic_key in classifier_keys:
            resolved = classifier_by_key[topic_key]

            if entry.state == "injected":
                # Forward-only: only update last_seen_turn
                entry.last_seen_turn = current_turn
                continue

            # detected or deferred state
            entry.last_seen_turn = current_turn

            if resolved.confidence == "medium" and entry.kind == "leaf":
                entry.consecutive_medium_count += 1
            elif resolved.confidence == "medium" and entry.kind == "family":
                # Family-kind: last_seen_turn updated but count unchanged
                pass
            else:
                # Non-medium confidence: reset count
                entry.consecutive_medium_count = 0
        else:
            # Topic absent from classifier — reset count (non-suppressed only)
            entry.consecutive_medium_count = 0


# ---------------------------------------------------------------------------
# Semantic hint processing
# ---------------------------------------------------------------------------


def _reenter_suppressed(entry: TopicRegistryEntry, current_turn: int) -> None:
    """Transition a suppressed entry back to detected.

    Per registry.md: state=detected, suppression_reason=null,
    suppressed_docs_epoch=null, last_seen_turn=current_turn.
    """
    entry.state = "detected"
    entry.suppression_reason = None
    entry.suppressed_docs_epoch = None
    entry.last_seen_turn = current_turn


def _transition_deferred_to_detected(
    entry: TopicRegistryEntry, current_turn: int
) -> None:
    """Transition a deferred entry to detected via hint elevation.

    Per registry.md: clears deferred_reason, deferred_ttl, updates last_seen_turn.
    """
    entry.state = "detected"
    entry.deferred_reason = None
    entry.deferred_ttl = None
    entry.last_seen_turn = current_turn


def _resolve_facet_expansion(
    entry: TopicRegistryEntry,
    resolved_facet: str,
    inventory: CompiledInventory,
) -> str | None:
    """Resolve the facet for a facet_expansion candidate via cascade.

    Cascade per registry.md scheduling step 9:
    1. facet resolved from claim_excerpt classification
    2. pending_facets[0] if resolved facet already in facets_injected
    3. default_facet if all pending facets exhausted
    Returns None if all candidate facets are already in facets_injected.
    """
    injected = set(entry.coverage_facets_injected)

    # Step 1: resolved facet
    if resolved_facet not in injected:
        return resolved_facet

    # Step 2: pending_facets
    for pending_facet in entry.coverage_pending_facets:
        if pending_facet not in injected:
            return pending_facet

    # Step 3: default_facet from inventory
    topic_record = inventory.topics.get(entry.topic_key)
    if topic_record is not None:
        default_facet = topic_record.query_plan.default_facet
        if default_facet not in injected:
            return default_facet

    # All exhausted
    return None


def _make_injection_candidate(
    entry: TopicRegistryEntry,
    facet: str,
    candidate_type: str,
    confidence: str | None,
    inventory: CompiledInventory,
) -> InjectionCandidate:
    """Build an InjectionCandidate from entry + resolution data."""
    topic_record = inventory.topics.get(entry.topic_key)
    query_plan = topic_record.query_plan if topic_record is not None else None

    # Fallback if topic not in inventory (shouldn't happen in practice)
    if query_plan is None:
        from scripts.ccdi.types import QueryPlan

        query_plan = QueryPlan(default_facet="overview", facets={})

    return InjectionCandidate(
        topic_key=entry.topic_key,
        family_key=entry.family_key,
        facet=facet,
        confidence=confidence,
        coverage_target=entry.coverage_target,
        candidate_type=candidate_type,
        query_plan=query_plan,
    )


def process_semantic_hints(
    seed: RegistrySeed,
    hints: list[SemanticHint],
    inventory: CompiledInventory,
    classifier_fn: Callable[
        [str, CompiledInventory, CCDIConfig], ClassifierResult
    ],
    current_turn: int,
) -> list[InjectionCandidate]:
    """Process semantic hints and return injection candidates.

    In-memory function — mutates seed entries, returns candidates.
    The caller (dialogue-turn pipeline) handles persisting the seed.

    Hints are processed sequentially in array order per registry.md.
    Intra-turn mutations (e.g. contradicts_prior appending to pending_facets)
    are visible to subsequent hints in the same call.

    The classifier_fn is called with (claim_excerpt, inventory, config).
    A default CCDIConfig is used internally for the classify call.
    """
    from scripts.ccdi.config import BUILTIN_DEFAULTS

    # Build a config for classifier calls
    config = _build_default_config()

    candidates: list[InjectionCandidate] = []

    # Build entry lookup
    entry_by_key: dict[str, TopicRegistryEntry] = {}
    for entry in seed.entries:
        entry_by_key[entry.topic_key] = entry

    for hint in hints:
        # Classify the claim_excerpt
        result = classifier_fn(hint.claim_excerpt, inventory, config)

        if not result.resolved_topics:
            # No topic resolved — hint ignored
            continue

        # Use first resolved topic
        resolved = result.resolved_topics[0]
        topic_key = resolved.topic_key

        entry = entry_by_key.get(topic_key)
        if entry is None:
            # Topic not in registry — hint ignored
            continue

        resolved_facet = resolved.facet

        if hint.hint_type == "prescriptive":
            _apply_prescriptive(
                entry, resolved, inventory, current_turn, candidates
            )

        elif hint.hint_type == "contradicts_prior":
            _apply_contradicts_prior(
                entry, resolved, inventory, current_turn, candidates
            )

        elif hint.hint_type == "extends_topic":
            _apply_extends_topic(
                entry, resolved, inventory, current_turn, candidates
            )

    return candidates


def _apply_prescriptive(
    entry: TopicRegistryEntry,
    resolved: ResolvedTopic,
    inventory: CompiledInventory,
    current_turn: int,
    candidates: list[InjectionCandidate],
) -> None:
    """Apply prescriptive hint effects per registry.md scheduling table."""
    if entry.state == "detected":
        # Elevate to materially new
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "deferred":
        # Transition deferred → detected, then elevate
        _transition_deferred_to_detected(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "suppressed":
        # Re-enter as detected
        _reenter_suppressed(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "injected":
        # No effect — already covered
        pass


def _apply_contradicts_prior(
    entry: TopicRegistryEntry,
    resolved: ResolvedTopic,
    inventory: CompiledInventory,
    current_turn: int,
    candidates: list[InjectionCandidate],
) -> None:
    """Apply contradicts_prior hint effects per registry.md scheduling table."""
    if entry.state == "injected":
        # Append resolved facet to pending_facets
        entry.coverage_pending_facets.append(resolved.facet)
    elif entry.state == "detected":
        # Elevate to materially new
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "deferred":
        # Transition deferred → detected, then elevate
        _transition_deferred_to_detected(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "suppressed":
        # Re-enter as detected
        _reenter_suppressed(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )


def _apply_extends_topic(
    entry: TopicRegistryEntry,
    resolved: ResolvedTopic,
    inventory: CompiledInventory,
    current_turn: int,
    candidates: list[InjectionCandidate],
) -> None:
    """Apply extends_topic hint effects per registry.md scheduling table."""
    if entry.state == "injected":
        # Emit facet_expansion candidate via cascade
        target_facet = _resolve_facet_expansion(
            entry, resolved.facet, inventory
        )
        if target_facet is not None:
            candidates.append(
                _make_injection_candidate(
                    entry, target_facet, "facet_expansion", None, inventory
                )
            )
        # else: all exhausted, discard silently
    elif entry.state == "detected":
        # Elevate to materially new
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "deferred":
        # Transition deferred → detected first, then follow detected path
        _transition_deferred_to_detected(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )
    elif entry.state == "suppressed":
        # Re-enter as detected
        _reenter_suppressed(entry, current_turn)
        candidates.append(
            _make_injection_candidate(
                entry, resolved.facet, "new", resolved.confidence, inventory
            )
        )


def _build_default_config() -> CCDIConfig:
    """Build a CCDIConfig from built-in defaults for classifier calls."""
    from scripts.ccdi.config import BUILTIN_DEFAULTS

    c = BUILTIN_DEFAULTS["classifier"]
    i = BUILTIN_DEFAULTS["injection"]
    p = BUILTIN_DEFAULTS["packets"]
    return CCDIConfig(
        classifier_confidence_high_min_weight=c["confidence_high_min_weight"],
        classifier_confidence_medium_min_score=c["confidence_medium_min_score"],
        classifier_confidence_medium_min_single_weight=c[
            "confidence_medium_min_single_weight"
        ],
        injection_initial_threshold_high_count=i[
            "initial_threshold_high_count"
        ],
        injection_initial_threshold_medium_same_family_count=i[
            "initial_threshold_medium_same_family_count"
        ],
        injection_mid_turn_consecutive_medium_turns=i[
            "mid_turn_consecutive_medium_turns"
        ],
        injection_cooldown_max_new_topics_per_turn=i[
            "cooldown_max_new_topics_per_turn"
        ],
        injection_deferred_ttl_turns=i["deferred_ttl_turns"],
        packets_initial_token_budget_min=p["initial_token_budget_min"],
        packets_initial_token_budget_max=p["initial_token_budget_max"],
        packets_initial_max_topics=p["initial_max_topics"],
        packets_initial_max_facts=p["initial_max_facts"],
        packets_mid_turn_token_budget_min=p["mid_turn_token_budget_min"],
        packets_mid_turn_token_budget_max=p["mid_turn_token_budget_max"],
        packets_mid_turn_max_topics=p["mid_turn_max_topics"],
        packets_mid_turn_max_facts=p["mid_turn_max_facts"],
        packets_quality_min_result_score=p["quality_min_result_score"],
        packets_quality_min_useful_facts=p["quality_min_useful_facts"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_entry(
    seed: RegistrySeed, topic_key: str
) -> TopicRegistryEntry | None:
    """Find entry by topic_key. Returns None if not found."""
    for entry in seed.entries:
        if entry.topic_key == topic_key:
            return entry
    return None


def _propagate_family_context(
    seed: RegistrySeed, injected_entry: TopicRegistryEntry
) -> None:
    """After injection, propagate family_context_available to same-family leaves.

    Condition: the family's overview has been injected (any family entry in
    this family_key has coverage_overview_injected=True).
    """
    family_key = injected_entry.family_key

    # Check if any entry in this family has overview_injected
    family_overview_injected = any(
        e.coverage_overview_injected
        for e in seed.entries
        if e.family_key == family_key
    )

    if not family_overview_injected:
        return

    # Propagate to all leaves in this family
    for entry in seed.entries:
        if entry.family_key == family_key and entry.kind == "leaf":
            entry.coverage_family_context_available = True
