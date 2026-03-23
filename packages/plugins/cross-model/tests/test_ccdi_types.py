"""Tests for CCDI foundation types."""

from __future__ import annotations

import json

import pytest

from scripts.ccdi.types import (
    DURABLE_STATES,
    TRANSPORT_ONLY_FIELDS,
    VALID_FACETS,
    Alias,
    AppliedRule,
    ClassifierResult,
    CompiledInventory,
    DenyRule,
    DocRef,
    FactItem,
    FactPacket,
    MatchedAlias,
    OverlayMeta,
    QueryPlan,
    QuerySpec,
    RegistrySeed,
    ResolvedTopic,
    SuppressedCandidate,
    TopicRecord,
    TopicRegistryEntry,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """VALID_FACETS, TRANSPORT_ONLY_FIELDS, DURABLE_STATES."""

    def test_valid_facets(self) -> None:
        assert VALID_FACETS == {"overview", "schema", "input", "output", "control", "config"}

    def test_transport_only_fields(self) -> None:
        assert TRANSPORT_ONLY_FIELDS == {"results_file", "inventory_snapshot_path"}

    def test_durable_states(self) -> None:
        assert DURABLE_STATES == {"detected", "injected", "suppressed", "deferred"}


# ---------------------------------------------------------------------------
# Alias
# ---------------------------------------------------------------------------


class TestAlias:
    """Alias construction and weight clamping."""

    def test_basic_construction(self) -> None:
        a = Alias(text="hooks", match_type="exact", weight=0.9)
        assert a.text == "hooks"
        assert a.match_type == "exact"
        assert a.weight == 0.9
        assert a.facet_hint is None
        assert a.source == "generated"

    def test_weight_clamped_above_one(self) -> None:
        a = Alias(text="x", match_type="exact", weight=1.5)
        assert a.weight == 1.0

    def test_weight_clamped_below_zero(self) -> None:
        a = Alias(text="x", match_type="exact", weight=-0.3)
        assert a.weight == 0.0

    def test_weight_at_boundaries(self) -> None:
        assert Alias(text="x", match_type="exact", weight=0.0).weight == 0.0
        assert Alias(text="x", match_type="exact", weight=1.0).weight == 1.0

    def test_facet_hint_and_source(self) -> None:
        a = Alias(
            text="pre_tool_use",
            match_type="phrase",
            weight=0.7,
            facet_hint="schema",
            source="overlay",
        )
        assert a.facet_hint == "schema"
        assert a.source == "overlay"


# ---------------------------------------------------------------------------
# DenyRule — discriminated union
# ---------------------------------------------------------------------------


class TestDenyRule:
    """DenyRule discriminated union constraints."""

    def test_drop_rule_penalty_is_null(self) -> None:
        r = DenyRule(
            id="d1", pattern="foo", match_type="token", action="drop", penalty=None, reason="test"
        )
        assert r.action == "drop"
        assert r.penalty is None

    def test_downrank_rule_has_penalty(self) -> None:
        r = DenyRule(
            id="d2",
            pattern="bar",
            match_type="phrase",
            action="downrank",
            penalty=0.5,
            reason="test",
        )
        assert r.action == "downrank"
        assert r.penalty == 0.5

    def test_drop_with_penalty_raises(self) -> None:
        with pytest.raises(ValueError, match="drop.*penalty.*null"):
            DenyRule(
                id="d3", pattern="x", match_type="token", action="drop", penalty=0.5, reason="bad"
            )

    def test_downrank_without_penalty_raises(self) -> None:
        with pytest.raises(ValueError, match="downrank.*penalty.*non-null"):
            DenyRule(
                id="d4",
                pattern="x",
                match_type="regex",
                action="downrank",
                penalty=None,
                reason="bad",
            )

    def test_downrank_penalty_zero_raises(self) -> None:
        """Penalty must be in (0.0, 1.0] — zero is not valid."""
        with pytest.raises(ValueError, match="penalty"):
            DenyRule(
                id="d5",
                pattern="x",
                match_type="token",
                action="downrank",
                penalty=0.0,
                reason="bad",
            )

    def test_downrank_penalty_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="penalty"):
            DenyRule(
                id="d6",
                pattern="x",
                match_type="token",
                action="downrank",
                penalty=1.1,
                reason="bad",
            )

    def test_exact_match_type_not_allowed(self) -> None:
        """DenyRule match_type excludes 'exact'."""
        with pytest.raises(ValueError, match="match_type"):
            DenyRule(
                id="d7",
                pattern="x",
                match_type="exact",
                action="drop",
                penalty=None,
                reason="bad",
            )


# ---------------------------------------------------------------------------
# TopicRecord — minimum 1 alias
# ---------------------------------------------------------------------------


class TestTopicRecord:
    """TopicRecord requires at least one alias."""

    def _make_alias(self, text: str = "hooks") -> Alias:
        return Alias(text=text, match_type="exact", weight=0.9)

    def _make_query_plan(self) -> QueryPlan:
        return QueryPlan(
            default_facet="overview",
            facets={"overview": [QuerySpec(q="hooks", category=None, priority=1)]},
        )

    def test_valid_construction(self) -> None:
        tr = TopicRecord(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            canonical_label="Hooks",
            category_hint="hooks",
            parent_topic=None,
            aliases=[self._make_alias()],
            query_plan=self._make_query_plan(),
            canonical_refs=[],
        )
        assert tr.topic_key == "hooks"
        assert len(tr.aliases) == 1

    def test_empty_aliases_raises(self) -> None:
        with pytest.raises(ValueError, match="alias"):
            TopicRecord(
                topic_key="hooks",
                family_key="hooks",
                kind="family",
                canonical_label="Hooks",
                category_hint="hooks",
                parent_topic=None,
                aliases=[],
                query_plan=self._make_query_plan(),
                canonical_refs=[],
            )


# ---------------------------------------------------------------------------
# RegistrySeed serialization
# ---------------------------------------------------------------------------


class TestRegistrySeed:
    """RegistrySeed JSON round-trip and transport field handling."""

    def _make_entry(self) -> TopicRegistryEntry:
        return TopicRegistryEntry(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            state="detected",
            first_seen_turn=1,
            last_seen_turn=1,
            last_injected_turn=None,
            last_query_fingerprint=None,
            consecutive_medium_count=0,
            suppression_reason=None,
            suppressed_docs_epoch=None,
            deferred_reason=None,
            deferred_ttl=None,
            coverage_target="leaf",
            facet="overview",
            kind="leaf",
            coverage_overview_injected=False,
            coverage_facets_injected=[],
            coverage_pending_facets=[],
            coverage_family_context_available=False,
            coverage_injected_chunk_ids=[],
        )

    def test_to_json_nullable_fields_explicit_null(self) -> None:
        """Nullable fields MUST appear as explicit null in JSON."""
        seed = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )
        data = seed.to_json()
        assert data["docs_epoch"] is None

        entry = data["entries"][0]
        assert entry["last_injected_turn"] is None
        assert entry["last_query_fingerprint"] is None
        assert entry["suppression_reason"] is None
        assert entry["suppressed_docs_epoch"] is None
        assert entry["deferred_reason"] is None
        assert entry["deferred_ttl"] is None

    def test_to_json_non_nullable_always_present(self) -> None:
        """Non-nullable fields present even when empty/false."""
        seed = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )
        data = seed.to_json()
        entry = data["entries"][0]

        # Empty arrays serialized
        assert entry["coverage"]["facets_injected"] == []
        assert entry["coverage"]["pending_facets"] == []
        assert entry["coverage"]["injected_chunk_ids"] == []

        # False booleans serialized
        assert entry["coverage"]["overview_injected"] is False
        assert entry["coverage"]["family_context_available"] is False

    def test_to_json_excludes_transport_fields(self) -> None:
        """results_file and inventory_snapshot_path excluded from output."""
        seed = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch=None,
            inventory_snapshot_version="1",
            results_file="/tmp/results.json",
            inventory_snapshot_path="/tmp/snapshot.json",
        )
        data = seed.to_json()
        assert "results_file" not in data
        assert "inventory_snapshot_path" not in data

    def test_to_json_round_trip(self) -> None:
        """JSON serialization round-trips through json.dumps/loads."""
        seed = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch="2026-03-23",
            inventory_snapshot_version="1",
        )
        text = json.dumps(seed.to_json())
        parsed = json.loads(text)
        assert parsed["docs_epoch"] == "2026-03-23"
        assert len(parsed["entries"]) == 1

    def test_from_json_strips_transport_fields(self) -> None:
        """from_json silently strips transport-only fields."""
        seed_orig = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )
        data = seed_orig.to_json()
        # Inject transport fields as if loaded from external source
        data["results_file"] = "/tmp/r.json"
        data["inventory_snapshot_path"] = "/tmp/s.json"

        seed_loaded = RegistrySeed.from_json(data)
        assert seed_loaded.results_file is None
        assert seed_loaded.inventory_snapshot_path is None

    def test_from_json_warns_on_transport_fields(self, caplog: pytest.LogCaptureFixture) -> None:
        """from_json emits warning when transport fields present."""
        seed_orig = RegistrySeed(
            entries=[self._make_entry()],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )
        data = seed_orig.to_json()
        data["results_file"] = "/tmp/r.json"

        import logging

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.types"):
            seed_loaded = RegistrySeed.from_json(data)

        assert seed_loaded.results_file is None
        assert any("results_file" in msg for msg in caplog.messages)

    def test_pending_facets_fifo_order_preserved(self) -> None:
        """pending_facets maintains FIFO order through serialization."""
        entry = TopicRegistryEntry(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            state="detected",
            first_seen_turn=1,
            last_seen_turn=1,
            last_injected_turn=None,
            last_query_fingerprint=None,
            consecutive_medium_count=0,
            suppression_reason=None,
            suppressed_docs_epoch=None,
            deferred_reason=None,
            deferred_ttl=None,
            coverage_target="leaf",
            facet="overview",
            kind="leaf",
            coverage_overview_injected=False,
            coverage_facets_injected=[],
            coverage_pending_facets=["schema", "input", "output"],
            coverage_family_context_available=False,
            coverage_injected_chunk_ids=[],
        )
        seed = RegistrySeed(
            entries=[entry],
            docs_epoch=None,
            inventory_snapshot_version="1",
        )
        data = seed.to_json()
        assert data["entries"][0]["coverage"]["pending_facets"] == [
            "schema",
            "input",
            "output",
        ]


# ---------------------------------------------------------------------------
# TopicRegistryEntry — schema-evolution defaults
# ---------------------------------------------------------------------------


class TestTopicRegistryEntryFromDict:
    """TopicRegistryEntry.from_dict() applies all 19 schema-evolution defaults."""

    MINIMAL_DICT: dict = {
        "topic_key": "hooks.pre_tool_use",
    }

    def test_state_defaults_to_detected(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.state == "detected"

    def test_last_seen_turn_defaults_to_zero(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.last_seen_turn == 0

    def test_first_seen_turn_defaults_to_zero(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.first_seen_turn == 0

    def test_last_injected_turn_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.last_injected_turn is None

    def test_last_query_fingerprint_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.last_query_fingerprint is None

    def test_consecutive_medium_count_defaults_to_zero(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.consecutive_medium_count == 0

    def test_deferred_reason_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.deferred_reason is None

    def test_deferred_ttl_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.deferred_ttl is None

    def test_suppressed_docs_epoch_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.suppressed_docs_epoch is None

    def test_suppression_reason_defaults_to_null(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.suppression_reason is None

    def test_facets_injected_defaults_to_empty(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_facets_injected == []

    def test_injected_chunk_ids_defaults_to_empty(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_injected_chunk_ids == []

    def test_pending_facets_defaults_to_empty(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_pending_facets == []

    def test_overview_injected_defaults_to_false(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_overview_injected is False

    def test_family_context_available_defaults_to_false(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_family_context_available is False

    def test_family_key_derived_from_topic_key(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.family_key == "hooks"

    def test_family_key_for_root_topic(self) -> None:
        """Root topic (no dot) uses topic_key as family_key."""
        e = TopicRegistryEntry.from_dict({"topic_key": "hooks"})
        assert e.family_key == "hooks"

    def test_kind_defaults_to_leaf(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.kind == "leaf"

    def test_coverage_target_derived_from_kind_family(self) -> None:
        e = TopicRegistryEntry.from_dict({**self.MINIMAL_DICT, "kind": "family"})
        assert e.coverage_target == "family"

    def test_coverage_target_derived_from_kind_leaf(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.coverage_target == "leaf"

    def test_facet_defaults_to_overview(self) -> None:
        e = TopicRegistryEntry.from_dict(self.MINIMAL_DICT)
        assert e.facet == "overview"

    def test_explicit_values_override_defaults(self) -> None:
        """Explicitly provided values are not overwritten."""
        d = {
            "topic_key": "hooks.pre_tool_use",
            "family_key": "custom_family",
            "state": "injected",
            "first_seen_turn": 5,
            "last_seen_turn": 10,
            "kind": "leaf",
            "coverage_target": "family",
            "facet": "schema",
        }
        e = TopicRegistryEntry.from_dict(d)
        assert e.family_key == "custom_family"
        assert e.state == "injected"
        assert e.first_seen_turn == 5
        assert e.last_seen_turn == 10
        assert e.coverage_target == "family"
        assert e.facet == "schema"

    def test_coverage_nested_dict(self) -> None:
        """from_dict handles coverage as nested dict (JSON shape)."""
        d = {
            "topic_key": "hooks.pre_tool_use",
            "coverage": {
                "overview_injected": True,
                "facets_injected": ["schema"],
                "pending_facets": ["input", "output"],
                "family_context_available": True,
                "injected_chunk_ids": ["c1", "c2"],
            },
        }
        e = TopicRegistryEntry.from_dict(d)
        assert e.coverage_overview_injected is True
        assert e.coverage_facets_injected == ["schema"]
        assert e.coverage_pending_facets == ["input", "output"]
        assert e.coverage_family_context_available is True
        assert e.coverage_injected_chunk_ids == ["c1", "c2"]


# ---------------------------------------------------------------------------
# TopicRegistryEntry.new_detected() factory
# ---------------------------------------------------------------------------


class TestTopicRegistryEntryNewDetected:
    """new_detected() factory method."""

    def test_creates_detected_entry(self) -> None:
        e = TopicRegistryEntry.new_detected(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            kind="leaf",
            confidence="high",
            facet="overview",
            turn=3,
        )
        assert e.state == "detected"
        assert e.first_seen_turn == 3
        assert e.last_seen_turn == 3

    def test_consecutive_medium_leaf(self) -> None:
        """Medium confidence + leaf → consecutive_medium_count = 1."""
        e = TopicRegistryEntry.new_detected(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            kind="leaf",
            confidence="medium",
            facet="overview",
            turn=3,
        )
        assert e.consecutive_medium_count == 1

    def test_consecutive_medium_family(self) -> None:
        """Medium confidence + family → consecutive_medium_count = 0."""
        e = TopicRegistryEntry.new_detected(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            confidence="medium",
            facet="overview",
            turn=3,
        )
        assert e.consecutive_medium_count == 0

    def test_consecutive_high(self) -> None:
        """High confidence → consecutive_medium_count = 0."""
        e = TopicRegistryEntry.new_detected(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            kind="leaf",
            confidence="high",
            facet="overview",
            turn=3,
        )
        assert e.consecutive_medium_count == 0

    def test_coverage_target_from_kind(self) -> None:
        e = TopicRegistryEntry.new_detected(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            confidence="high",
            facet="overview",
            turn=1,
        )
        assert e.coverage_target == "family"


# ---------------------------------------------------------------------------
# Ancillary types — basic construction
# ---------------------------------------------------------------------------


class TestAncillaryTypes:
    """DocRef, QuerySpec, QueryPlan, AppliedRule, OverlayMeta, etc."""

    def test_docref(self) -> None:
        r = DocRef(chunk_id="c1", category="hooks", source_file="hooks.md")
        assert r.chunk_id == "c1"

    def test_queryspec(self) -> None:
        q = QuerySpec(q="hooks", category=None, priority=1)
        assert q.q == "hooks"
        assert q.category is None

    def test_queryplan(self) -> None:
        qp = QueryPlan(
            default_facet="overview",
            facets={"overview": [QuerySpec(q="hooks", category=None, priority=1)]},
        )
        assert qp.default_facet == "overview"
        assert len(qp.facets["overview"]) == 1

    def test_applied_rule(self) -> None:
        ar = AppliedRule(rule_id="r1", operation="add_topic", target="hooks")
        assert ar.operation == "add_topic"

    def test_overlay_meta(self) -> None:
        om = OverlayMeta(
            overlay_version="1.0",
            overlay_schema_version="1",
            applied_rules=[AppliedRule(rule_id="r1", operation="add_topic", target="hooks")],
        )
        assert len(om.applied_rules) == 1

    def test_matched_alias(self) -> None:
        ma = MatchedAlias(text="hooks", span=(0, 5), weight=0.9)
        assert ma.span == (0, 5)

    def test_resolved_topic(self) -> None:
        rt = ResolvedTopic(
            topic_key="hooks",
            family_key="hooks",
            coverage_target="family",
            confidence="high",
            facet="overview",
            matched_aliases=[MatchedAlias(text="hooks", span=(0, 5), weight=0.9)],
            reason="matched",
        )
        assert rt.confidence == "high"

    def test_suppressed_candidate(self) -> None:
        sc = SuppressedCandidate(topic_key="hooks", reason="low score")
        assert sc.topic_key == "hooks"

    def test_classifier_result(self) -> None:
        cr = ClassifierResult(resolved_topics=[], suppressed_candidates=[])
        assert cr.resolved_topics == []

    def test_compiled_inventory(self) -> None:
        ci = CompiledInventory(
            schema_version="1",
            built_at="2026-03-23T00:00:00Z",
            docs_epoch=None,
            topics={},
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        assert ci.docs_epoch is None
        assert ci.topics == {}

    def test_fact_item(self) -> None:
        fi = FactItem(mode="paraphrase", facet="overview", text="Hooks are ...", refs=[])
        assert fi.mode == "paraphrase"

    def test_fact_packet(self) -> None:
        fp = FactPacket(
            packet_kind="initial",
            topics=["hooks"],
            facet="overview",
            facts=[],
            token_estimate=100,
        )
        assert fp.packet_kind == "initial"
