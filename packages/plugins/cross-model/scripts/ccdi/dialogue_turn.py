"""CCDI dialogue-turn scheduling pipeline.

Core function: dialogue_turn() — runs the 10-step scheduling pipeline each
time the agent processes a turn. File-based: loads registry from disk,
performs all mutations in-memory, writes back atomically once.

Import pattern:
    from scripts.ccdi.dialogue_turn import dialogue_turn, DialogueTurnResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from scripts.ccdi.classifier import classify
from scripts.ccdi.config import CCDIConfig
from scripts.ccdi.hash_utils import classify_result_hash
from scripts.ccdi.registry import (
    _find_entry,
    _propagate_family_context,
    _write_registry,
    apply_ttl_transitions,
    check_suppression_reentry,
    load_registry,
    process_semantic_hints,
    sort_candidates,
    update_redetections,
)
from scripts.ccdi.types import (
    ClassifierResult,
    CompiledInventory,
    InjectionCandidate,
    QueryPlan,
    RegistrySeed,
    ResolvedTopic,
    SemanticHint,
    ShadowDeferIntent,
    TopicRegistryEntry,
)

logger = logging.getLogger(__name__)

# Confidence levels eligible for candidacy (low is excluded)
_ELIGIBLE_CONFIDENCES: frozenset[str] = frozenset({"high", "medium"})

# Confidence ordering for tiebreaker — lower number = higher priority.
# None (pending_facet / facet_expansion) sorts last.
_CONFIDENCE_ORDER: dict[str | None, int] = {"high": 0, "medium": 1, "low": 2}
_NULL_CONFIDENCE_ORDER: int = 99


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class DialogueTurnResult:
    """Return value from dialogue_turn() — carries candidates + trace metadata."""

    candidates: list[InjectionCandidate]
    classifier_result: ClassifierResult
    shadow_defer_intents: list[ShadowDeferIntent]


# ---------------------------------------------------------------------------
# Facet resolution helpers
# ---------------------------------------------------------------------------


def _facet_has_queries(topic_key: str, facet: str, inventory: CompiledInventory) -> bool:
    """Check if a facet has non-empty QuerySpec list in the inventory."""
    topic_record = inventory.topics.get(topic_key)
    if topic_record is None:
        return False
    specs = topic_record.query_plan.facets.get(facet)
    return specs is not None and len(specs) > 0


def _resolve_candidate_facet(
    topic_key: str,
    classified_facet: str,
    inventory: CompiledInventory,
) -> str | None:
    """Resolve the effective facet for a candidate.

    If the classified facet has a non-empty QuerySpec, use it.
    Otherwise fall back to the topic's default_facet.
    If default_facet also has empty/absent QuerySpec, return None (suppress).
    """
    if _facet_has_queries(topic_key, classified_facet, inventory):
        return classified_facet

    # Fallback to default_facet
    topic_record = inventory.topics.get(topic_key)
    if topic_record is None:
        return None

    default_facet = topic_record.query_plan.default_facet
    if default_facet != classified_facet and _facet_has_queries(topic_key, default_facet, inventory):
        return default_facet

    # Both empty/absent
    return None


def _make_candidate(
    entry: TopicRegistryEntry,
    facet: str,
    candidate_type: str,
    confidence: str | None,
    inventory: CompiledInventory,
) -> InjectionCandidate:
    """Build an InjectionCandidate from entry + resolution data."""
    topic_record = inventory.topics.get(entry.topic_key)
    query_plan = topic_record.query_plan if topic_record is not None else QueryPlan(
        default_facet="overview", facets={}
    )
    return InjectionCandidate(
        topic_key=entry.topic_key,
        family_key=entry.family_key,
        facet=facet,
        confidence=confidence,
        coverage_target=entry.coverage_target,
        candidate_type=candidate_type,
        query_plan=query_plan,
    )


# ---------------------------------------------------------------------------
# Candidate sorting
# ---------------------------------------------------------------------------


def _sort_final_candidates(candidates: list[InjectionCandidate]) -> list[InjectionCandidate]:
    """Sort candidates for emission: new first, then pending_facet, then facet_expansion.

    Within each type, sort by confidence (high > medium > null),
    then first_seen_turn ascending (not available here, so use topic_key).
    """
    type_order = {"new": 0, "pending_facet": 1, "facet_expansion": 2}
    return sorted(
        candidates,
        key=lambda c: (
            type_order.get(c.candidate_type, 9),
            _CONFIDENCE_ORDER.get(c.confidence, _NULL_CONFIDENCE_ORDER),
            c.topic_key,
        ),
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def dialogue_turn(
    registry_path: str,
    text: str,
    source: str,
    inventory: CompiledInventory,
    config: CCDIConfig,
    hints: list[SemanticHint] | None = None,
    shadow_mode: bool = False,
    current_turn: int = 1,
    docs_epoch: str | None = None,
) -> DialogueTurnResult:
    """Run the dialogue-turn scheduling pipeline.

    10-step pipeline:
    1. Classify text against inventory
    2-5. TTL lifecycle (load-time recovery, high-confidence bypass, decrement, transitions)
    6. Suppression re-entry scan
    7. Process semantic hints
    8. Diff new topics (absent -> detected)
    9. Materially new + facet resolution
    10. Consecutive-medium tracking
    + Cooldown enforcement
    + Candidate emission
    + Atomic write
    """
    # Load registry
    seed = load_registry(registry_path)

    # Update docs_epoch on the seed if provided
    if docs_epoch is not None:
        seed.docs_epoch = docs_epoch

    # -----------------------------------------------------------------------
    # Step 1: Classify
    # -----------------------------------------------------------------------
    classifier_result = classify(text, inventory, config)

    # Build lookup structures from classifier result
    classifier_topic_keys: set[str] = set()
    classifier_confidences: dict[str, str] = {}
    classifier_by_key: dict[str, ResolvedTopic] = {}
    for rt in classifier_result.resolved_topics:
        classifier_topic_keys.add(rt.topic_key)
        classifier_confidences[rt.topic_key] = rt.confidence
        classifier_by_key[rt.topic_key] = rt

    # -----------------------------------------------------------------------
    # Steps 2-5: TTL lifecycle (load-time recovery, bypass, decrement, transitions)
    # -----------------------------------------------------------------------
    transitioned_entries = apply_ttl_transitions(
        seed, classifier_topic_keys, classifier_confidences, config
    )

    # -----------------------------------------------------------------------
    # Step 6: Suppression re-entry scan
    # -----------------------------------------------------------------------
    current_docs_epoch = docs_epoch if docs_epoch is not None else seed.docs_epoch

    # weak_results re-entry on epoch change
    reentry_entries = check_suppression_reentry(seed.entries, current_docs_epoch)
    for entry in reentry_entries:
        entry.state = "detected"
        entry.suppression_reason = None
        entry.suppressed_docs_epoch = None
        entry.last_seen_turn = current_turn

    # Redundant re-entry via new leaf: check if any NEW leaf is being detected
    # in a family that has suppressed:redundant entries
    _reenter_redundant_via_new_leaves(seed, classifier_topic_keys, inventory, current_turn)

    # -----------------------------------------------------------------------
    # Step 7: Process semantic hints
    # -----------------------------------------------------------------------
    hint_candidates: list[InjectionCandidate] = []
    if hints:
        hint_candidates = process_semantic_hints(
            seed, hints, inventory, classify, current_turn
        )

    # -----------------------------------------------------------------------
    # Step 10: Consecutive-medium tracking on EXISTING entries
    # (Must run before step 8 to avoid double-counting on newly created entries,
    # which already have the correct initial consecutive_medium_count.)
    # -----------------------------------------------------------------------
    update_redetections(seed, classifier_result.resolved_topics, current_turn)

    # -----------------------------------------------------------------------
    # Step 8: Diff new topics (absent -> detected)
    # -----------------------------------------------------------------------
    newly_created_keys: set[str] = set()
    existing_keys = {e.topic_key for e in seed.entries}
    for rt in classifier_result.resolved_topics:
        if rt.topic_key not in existing_keys:
            # Create new entry
            topic_record = inventory.topics.get(rt.topic_key)
            kind = topic_record.kind if topic_record else "leaf"
            new_entry = TopicRegistryEntry.new_detected(
                topic_key=rt.topic_key,
                family_key=rt.family_key,
                kind=kind,
                confidence=rt.confidence,
                facet=rt.facet,
                turn=current_turn,
            )
            seed.entries.append(new_entry)
            newly_created_keys.add(rt.topic_key)

    # -----------------------------------------------------------------------
    # Step 9: Materially new + facet resolution — identify candidates
    # -----------------------------------------------------------------------
    new_candidates: list[InjectionCandidate] = []

    for rt in classifier_result.resolved_topics:
        entry = _find_entry(seed, rt.topic_key)
        if entry is None:
            continue

        # Skip low confidence
        if rt.confidence not in _ELIGIBLE_CONFIDENCES:
            continue

        # Skip already injected (no re-injection as "new")
        if entry.state == "injected":
            continue

        # Skip suppressed (unless re-entered above)
        if entry.state == "suppressed":
            continue

        # Skip deferred (unless transitioned above)
        if entry.state == "deferred":
            continue

        # Materially new: newly created OR transitioned from deferred
        is_new = (
            rt.topic_key in newly_created_keys
            or entry in transitioned_entries
        )

        if rt.confidence == "high":
            # High confidence: must be materially new to be a candidate.
            # Re-detections of already-detected high topics are not new candidates.
            if not is_new:
                continue
        elif rt.confidence == "medium":
            # Medium confidence: always subject to consecutive-medium gate.
            # A single medium (even on first detection) is not a candidate.
            # Once threshold is reached (by re-detection across turns), it qualifies.
            if entry.kind == "leaf":
                if entry.consecutive_medium_count < config.injection_mid_turn_consecutive_medium_turns:
                    continue
            elif entry.kind == "family":
                # Family-kind medium never becomes a candidate via consecutive count
                continue

        # Facet resolution
        effective_facet = _resolve_candidate_facet(
            rt.topic_key, rt.facet, inventory
        )

        if effective_facet is None:
            # Both classified facet and default_facet are empty -> suppress
            entry.state = "suppressed"
            entry.suppression_reason = "weak_results"
            entry.suppressed_docs_epoch = current_docs_epoch
            continue

        new_candidates.append(
            _make_candidate(entry, effective_facet, "new", rt.confidence, inventory)
        )

    # -----------------------------------------------------------------------
    # Collect pending_facet candidates
    # -----------------------------------------------------------------------
    pending_facet_candidates: list[InjectionCandidate] = []
    for entry in seed.entries:
        if entry.state == "injected" and entry.coverage_pending_facets:
            for pf in entry.coverage_pending_facets:
                # Resolve facet
                effective_facet = _resolve_candidate_facet(
                    entry.topic_key, pf, inventory
                )
                if effective_facet is not None:
                    pending_facet_candidates.append(
                        _make_candidate(
                            entry, effective_facet, "pending_facet", None, inventory
                        )
                    )
                    break  # Only emit one pending_facet per entry per turn

    # -----------------------------------------------------------------------
    # Cooldown enforcement (only applies to "new" candidates)
    # -----------------------------------------------------------------------
    shadow_defer_intents: list[ShadowDeferIntent] = []

    # Sort new candidates for scheduling priority
    new_candidates_sorted = _sort_new_candidates(new_candidates, seed)

    max_new = config.injection_cooldown_max_new_topics_per_turn
    emitted_new: list[InjectionCandidate] = []
    deferred_new: list[InjectionCandidate] = []

    for candidate in new_candidates_sorted:
        if len(emitted_new) < max_new:
            emitted_new.append(candidate)
        else:
            deferred_new.append(candidate)

    # Apply deferral for cooldown-exceeded candidates
    for candidate in deferred_new:
        entry = _find_entry(seed, candidate.topic_key)
        if entry is None:
            continue

        if shadow_mode:
            # Shadow mode: emit ShadowDeferIntent, do NOT write deferred state
            # Build classify_result_hash from the classifier result
            rt = classifier_by_key.get(candidate.topic_key)
            if rt is not None:
                crh = classify_result_hash(
                    topic_key=rt.topic_key,
                    confidence=rt.confidence,
                    facet=rt.facet,
                    matched_aliases=[
                        {"text": ma.text, "weight": ma.weight}
                        for ma in rt.matched_aliases
                    ],
                )
            else:
                crh = ""
            shadow_defer_intents.append(
                ShadowDeferIntent(
                    turn=current_turn,
                    topic_key=candidate.topic_key,
                    reason="cooldown",
                    classify_result_hash=crh,
                )
            )
        else:
            # Normal mode: write deferred:cooldown
            entry.state = "deferred"
            entry.deferred_reason = "cooldown"
            entry.deferred_ttl = config.injection_deferred_ttl_turns

    # -----------------------------------------------------------------------
    # Candidate emission: new, pending_facet, facet_expansion in priority order
    # -----------------------------------------------------------------------
    all_candidates: list[InjectionCandidate] = []
    all_candidates.extend(emitted_new)
    all_candidates.extend(pending_facet_candidates)
    all_candidates.extend(hint_candidates)

    # Sort final candidates
    all_candidates = _sort_final_candidates(all_candidates)

    # -----------------------------------------------------------------------
    # Propagate family context for any entries with overview injected
    # -----------------------------------------------------------------------
    for entry in seed.entries:
        if entry.coverage_overview_injected:
            _propagate_family_context(seed, entry)

    # -----------------------------------------------------------------------
    # Atomic write
    # -----------------------------------------------------------------------
    _write_registry(registry_path, seed)

    return DialogueTurnResult(
        candidates=all_candidates,
        classifier_result=classifier_result,
        shadow_defer_intents=shadow_defer_intents,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sort_new_candidates(
    candidates: list[InjectionCandidate],
    seed: RegistrySeed,
) -> list[InjectionCandidate]:
    """Sort new candidates for scheduling priority.

    Order: confidence descending (high > medium), first_seen_turn ascending,
    topic_key lexicographic ascending.
    """
    # Build a lookup for first_seen_turn from the seed
    first_seen: dict[str, int] = {}
    for entry in seed.entries:
        first_seen[entry.topic_key] = entry.first_seen_turn

    return sorted(
        candidates,
        key=lambda c: (
            _CONFIDENCE_ORDER.get(c.confidence, _NULL_CONFIDENCE_ORDER),
            first_seen.get(c.topic_key, 0),
            c.topic_key,
        ),
    )


def _reenter_redundant_via_new_leaves(
    seed: RegistrySeed,
    classifier_topic_keys: set[str],
    inventory: CompiledInventory,
    current_turn: int,
) -> None:
    """Re-enter suppressed:redundant entries when a new leaf is detected in the same family.

    A "new leaf" is a topic_key present in the classifier output but absent
    from the registry. When such a leaf belongs to a family that has
    suppressed:redundant entries, those entries re-enter as detected.
    """
    existing_keys = {e.topic_key for e in seed.entries}
    new_leaf_families: set[str] = set()

    for topic_key in classifier_topic_keys:
        if topic_key not in existing_keys:
            topic_record = inventory.topics.get(topic_key)
            if topic_record is not None and topic_record.kind == "leaf":
                new_leaf_families.add(topic_record.family_key)

    if not new_leaf_families:
        return

    for entry in seed.entries:
        if (
            entry.state == "suppressed"
            and entry.suppression_reason == "redundant"
            and entry.family_key in new_leaf_families
        ):
            entry.state = "detected"
            entry.suppression_reason = None
            entry.suppressed_docs_epoch = None
            entry.last_seen_turn = current_turn
