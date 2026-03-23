"""CCDI session registry — Phase A subset.

Manages per-topic state transitions: load, inject, suppress, persist.
Atomic file writes via temp+rename. Fingerprint normalization for
deduplication.

Import pattern:
    from scripts.ccdi.registry import load_registry, mark_injected, write_suppressed
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile

from scripts.ccdi.types import DURABLE_STATES, RegistrySeed, TopicRegistryEntry

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
