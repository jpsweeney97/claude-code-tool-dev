"""CCDI foundation data model types.

All types used across the CCDI system: inventory, classifier, registry,
packets, and config. Defined as frozen dataclasses for immutability.

Import pattern:
    from scripts.ccdi.types import Alias, TopicRecord, RegistrySeed, ...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_FACETS: set[str] = {"overview", "schema", "input", "output", "control", "config"}

TRANSPORT_ONLY_FIELDS: set[str] = {"results_file", "inventory_snapshot_path"}

DURABLE_STATES: set[str] = {"detected", "injected", "suppressed", "deferred"}

# ---------------------------------------------------------------------------
# Inventory types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Alias:
    """A term that refers to a topic, with match semantics and weight."""

    text: str
    match_type: str  # "exact" | "phrase" | "token" | "regex"
    weight: float
    facet_hint: str | None = None
    source: str = "generated"  # "generated" | "overlay"

    def __post_init__(self) -> None:
        # Clamp weight to [0.0, 1.0]
        if self.weight < 0.0:
            object.__setattr__(self, "weight", 0.0)
        elif self.weight > 1.0:
            object.__setattr__(self, "weight", 1.0)


@dataclass(frozen=True)
class DenyRule:
    """Deny/downrank rule — discriminated union on action.

    Constraints:
    - match_type: "token" | "phrase" | "regex" (NOT "exact")
    - action="drop" → penalty MUST be None
    - action="downrank" → penalty MUST be in (0.0, 1.0]
    """

    id: str
    pattern: str
    match_type: str  # "token" | "phrase" | "regex"
    action: str  # "drop" | "downrank"
    penalty: float | None
    reason: str

    def __post_init__(self) -> None:
        if self.match_type not in ("token", "phrase", "regex"):
            msg = f"DenyRule match_type must be 'token', 'phrase', or 'regex', got {self.match_type!r}"
            raise ValueError(msg)

        if self.action == "drop" and self.penalty is not None:
            msg = "DenyRule: drop action requires penalty to be null"
            raise ValueError(msg)

        if self.action == "downrank":
            if self.penalty is None:
                msg = "DenyRule: downrank action requires penalty to be non-null in (0.0, 1.0]"
                raise ValueError(msg)
            if not (0.0 < self.penalty <= 1.0):
                msg = f"DenyRule: downrank penalty must be in (0.0, 1.0], got {self.penalty}"
                raise ValueError(msg)


@dataclass(frozen=True)
class DocRef:
    """Reference to a specific documentation chunk."""

    chunk_id: str
    category: str
    source_file: str


@dataclass(frozen=True)
class QuerySpec:
    """A single search query within a query plan."""

    q: str
    category: str | None
    priority: int


@dataclass(frozen=True)
class QueryPlan:
    """Pre-computed search queries per facet."""

    default_facet: str
    facets: dict[str, list[QuerySpec]]


@dataclass(frozen=True)
class TopicRecord:
    """A topic in the compiled inventory. Requires at least one alias."""

    topic_key: str
    family_key: str
    kind: str  # "family" | "leaf"
    canonical_label: str
    category_hint: str
    parent_topic: str | None
    aliases: list[Alias]
    query_plan: QueryPlan
    canonical_refs: list[DocRef]

    def __post_init__(self) -> None:
        if not self.aliases:
            msg = "TopicRecord requires at least one alias"
            raise ValueError(msg)


@dataclass(frozen=True)
class AppliedRule:
    """Record of an overlay rule that was applied."""

    rule_id: str
    operation: str
    target: str


@dataclass(frozen=True)
class OverlayMeta:
    """Metadata about overlay rules applied to inventory."""

    overlay_version: str
    overlay_schema_version: str
    applied_rules: list[AppliedRule]


@dataclass(frozen=True)
class CompiledInventory:
    """Full compiled topic inventory."""

    schema_version: str
    built_at: str
    docs_epoch: str | None
    topics: dict[str, TopicRecord]
    denylist: list[DenyRule]
    overlay_meta: OverlayMeta | None
    merge_semantics_version: str


# ---------------------------------------------------------------------------
# Classifier types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchedAlias:
    """An alias match found by the classifier."""

    text: str
    span: tuple[int, int]
    weight: float


@dataclass(frozen=True)
class ResolvedTopic:
    """A topic resolved by the classifier with confidence."""

    topic_key: str
    family_key: str
    coverage_target: str  # "family" | "leaf"
    confidence: str  # "high" | "medium" | "low"
    facet: str
    matched_aliases: list[MatchedAlias]
    reason: str


@dataclass(frozen=True)
class SuppressedCandidate:
    """A candidate topic that was suppressed by the classifier."""

    topic_key: str
    reason: str


@dataclass(frozen=True)
class ClassifierResult:
    """Full classifier output."""

    resolved_topics: list[ResolvedTopic]
    suppressed_candidates: list[SuppressedCandidate]


# ---------------------------------------------------------------------------
# Registry types
# ---------------------------------------------------------------------------


@dataclass
class TopicRegistryEntry:
    """Per-topic state in the session registry.

    Mutable — state transitions happen during the session.
    """

    topic_key: str
    family_key: str
    state: str  # "detected" | "injected" | "suppressed" | "deferred"
    first_seen_turn: int
    last_seen_turn: int
    last_injected_turn: int | None
    last_query_fingerprint: str | None
    consecutive_medium_count: int
    suppression_reason: str | None  # "weak_results" | "redundant" | None
    suppressed_docs_epoch: str | None
    deferred_reason: str | None  # "cooldown" | "scout_priority" | "target_mismatch" | None
    deferred_ttl: int | None
    coverage_target: str  # "family" | "leaf"
    facet: str
    kind: str  # "family" | "leaf"
    # Coverage sub-fields (flattened to avoid nested mutable dataclass)
    coverage_overview_injected: bool
    coverage_facets_injected: list[str]
    coverage_pending_facets: list[str]
    coverage_family_context_available: bool
    coverage_injected_chunk_ids: list[str]

    def to_dict(self) -> dict:
        """Serialize to dict with nested coverage structure."""
        return {
            "topic_key": self.topic_key,
            "family_key": self.family_key,
            "state": self.state,
            "first_seen_turn": self.first_seen_turn,
            "last_seen_turn": self.last_seen_turn,
            "last_injected_turn": self.last_injected_turn,
            "last_query_fingerprint": self.last_query_fingerprint,
            "consecutive_medium_count": self.consecutive_medium_count,
            "suppression_reason": self.suppression_reason,
            "suppressed_docs_epoch": self.suppressed_docs_epoch,
            "deferred_reason": self.deferred_reason,
            "deferred_ttl": self.deferred_ttl,
            "coverage_target": self.coverage_target,
            "facet": self.facet,
            "kind": self.kind,
            "coverage": {
                "overview_injected": self.coverage_overview_injected,
                "facets_injected": list(self.coverage_facets_injected),
                "pending_facets": list(self.coverage_pending_facets),
                "family_context_available": self.coverage_family_context_available,
                "injected_chunk_ids": list(self.coverage_injected_chunk_ids),
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> TopicRegistryEntry:
        """Construct from dict, applying all 19 schema-evolution defaults.

        Handles both flat (coverage_* prefixed) and nested (coverage.*)
        field layouts for the coverage sub-object.
        """
        topic_key: str = d["topic_key"]

        # Derived defaults
        if "family_key" not in d:
            # Family prefix: everything before the first dot, or the key itself
            family_key = topic_key.split(".")[0]
        else:
            family_key = d["family_key"]

        kind = d.get("kind", "leaf")

        if "coverage_target" not in d:
            coverage_target = "family" if kind == "family" else "leaf"
        else:
            coverage_target = d["coverage_target"]

        # Coverage fields — check nested dict first, then flat prefix
        cov = d.get("coverage", {})

        return cls(
            topic_key=topic_key,
            family_key=family_key,
            state=d.get("state", "detected"),
            first_seen_turn=d.get("first_seen_turn", 0),
            last_seen_turn=d.get("last_seen_turn", 0),
            last_injected_turn=d.get("last_injected_turn"),
            last_query_fingerprint=d.get("last_query_fingerprint"),
            consecutive_medium_count=d.get("consecutive_medium_count", 0),
            suppression_reason=d.get("suppression_reason"),
            suppressed_docs_epoch=d.get("suppressed_docs_epoch"),
            deferred_reason=d.get("deferred_reason"),
            deferred_ttl=d.get("deferred_ttl"),
            coverage_target=coverage_target,
            facet=d.get("facet", "overview"),
            kind=kind,
            coverage_overview_injected=cov.get(
                "overview_injected",
                d.get("coverage_overview_injected", False),
            ),
            coverage_facets_injected=cov.get(
                "facets_injected",
                d.get("coverage_facets_injected", []),
            ),
            coverage_pending_facets=cov.get(
                "pending_facets",
                d.get("coverage_pending_facets", []),
            ),
            coverage_family_context_available=cov.get(
                "family_context_available",
                d.get("coverage_family_context_available", False),
            ),
            coverage_injected_chunk_ids=cov.get(
                "injected_chunk_ids",
                d.get("coverage_injected_chunk_ids", []),
            ),
        )

    @classmethod
    def new_detected(
        cls,
        *,
        topic_key: str,
        family_key: str,
        kind: str,
        confidence: str,
        facet: str,
        turn: int,
    ) -> TopicRegistryEntry:
        """Factory for a newly detected topic.

        consecutive_medium_count is 1 if confidence is "medium" AND kind is
        "leaf", else 0.
        """
        cmc = 1 if (confidence == "medium" and kind == "leaf") else 0
        return cls(
            topic_key=topic_key,
            family_key=family_key,
            state="detected",
            first_seen_turn=turn,
            last_seen_turn=turn,
            last_injected_turn=None,
            last_query_fingerprint=None,
            consecutive_medium_count=cmc,
            suppression_reason=None,
            suppressed_docs_epoch=None,
            deferred_reason=None,
            deferred_ttl=None,
            coverage_target="family" if kind == "family" else "leaf",
            facet=facet,
            kind=kind,
            coverage_overview_injected=False,
            coverage_facets_injected=[],
            coverage_pending_facets=[],
            coverage_family_context_available=False,
            coverage_injected_chunk_ids=[],
        )


@dataclass
class RegistrySeed:
    """Serializable registry snapshot for persistence.

    Transport-only fields (results_file, inventory_snapshot_path) are
    accepted at construction but excluded from to_json() output and
    stripped when loaded via from_json().
    """

    entries: list[TopicRegistryEntry]
    docs_epoch: str | None
    inventory_snapshot_version: str
    results_file: str | None = None
    inventory_snapshot_path: str | None = None

    def to_json(self) -> dict:
        """Serialize to JSON-compatible dict.

        - All nullable fields serialized as explicit null
        - Non-nullable fields always present (empty arrays, false)
        - Transport-only fields excluded
        """
        return {
            "entries": [e.to_dict() for e in self.entries],
            "docs_epoch": self.docs_epoch,
            "inventory_snapshot_version": self.inventory_snapshot_version,
        }

    @classmethod
    def from_json(cls, data: dict) -> RegistrySeed:
        """Load from JSON dict, stripping transport-only fields.

        Warns if transport fields are present in the input.
        """
        for field_name in TRANSPORT_ONLY_FIELDS:
            if field_name in data:
                logger.warning(
                    "RegistrySeed: stripping transport-only field %r from loaded data",
                    field_name,
                )

        entries = [TopicRegistryEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            docs_epoch=data.get("docs_epoch"),
            inventory_snapshot_version=data.get("inventory_snapshot_version", "1"),
            results_file=None,
            inventory_snapshot_path=None,
        )


# ---------------------------------------------------------------------------
# Packet types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactItem:
    """A single fact within a packet."""

    mode: str  # "paraphrase" | "snippet"
    facet: str
    text: str
    refs: list[DocRef]


@dataclass(frozen=True)
class FactPacket:
    """Documentation packet delivered to the session."""

    packet_kind: str  # "initial" | "mid_turn"
    topics: list[str]
    facet: str
    facts: list[FactItem]
    token_estimate: int
