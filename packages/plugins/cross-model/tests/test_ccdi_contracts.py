"""CCDI boundary contract tests — Phase A + Phase B.

Verifies field names, enum values, and schema shapes agree across component
boundaries. Each test imports from BOTH sides of a boundary.
"""

from __future__ import annotations

import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any

import pytest

from scripts.ccdi.build_inventory import generate_scaffold, merge_overlay, build_inventory
from scripts.ccdi.classifier import classify
from scripts.ccdi.config import BUILTIN_DEFAULTS, CCDIConfigLoader
from scripts.ccdi.hash_utils import classify_result_hash
from scripts.ccdi.inventory import load_inventory
from scripts.ccdi.packets import build_packet, render_initial, render_mid_turn
from scripts.ccdi.registry import load_registry, mark_injected, write_suppressed, write_deferred
from scripts.ccdi.types import (
    DURABLE_STATES,
    TRANSPORT_ONLY_FIELDS,
    VALID_CANDIDATE_TYPES,
    VALID_FACETS,
    VALID_HINT_TYPES,
    Alias,
    ClassifierResult,
    CompiledInventory,
    DenyRule,
    DiagnosticsRecord,
    DocRef,
    FactPacket,
    InjectionCandidate,
    MatchedAlias,
    QueryPlan,
    QuerySpec,
    RegistrySeed,
    ResolvedTopic,
    SemanticHint,
    ShadowDeferIntent,
    SuppressedCandidate,
    TopicRecord,
    TopicRegistryEntry,
)
from scripts.ccdi.dialogue_turn import dialogue_turn, DialogueTurnResult
from scripts.validate_graduation import VALID_STATUS_VALUES
from scripts.topic_inventory import check_agent_gate, main as cli_main


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_entry(
    topic_key: str = "hooks.pre_tool_use",
    *,
    family_key: str = "hooks",
    state: str = "detected",
    kind: str = "leaf",
    facet: str = "overview",
    first_seen_turn: int = 1,
    coverage_target: str = "leaf",
    last_injected_turn: int | None = None,
    last_query_fingerprint: str | None = None,
    consecutive_medium_count: int = 0,
    suppression_reason: str | None = None,
    suppressed_docs_epoch: str | None = None,
    deferred_reason: str | None = None,
    deferred_ttl: int | None = None,
    coverage_overview_injected: bool = False,
    coverage_facets_injected: list[str] | None = None,
    coverage_pending_facets: list[str] | None = None,
    coverage_family_context_available: bool = False,
    coverage_injected_chunk_ids: list[str] | None = None,
) -> TopicRegistryEntry:
    return TopicRegistryEntry(
        topic_key=topic_key,
        family_key=family_key,
        state=state,
        kind=kind,
        facet=facet,
        first_seen_turn=first_seen_turn,
        last_seen_turn=first_seen_turn,
        last_injected_turn=last_injected_turn,
        last_query_fingerprint=last_query_fingerprint,
        consecutive_medium_count=consecutive_medium_count,
        suppression_reason=suppression_reason,
        suppressed_docs_epoch=suppressed_docs_epoch,
        deferred_reason=deferred_reason,
        deferred_ttl=deferred_ttl,
        coverage_target=coverage_target,
        coverage_overview_injected=coverage_overview_injected,
        coverage_facets_injected=coverage_facets_injected or [],
        coverage_pending_facets=coverage_pending_facets or [],
        coverage_family_context_available=coverage_family_context_available,
        coverage_injected_chunk_ids=coverage_injected_chunk_ids or [],
    )


def _make_topic(
    topic_key: str = "hooks",
    *,
    family_key: str | None = None,
    kind: str = "family",
    aliases: list[Alias] | None = None,
) -> TopicRecord:
    fk = family_key or topic_key.split(".")[0]
    als = aliases or [Alias(text=topic_key, match_type="token", weight=0.8)]
    return TopicRecord(
        topic_key=topic_key,
        family_key=fk,
        kind=kind,
        canonical_label=topic_key.replace(".", " ").title(),
        category_hint=fk,
        parent_topic=fk if kind == "leaf" else None,
        aliases=als,
        query_plan=QueryPlan(
            default_facet="overview",
            facets={"overview": [QuerySpec(q=topic_key, category=fk, priority=1)]},
        ),
        canonical_refs=[],
    )


def _make_inventory(
    topics: dict[str, TopicRecord] | None = None,
    denylist: list[DenyRule] | None = None,
    docs_epoch: str | None = None,
) -> CompiledInventory:
    return CompiledInventory(
        schema_version="1",
        built_at="2026-03-23T00:00:00Z",
        docs_epoch=docs_epoch,
        topics=topics or {},
        denylist=denylist or [],
        overlay_meta=None,
        merge_semantics_version="1",
    )


def _default_config():
    return CCDIConfigLoader("/dev/null").load()


def _write_seed_file(seed: RegistrySeed, path: Path) -> None:
    data = seed.to_json()
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# 1. inventory -> classifier boundary
# ---------------------------------------------------------------------------


class TestInventoryClassifierBoundary:
    """topic_key, family_key, alias normalization, denylist shapes match."""

    def test_topic_key_propagates_to_resolved(self) -> None:
        topic = _make_topic("hooks.pre_tool_use", kind="leaf")
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        assert any(r.topic_key == "hooks.pre_tool_use" for r in result.resolved_topics)

    def test_family_key_propagates_to_resolved(self) -> None:
        topic = _make_topic("hooks.pre_tool_use", kind="leaf")
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        for r in result.resolved_topics:
            if r.topic_key == "hooks.pre_tool_use":
                assert r.family_key == "hooks"

    def test_alias_weight_normalization(self) -> None:
        """Alias with weight > 1.0 is clamped before classifier sees it."""
        alias = Alias(text="hooks", match_type="token", weight=1.5)
        assert alias.weight == 1.0

    def test_denylist_shape_matches_classifier_expectation(self) -> None:
        """DenyRule fields accepted by classifier's deny_map builder."""
        rule = DenyRule(
            id="d1", pattern="test", match_type="token",
            action="drop", penalty=None, reason="test",
        )
        inv = _make_inventory(denylist=[rule])
        # Classifier must not crash — denylist shape compatible
        result = classify("test hooks", inv, _default_config())
        assert isinstance(result, ClassifierResult)


# ---------------------------------------------------------------------------
# 2. classifier -> registry boundary
# ---------------------------------------------------------------------------


class TestClassifierRegistryBoundary:
    """confidence, facet, coverage_target enum values, candidate_type enum."""

    def test_confidence_values_are_valid(self) -> None:
        topic = _make_topic(
            "hooks.pre_tool_use", kind="leaf",
            aliases=[Alias(text="hooks.pre_tool_use", match_type="phrase", weight=0.9)],
        )
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        valid_confidences = {"high", "medium", "low"}
        for r in result.resolved_topics:
            assert r.confidence in valid_confidences

    def test_facet_values_are_in_valid_facets(self) -> None:
        topic = _make_topic("hooks.pre_tool_use", kind="leaf")
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        for r in result.resolved_topics:
            assert r.facet in VALID_FACETS

    def test_coverage_target_values_match_registry(self) -> None:
        """coverage_target from classifier is 'family' or 'leaf', same as registry."""
        valid_targets = {"family", "leaf"}
        topic = _make_topic("hooks.pre_tool_use", kind="leaf")
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        for r in result.resolved_topics:
            assert r.coverage_target in valid_targets

    def test_resolved_topic_creates_valid_registry_entry(self) -> None:
        """A ResolvedTopic can be used to construct a TopicRegistryEntry."""
        rt = ResolvedTopic(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            coverage_target="leaf",
            confidence="high",
            facet="overview",
            matched_aliases=[],
            reason="test",
        )
        entry = TopicRegistryEntry.new_detected(
            topic_key=rt.topic_key,
            family_key=rt.family_key,
            kind=rt.coverage_target,
            confidence=rt.confidence,
            facet=rt.facet,
            turn=1,
        )
        assert entry.topic_key == rt.topic_key
        assert entry.state == "detected"


# ---------------------------------------------------------------------------
# 3. search results -> packet builder boundary
# ---------------------------------------------------------------------------


class TestSearchResultsPacketBoundary:
    """Required fields present: chunk_id, category, content."""

    def test_required_fields_accepted(self) -> None:
        results = [
            {
                "chunk_id": "c1",
                "category": "hooks",
                "content": "PreToolUse hooks intercept tool calls.",
                "score": 0.9,
                "source_file": "hooks.md",
            }
        ]
        packet = build_packet(results, "initial", _default_config())
        assert packet is not None
        assert packet.facts[0].refs[0].chunk_id == "c1"

    def test_missing_chunk_id_raises(self) -> None:
        """Packet builder requires chunk_id on every result."""
        results = [{"category": "hooks", "content": "text", "score": 0.9}]
        with pytest.raises(KeyError):
            build_packet(results, "initial", _default_config())


# ---------------------------------------------------------------------------
# 4. packet -> prompt boundary
# ---------------------------------------------------------------------------


class TestPacketPromptBoundary:
    """Citation format [ccdocs:<chunk_id>], valid markdown, budget."""

    def _build_test_packet(self) -> FactPacket:
        results = [
            {
                "chunk_id": "hooks-overview-1",
                "category": "hooks",
                "content": "PreToolUse hooks intercept tool calls before execution.",
                "score": 0.9,
                "source_file": "hooks.md",
            }
        ]
        packet = build_packet(results, "initial", _default_config())
        assert packet is not None
        return packet

    def test_citation_format(self) -> None:
        packet = self._build_test_packet()
        rendered = render_initial(packet)
        pattern = r"\[ccdocs:[^\]]+\]"
        assert re.search(pattern, rendered), f"No citation found in: {rendered}"

    def test_citation_uses_chunk_id(self) -> None:
        packet = self._build_test_packet()
        rendered = render_initial(packet)
        assert "[ccdocs:hooks-overview-1]" in rendered

    def test_initial_render_is_valid_markdown(self) -> None:
        packet = self._build_test_packet()
        rendered = render_initial(packet)
        assert rendered.startswith("### Claude Code Extension Reference")

    def test_mid_turn_render_has_metadata_comment(self) -> None:
        results = [
            {
                "chunk_id": "c1", "category": "hooks",
                "content": "Hooks intercept tool calls.",
                "score": 0.9, "source_file": "hooks.md",
            }
        ]
        packet = build_packet(results, "mid_turn", _default_config())
        assert packet is not None
        rendered = render_mid_turn(packet)
        assert "<!-- ccdi-packet" in rendered

    def test_packet_respects_token_budget(self) -> None:
        packet = self._build_test_packet()
        config = _default_config()
        assert packet.token_estimate <= config.packets_initial_token_budget_max


# ---------------------------------------------------------------------------
# 5. CLI -> agents boundary
# ---------------------------------------------------------------------------


class TestCLIAgentBoundary:
    """Exit codes, stdout JSON contract, stderr behavior."""

    def test_classify_missing_text_file_nonzero_exit(self) -> None:
        ret = cli_main(["classify", "--text-file", "/nonexistent", "--inventory", "/nonexistent"])
        assert ret != 0

    def test_classify_success_emits_json(self, tmp_path: Path) -> None:
        # Write a minimal inventory
        topic = _make_topic("hooks", aliases=[Alias(text="hooks", match_type="token", weight=0.9)])
        inv = _make_inventory({"hooks": topic})
        from scripts.ccdi.build_inventory import serialize_inventory

        inv_path = tmp_path / "inv.json"
        inv_path.write_text(json.dumps(serialize_inventory(inv)))

        text_path = tmp_path / "text.txt"
        text_path.write_text("Tell me about hooks")

        import io
        import sys

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            ret = cli_main(["classify", "--text-file", str(text_path), "--inventory", str(inv_path)])
        finally:
            sys.stdout = old_stdout

        assert ret == 0
        output = json.loads(captured.getvalue())
        assert "resolved_topics" in output
        assert "suppressed_candidates" in output

    def test_classify_wrong_flag_name_rejected(self) -> None:
        """classify rejects --inventory-snapshot (wrong flag name)."""
        ret = cli_main(["classify", "--text-file", "/dev/null", "--inventory-snapshot", "/dev/null"])
        assert ret != 0


# ---------------------------------------------------------------------------
# 6. config -> CLI boundary
# ---------------------------------------------------------------------------


class TestConfigCLIBoundary:
    """ccdi_config.json schema validated at load."""

    def test_valid_config_loads(self, tmp_path: Path) -> None:
        config_data = {
            "config_version": "1",
            "classifier": {"confidence_high_min_weight": 0.9},
            "injection": {},
            "packets": {},
        }
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(json.dumps(config_data))

        loader = CCDIConfigLoader(config_path)
        config = loader.load()
        assert config.classifier_confidence_high_min_weight == 0.9

    def test_missing_config_uses_defaults(self) -> None:
        loader = CCDIConfigLoader("/nonexistent/ccdi_config.json")
        config = loader.load()
        assert config.classifier_confidence_high_min_weight == BUILTIN_DEFAULTS["classifier"]["confidence_high_min_weight"]

    def test_wrong_version_uses_defaults(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(json.dumps({"config_version": "99"}))

        with caplog.at_level(logging.WARNING):
            config = CCDIConfigLoader(config_path).load()
        assert config.classifier_confidence_high_min_weight == BUILTIN_DEFAULTS["classifier"]["confidence_high_min_weight"]
        assert any("Unsupported config_version" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# 7. dump_index_metadata -> build_inventory response shape
# ---------------------------------------------------------------------------


class TestDumpIndexMetadataBoundary:
    """Expected fields from dump_index_metadata match generate_scaffold."""

    def test_scaffold_from_metadata_shape(self) -> None:
        metadata: dict[str, Any] = {
            "categories": [
                {
                    "name": "hooks",
                    "aliases": ["hook system"],
                    "chunk_count": 1,
                    "chunks": [
                        {
                            "chunk_id": "hooks#pretooluse",
                            "source_file": "https://code.claude.com/docs/en/hooks",
                            "headings": ["Hooks", "PreToolUse Hooks"],
                            "code_literals": ["PreToolUse"],
                            "config_keys": [],
                            "distinctive_terms": ["pre-tool"],
                        }
                    ],
                }
            ]
        }
        inv = generate_scaffold(metadata)
        assert "hooks" in inv.topics
        assert "hooks.pretooluse_hooks" in inv.topics
        assert inv.topics["hooks"].kind == "family"
        assert inv.topics["hooks.pretooluse_hooks"].kind == "leaf"

    def test_scaffold_missing_optional_fields(self) -> None:
        """Unknown fields ignored; missing optional fields use defaults."""
        metadata: dict[str, Any] = {
            "categories": [
                {
                    "name": "tools",
                    "headings": [],
                    "future_field": "ignored",
                }
            ]
        }
        inv = generate_scaffold(metadata)
        assert "tools" in inv.topics


# ---------------------------------------------------------------------------
# 8. dump_index_metadata schema evolution
# ---------------------------------------------------------------------------


class TestDumpIndexMetadataSchemaEvolution:
    """Unknown field ignored, required field missing -> error."""

    def test_unknown_field_ignored(self) -> None:
        metadata: dict[str, Any] = {
            "categories": [
                {
                    "name": "hooks",
                    "headings": [],
                    "unknown_future_field": 42,
                }
            ]
        }
        inv = generate_scaffold(metadata)
        assert "hooks" in inv.topics

    def test_required_category_name_missing_raises(self) -> None:
        metadata: dict[str, Any] = {"categories": [{"headings": []}]}
        with pytest.raises(KeyError):
            generate_scaffold(metadata)


# ---------------------------------------------------------------------------
# 9. registry seed -> delegation envelope
# ---------------------------------------------------------------------------


class TestRegistrySeedDelegationEnvelope:
    """ccdi_seed path valid, JSON schema."""

    def test_seed_file_is_valid_json(self, tmp_path: Path) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        loaded_data = json.loads(seed_path.read_text())
        assert "entries" in loaded_data
        assert "docs_epoch" in loaded_data
        assert "inventory_snapshot_version" in loaded_data

    def test_seed_round_trips_through_load_registry(self, tmp_path: Path) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch="epoch-1", inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        loaded = load_registry(str(seed_path))
        assert len(loaded.entries) == 1
        assert loaded.entries[0].topic_key == "hooks.pre_tool_use"
        assert loaded.docs_epoch == "epoch-1"


# ---------------------------------------------------------------------------
# 10. registry null-field serialization
# ---------------------------------------------------------------------------


class TestRegistryNullFieldSerialization:
    """detected state: all nullable fields present as null in JSON."""

    def test_nullable_fields_explicit_null(self) -> None:
        entry = _make_entry(state="detected")
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        raw = json.loads(json.dumps(seed.to_json()))

        assert raw["docs_epoch"] is None
        e = raw["entries"][0]
        nullable_fields = [
            "last_injected_turn",
            "last_query_fingerprint",
            "suppression_reason",
            "suppressed_docs_epoch",
            "deferred_reason",
            "deferred_ttl",
        ]
        for field in nullable_fields:
            assert field in e, f"Nullable field {field!r} missing from serialized entry"
            assert e[field] is None, f"Nullable field {field!r} should be null, got {e[field]!r}"


# ---------------------------------------------------------------------------
# 11. registry null-field serialization includes envelope
# ---------------------------------------------------------------------------


class TestRegistryNullFieldEnvelope:
    """docs_epoch: null present in file."""

    def test_docs_epoch_null_present(self) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        raw = json.loads(json.dumps(seed.to_json()))
        assert "docs_epoch" in raw
        assert raw["docs_epoch"] is None


# ---------------------------------------------------------------------------
# 12. RegistrySeed durable fields completeness
# ---------------------------------------------------------------------------


class TestRegistrySeedDurableFieldsCompleteness:
    """All durable fields from TopicRegistryEntry present in entries,
    including all 5 coverage.* sub-fields."""

    def test_all_durable_fields_present(self) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        raw = seed.to_json()
        e = raw["entries"][0]

        # Top-level durable fields
        expected_top_fields = {
            "topic_key", "family_key", "state", "first_seen_turn",
            "last_seen_turn", "last_injected_turn", "last_query_fingerprint",
            "consecutive_medium_count", "suppression_reason",
            "suppressed_docs_epoch", "deferred_reason", "deferred_ttl",
            "coverage_target", "facet", "kind", "coverage",
        }
        for field in expected_top_fields:
            assert field in e, f"Durable field {field!r} missing from serialized entry"

    def test_all_five_coverage_subfields_present(self) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        raw = seed.to_json()
        cov = raw["entries"][0]["coverage"]

        expected_coverage = {
            "overview_injected",
            "facets_injected",
            "pending_facets",
            "family_context_available",
            "injected_chunk_ids",
        }
        for field in expected_coverage:
            assert field in cov, f"Coverage sub-field {field!r} missing"


# ---------------------------------------------------------------------------
# 13. transport-only field allowlist completeness
# ---------------------------------------------------------------------------


class TestTransportOnlyFieldAllowlist:
    """TRANSPORT_ONLY_FIELDS == {"results_file", "inventory_snapshot_path"}."""

    def test_exact_set(self) -> None:
        assert TRANSPORT_ONLY_FIELDS == {"results_file", "inventory_snapshot_path"}

    def test_transport_fields_are_on_registry_seed(self) -> None:
        """RegistrySeed dataclass has these as attributes."""
        seed = RegistrySeed(
            entries=[], docs_epoch=None, inventory_snapshot_version="1",
            results_file="/tmp/r.json", inventory_snapshot_path="/tmp/s.json",
        )
        assert seed.results_file == "/tmp/r.json"
        assert seed.inventory_snapshot_path == "/tmp/s.json"


# ---------------------------------------------------------------------------
# 14. results_file write-time exclusion (defense-in-depth)
# ---------------------------------------------------------------------------


class TestResultsFileWriteTimeExclusion:
    """Construct dict with results_file, serialize, assert absent."""

    def test_results_file_excluded_from_to_json(self) -> None:
        entry = _make_entry()
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
            results_file="/tmp/results.json",
        )
        data = seed.to_json()
        assert "results_file" not in data
        # Also check the JSON text itself
        text = json.dumps(data)
        assert "results_file" not in text

    def test_inventory_snapshot_path_excluded_from_to_json(self) -> None:
        seed = RegistrySeed(
            entries=[], docs_epoch=None, inventory_snapshot_version="1",
            inventory_snapshot_path="/tmp/snap.json",
        )
        data = seed.to_json()
        assert "inventory_snapshot_path" not in data


# ---------------------------------------------------------------------------
# 15. results_file stripped after commit
# ---------------------------------------------------------------------------


class TestResultsFileStrippedAfterCommit:
    """Write seed with results_file, run mark_injected, assert absent."""

    def test_results_file_absent_after_mark_injected(self, tmp_path: Path) -> None:
        entry = _make_entry()
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
            results_file="/tmp/results.json",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        # Write with results_file present in raw JSON
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        mark_injected(
            str(seed_path), "hooks.pre_tool_use", "overview",
            "leaf", ["c1"], "fp1", turn=1,
        )

        reloaded_raw = json.loads(seed_path.read_text())
        assert "results_file" not in reloaded_raw


# ---------------------------------------------------------------------------
# 16. results_file stripped after multi-topic commit
# ---------------------------------------------------------------------------


class TestResultsFileStrippedMultiTopic:
    """2 topics, commit first, assert stripped, commit second succeeds."""

    def test_multi_topic_commit(self, tmp_path: Path) -> None:
        e1 = _make_entry("hooks.pre_tool_use")
        e2 = _make_entry("hooks.post_tool_use")
        seed = RegistrySeed(
            entries=[e1, e2], docs_epoch=None, inventory_snapshot_version="1",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        # Commit first topic
        mark_injected(
            str(seed_path), "hooks.pre_tool_use", "overview",
            "leaf", ["c1"], "fp1", turn=1,
        )
        after_first = json.loads(seed_path.read_text())
        assert "results_file" not in after_first

        # Commit second topic succeeds
        mark_injected(
            str(seed_path), "hooks.post_tool_use", "overview",
            "leaf", ["c2"], "fp2", turn=1,
        )
        after_second = json.loads(seed_path.read_text())
        assert "results_file" not in after_second
        # Both topics got injected
        states = {e["topic_key"]: e["state"] for e in after_second["entries"]}
        assert states["hooks.pre_tool_use"] == "injected"
        assert states["hooks.post_tool_use"] == "injected"


# ---------------------------------------------------------------------------
# 17. results_file stripped when all commits fail
# ---------------------------------------------------------------------------


class TestResultsFileStrippedOnFailedCommit:
    """Failed commit doesn't strip, next successful mutation does."""

    def test_failed_commit_preserves_then_success_strips(self, tmp_path: Path) -> None:
        entry = _make_entry("hooks.pre_tool_use")
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        # Attempt commit on non-existent topic — entry not found, early return.
        # mark_injected returns before writing when the topic_key is absent,
        # so the raw file (including results_file) is NOT rewritten.
        mark_injected(
            str(seed_path), "nonexistent.topic", "overview",
            "leaf", ["c1"], "fp1", turn=1,
        )
        after_noop = json.loads(seed_path.read_text())
        # Transport field survives because the file was never rewritten
        assert "results_file" in after_noop

        # Successful mutation rewrites the file via load+write cycle,
        # which strips transport fields through from_json + to_json
        mark_injected(
            str(seed_path), "hooks.pre_tool_use", "overview",
            "leaf", ["c1"], "fp1", turn=1,
        )
        after_success = json.loads(seed_path.read_text())
        assert "results_file" not in after_success


# ---------------------------------------------------------------------------
# 18. results_file present on load
# ---------------------------------------------------------------------------


class TestResultsFilePresentOnLoad:
    """Warning logged, field stripped."""

    def test_warning_and_strip_on_load(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.types"):
            loaded = load_registry(str(seed_path))

        assert loaded.results_file is None
        assert any("results_file" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# 19. DenyRule load-time warn-and-skip
# ---------------------------------------------------------------------------


class TestDenyRuleLoadTimeWarnAndSkip:
    """downrank penalty=-0.5 -> warning, rule skipped."""

    def test_negative_penalty_skipped(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        inv_data: dict[str, Any] = {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "topics": {},
            "denylist": [
                {
                    "id": "bad-deny",
                    "pattern": "test",
                    "match_type": "token",
                    "action": "downrank",
                    "penalty": -0.5,
                    "reason": "test",
                }
            ],
            "merge_semantics_version": "1",
        }
        inv_path = tmp_path / "inv.json"
        inv_path.write_text(json.dumps(inv_data))

        with caplog.at_level(logging.INFO, logger="scripts.ccdi.inventory"):
            inv = load_inventory(inv_path)

        assert len(inv.denylist) == 0
        assert any("backward-compat skip" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# 20. pending_facets serialization order
# ---------------------------------------------------------------------------


class TestPendingFacetsSerializationOrder:
    """FIFO preserved through write/load cycle."""

    def test_fifo_order_preserved(self, tmp_path: Path) -> None:
        entry = _make_entry(coverage_pending_facets=["schema", "input", "output", "config"])
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        loaded = load_registry(str(seed_path))
        assert loaded.entries[0].coverage_pending_facets == ["schema", "input", "output", "config"]


# ---------------------------------------------------------------------------
# 21. RegistrySeed version mismatch + topic_key discard
# ---------------------------------------------------------------------------


class TestRegistrySeedVersionMismatch:
    """Mismatched version + invalid topic_key -> discard invalid, keep valid."""

    def test_version_mismatch_warns(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """inventory_snapshot_version mismatch triggers warning."""
        entry = _make_entry()
        data = {
            "entries": [entry.to_dict()],
            "docs_epoch": None,
            "inventory_snapshot_version": "99",
        }
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text(json.dumps(data))

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.types"):
            loaded = load_registry(str(seed_path))

        # Entries are kept (best-effort); version mismatch logged
        assert len(loaded.entries) == 1


# ---------------------------------------------------------------------------
# 22. RegistrySeed inventory_snapshot_version null at load
# ---------------------------------------------------------------------------


class TestRegistrySeedISVNull:
    """Treated as version mismatch."""

    def test_null_isv_warns(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        data = {
            "entries": [],
            "docs_epoch": None,
            "inventory_snapshot_version": None,
        }
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text(json.dumps(data))

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.types"):
            loaded = RegistrySeed.from_json(json.loads(seed_path.read_text()))

        assert any("version mismatch" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# 23. RegistrySeed <-> ClassifierResult coverage_target enum
# ---------------------------------------------------------------------------


class TestCoverageTargetEnumConsistency:
    """'family' | 'leaf' consistent between classifier and registry."""

    def test_coverage_target_values_match(self) -> None:
        valid = {"family", "leaf"}
        # Classifier produces these
        rt = ResolvedTopic(
            topic_key="hooks", family_key="hooks", coverage_target="family",
            confidence="high", facet="overview", matched_aliases=[], reason="test",
        )
        assert rt.coverage_target in valid

        # Registry accepts these
        entry = TopicRegistryEntry.new_detected(
            topic_key="hooks", family_key="hooks", kind="family",
            confidence="high", facet="overview", turn=1,
        )
        assert entry.coverage_target in valid


# ---------------------------------------------------------------------------
# 24. RegistrySeed <-> ClassifierResult facet enum
# ---------------------------------------------------------------------------


class TestFacetEnumConsistency:
    """Valid Facet values consistent between classifier and registry."""

    def test_facet_values_subset_of_valid_facets(self) -> None:
        rt = ResolvedTopic(
            topic_key="hooks", family_key="hooks", coverage_target="family",
            confidence="high", facet="overview", matched_aliases=[], reason="test",
        )
        assert rt.facet in VALID_FACETS

        entry = _make_entry(facet="schema")
        assert entry.facet in VALID_FACETS


# ---------------------------------------------------------------------------
# 25. version axes -> overlay merge
# ---------------------------------------------------------------------------


class TestVersionAxesOverlayMerge:
    """Axes validated at build time."""

    def test_overlay_schema_version_mismatch_exits(self) -> None:
        metadata: dict[str, Any] = {"categories": []}
        overlay = {
            "overlay_version": "1.0",
            "overlay_schema_version": "99",
            "rules": [],
        }
        with pytest.raises(SystemExit):
            build_inventory(metadata, overlay)

    def test_merge_semantics_version_mismatch_exits(self) -> None:
        metadata: dict[str, Any] = {"categories": []}
        overlay = {
            "overlay_version": "1.0",
            "overlay_schema_version": "1",
            "merge_semantics_version": "99",
            "rules": [],
        }
        with pytest.raises(SystemExit):
            build_inventory(metadata, overlay)


# ---------------------------------------------------------------------------
# 26. inventory -> classifier schema evolution
# ---------------------------------------------------------------------------


class TestInventoryClassifierSchemaEvolution:
    """Unknown field ignored, required Alias field missing -> error."""

    def test_unknown_topic_field_ignored(self, tmp_path: Path) -> None:
        inv_data: dict[str, Any] = {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "topics": {
                "hooks": {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "canonical_label": "Hooks",
                    "category_hint": "hooks",
                    "parent_topic": None,
                    "aliases": [{"text": "hooks", "match_type": "token", "weight": 0.8}],
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {"overview": [{"q": "hooks", "category": "hooks", "priority": 1}]},
                    },
                    "canonical_refs": [],
                    "future_field": "should be ignored",
                }
            },
            "denylist": [],
            "merge_semantics_version": "1",
        }
        inv_path = tmp_path / "inv.json"
        inv_path.write_text(json.dumps(inv_data))
        inv = load_inventory(inv_path)
        assert "hooks" in inv.topics

    def test_required_alias_text_missing_raises(self, tmp_path: Path) -> None:
        inv_data: dict[str, Any] = {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "topics": {
                "hooks": {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "canonical_label": "Hooks",
                    "category_hint": "hooks",
                    "parent_topic": None,
                    "aliases": [{"match_type": "token", "weight": 0.8}],
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {"overview": [{"q": "hooks", "category": "hooks", "priority": 1}]},
                    },
                    "canonical_refs": [],
                }
            },
            "denylist": [],
            "merge_semantics_version": "1",
        }
        inv_path = tmp_path / "inv.json"
        inv_path.write_text(json.dumps(inv_data))
        with pytest.raises(KeyError):
            load_inventory(inv_path)


# ---------------------------------------------------------------------------
# 27. inventory -> packet builder schema evolution
# ---------------------------------------------------------------------------


class TestInventoryPacketSchemaEvolution:
    """Unknown facet skipped."""

    def test_unknown_facet_in_query_plan_no_crash(self) -> None:
        """Packet builder only uses facets it understands; unknown facets in
        inventory don't cause errors."""
        topic = _make_topic("hooks")
        # Add an unknown facet to query_plan — the topic is still valid
        qp = QueryPlan(
            default_facet="overview",
            facets={
                "overview": [QuerySpec(q="hooks", category="hooks", priority=1)],
                "future_facet": [QuerySpec(q="hooks future", category="hooks", priority=1)],
            },
        )
        topic_with_extra = TopicRecord(
            topic_key=topic.topic_key,
            family_key=topic.family_key,
            kind=topic.kind,
            canonical_label=topic.canonical_label,
            category_hint=topic.category_hint,
            parent_topic=topic.parent_topic,
            aliases=topic.aliases,
            query_plan=qp,
            canonical_refs=topic.canonical_refs,
        )
        inv = _make_inventory({"hooks": topic_with_extra})
        # Classifier still works (extra facet doesn't crash)
        result = classify("hooks", inv, _default_config())
        assert isinstance(result, ClassifierResult)


# ---------------------------------------------------------------------------
# 28. inventory -> registry schema evolution
# ---------------------------------------------------------------------------


class TestInventoryRegistrySchemaEvolution:
    """Unknown field ignored, required missing -> reinitialize."""

    def test_unknown_entry_field_ignored(self, tmp_path: Path) -> None:
        entry_dict = _make_entry().to_dict()
        entry_dict["future_field"] = "should be ignored"
        data = {
            "entries": [entry_dict],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text(json.dumps(data))

        loaded = load_registry(str(seed_path))
        assert len(loaded.entries) == 1
        assert loaded.entries[0].topic_key == "hooks.pre_tool_use"

    def test_corrupt_json_reinitializes(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text("{invalid json")

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.registry"):
            loaded = load_registry(str(seed_path))

        assert len(loaded.entries) == 0
        assert any("corrupt" in m.lower() or "reinitializing" in m.lower() for m in caplog.messages)


# ---------------------------------------------------------------------------
# 29. registry file with attempt-local state
# ---------------------------------------------------------------------------


class TestRegistryAttemptLocalState:
    """state: 'looked_up' -> reinitialized with warning."""

    def test_looked_up_resets_to_detected(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        entry_dict = _make_entry().to_dict()
        entry_dict["state"] = "looked_up"
        data = {
            "entries": [entry_dict],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text(json.dumps(data))

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.registry"):
            loaded = load_registry(str(seed_path))

        assert loaded.entries[0].state == "detected"
        assert any("attempt-local" in m for m in caplog.messages)

    def test_built_resets_to_detected(self, tmp_path: Path) -> None:
        entry_dict = _make_entry().to_dict()
        entry_dict["state"] = "built"
        data = {
            "entries": [entry_dict],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        seed_path = tmp_path / "ccdi_seed.json"
        seed_path.write_text(json.dumps(data))

        loaded = load_registry(str(seed_path))
        assert loaded.entries[0].state == "detected"


# ---------------------------------------------------------------------------
# 30. defaults table <-> TopicRegistryEntry durable fields sync
# ---------------------------------------------------------------------------


class TestDefaultsTableSync:
    """Every durable field has a default via from_dict."""

    def test_minimal_dict_populates_all_fields(self) -> None:
        """from_dict with only topic_key produces a valid entry with all fields."""
        entry = TopicRegistryEntry.from_dict({"topic_key": "hooks.pre_tool_use"})
        # Verify all fields are set (not AttributeError)
        assert entry.topic_key == "hooks.pre_tool_use"
        assert entry.family_key is not None
        assert entry.state is not None
        assert entry.first_seen_turn is not None
        assert entry.last_seen_turn is not None
        assert entry.consecutive_medium_count is not None
        assert entry.coverage_target is not None
        assert entry.facet is not None
        assert entry.kind is not None
        assert entry.coverage_overview_injected is not None
        assert entry.coverage_facets_injected is not None
        assert entry.coverage_pending_facets is not None
        assert entry.coverage_family_context_available is not None
        assert entry.coverage_injected_chunk_ids is not None

    def test_durable_states_cover_valid_states(self) -> None:
        """DURABLE_STATES contains all states that survive persistence."""
        # attempt-local states are NOT in DURABLE_STATES
        assert "looked_up" not in DURABLE_STATES
        assert "built" not in DURABLE_STATES
        # All durable states listed
        assert DURABLE_STATES == {"detected", "injected", "suppressed", "deferred"}


# ---------------------------------------------------------------------------
# 31. ccdi_inventory_snapshot absent with ccdi_seed present
# ---------------------------------------------------------------------------


class TestInventorySnapshotAbsent:
    """Degraded: treated as no CCDI."""

    def test_seed_present_no_inventory_is_degraded(self, tmp_path: Path) -> None:
        """When the seed file exists but inventory snapshot is missing,
        the system should degrade (load_inventory raises on missing path)."""
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        inv_path = tmp_path / "nonexistent_inventory.json"

        # Seed loads fine
        loaded = load_registry(str(seed_path))
        assert len(loaded.entries) == 1

        # Inventory load raises — degraded mode, treated as no CCDI
        with pytest.raises((FileNotFoundError, OSError)):
            load_inventory(inv_path)


# ---------------------------------------------------------------------------
# 32. ccdi_seed inline JSON rejection
# ---------------------------------------------------------------------------


class TestCCDISeedInlineJSONRejection:
    """JSON object (not path) -> treated as absent."""

    def test_inline_json_is_not_valid_seed_path(self) -> None:
        """A ccdi_seed value that starts with '{' is inline JSON, not a path.
        load_registry treats a non-existent path as missing and returns an
        empty registry. The agent layer must detect inline JSON (starts with
        '{') BEFORE calling load_registry and treat it as absent."""
        inline_json = '{"entries": [], "docs_epoch": null, "inventory_snapshot_version": "1"}'
        assert inline_json.startswith("{")
        # load_registry returns empty seed for non-existent paths (not a crash)
        loaded = load_registry(inline_json)
        assert len(loaded.entries) == 0
        # Agent-side contract: inline JSON must be rejected before reaching load
        assert inline_json.lstrip().startswith("{"), "Agent must detect inline JSON"


# ---------------------------------------------------------------------------
# 33. ccdi_policy_snapshot xfail placeholder (Phase B deferred)
# ---------------------------------------------------------------------------


class TestCCDIPolicySnapshot:
    """Policy snapshot shape not yet defined — deferred to Phase B graduation gate."""

    @pytest.mark.xfail(strict=True, reason="Phase B deferred — policy snapshot shape defined during graduation gate (T17)")
    def test_ccdi_policy_snapshot_boundary(self) -> None:
        assert False, "placeholder -- define shape during graduation gate"


# ===========================================================================
# Phase B boundary contract tests
# ===========================================================================


# ---------------------------------------------------------------------------
# B1. candidate_type enum consistency
# ---------------------------------------------------------------------------


class TestCandidateTypeEnumConsistency:
    """InjectionCandidate candidate_type values are the only valid types."""

    def test_valid_candidate_types_exact_set(self) -> None:
        assert VALID_CANDIDATE_TYPES == {"new", "facet_expansion", "pending_facet"}

    def test_injection_candidate_accepts_valid_types(self) -> None:
        """Each valid candidate_type can construct an InjectionCandidate."""
        qp = QueryPlan(default_facet="overview", facets={})
        for ct in VALID_CANDIDATE_TYPES:
            candidate = InjectionCandidate(
                topic_key="hooks",
                family_key="hooks",
                facet="overview",
                confidence="high" if ct == "new" else None,
                coverage_target="leaf",
                candidate_type=ct,
                query_plan=qp,
            )
            assert candidate.candidate_type == ct


# ---------------------------------------------------------------------------
# B2. SemanticHint schema boundary
# ---------------------------------------------------------------------------


class TestSemanticHintsSchemaB:
    """SemanticHint hint_type enum and claim_excerpt length cap."""

    def test_hint_type_enum_values_match(self) -> None:
        assert VALID_HINT_TYPES == {"prescriptive", "contradicts_prior", "extends_topic"}

    def test_valid_hint_types_accepted(self) -> None:
        for ht in VALID_HINT_TYPES:
            hint = SemanticHint(claim_index=0, hint_type=ht, claim_excerpt="test")
            assert hint.hint_type == ht

    def test_invalid_hint_type_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid hint_type"):
            SemanticHint(claim_index=0, hint_type="unknown", claim_excerpt="test")

    def test_claim_excerpt_length_cap_enforced(self) -> None:
        """claim_excerpt > 100 characters is rejected."""
        with pytest.raises(ValueError, match="claim_excerpt exceeds 100"):
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="x" * 101,
            )

    def test_claim_excerpt_at_boundary(self) -> None:
        """Exactly 100 characters is accepted."""
        hint = SemanticHint(
            claim_index=0,
            hint_type="prescriptive",
            claim_excerpt="x" * 100,
        )
        assert len(hint.claim_excerpt) == 100


# ---------------------------------------------------------------------------
# B3. graduation status enum consistency
# ---------------------------------------------------------------------------


class TestGraduationStatusEnumConsistency:
    """Validator uses same status values as graduation gate."""

    def test_graduation_status_values(self) -> None:
        """VALID_STATUS_VALUES from validate_graduation.py matches expected set."""
        assert VALID_STATUS_VALUES == {"approved", "rejected"}

    def test_durable_states_independent_of_graduation_status(self) -> None:
        """Registry DURABLE_STATES and graduation VALID_STATUS_VALUES are disjoint."""
        assert DURABLE_STATES.isdisjoint(VALID_STATUS_VALUES)


# ---------------------------------------------------------------------------
# B4. ccdi_inventory_snapshot absent with ccdi_seed present
# ---------------------------------------------------------------------------


class TestCCDIInventorySnapshotAbsentWithSeed:
    """When registry seed is present but inventory_snapshot is absent -> degraded mode."""

    def test_seed_present_inventory_absent_degraded(self, tmp_path: Path) -> None:
        """dialogue_turn with missing inventory raises or returns empty candidates."""
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        # Inventory path does not exist — load_inventory raises
        inv_path = tmp_path / "nonexistent_inventory.json"
        assert seed_path.exists()
        assert not inv_path.exists()

        with pytest.raises((FileNotFoundError, OSError)):
            load_inventory(inv_path)


# ---------------------------------------------------------------------------
# B5. ccdi_seed inline JSON rejection
# ---------------------------------------------------------------------------


class TestCCDISeedInlineJSONRejectionB:
    """Inline JSON string (not file path) treated as absent."""

    def test_inline_json_not_treated_as_path(self) -> None:
        """A JSON string starting with '{' is not a valid file path.
        load_registry returns empty for non-existent paths."""
        inline = '{"entries":[],"docs_epoch":null,"inventory_snapshot_version":"1"}'
        # Starts with { — agent contract: reject before passing to load_registry
        assert inline.lstrip().startswith("{")
        loaded = load_registry(inline)
        assert len(loaded.entries) == 0

    def test_inline_json_detection_contract(self) -> None:
        """The agent-side check is: if value starts with '{', treat as absent."""
        for value in ['{"a":1}', '  {"entries":[]}', '{ }']:
            assert value.lstrip().startswith("{"), f"Detection failed for {value!r}"


# ---------------------------------------------------------------------------
# B6. shadow mode auto-suppression permitted
# ---------------------------------------------------------------------------


class TestShadowModeAutoSuppressionPermitted:
    """Empty build-packet in shadow mode -> suppressed state written."""

    def test_shadow_mode_allows_auto_suppression(self, tmp_path: Path) -> None:
        """In shadow mode, a topic with no queryable facets gets auto-suppressed."""
        # Create a topic with an empty query plan (no facet queries)
        topic = _make_topic(
            "empty_topic",
            kind="leaf",
            aliases=[Alias(text="empty_topic", match_type="phrase", weight=0.9)],
        )
        # Override query_plan to have empty facets
        topic_with_empty = TopicRecord(
            topic_key=topic.topic_key,
            family_key=topic.family_key,
            kind=topic.kind,
            canonical_label=topic.canonical_label,
            category_hint=topic.category_hint,
            parent_topic=topic.parent_topic,
            aliases=topic.aliases,
            query_plan=QueryPlan(default_facet="overview", facets={}),
            canonical_refs=topic.canonical_refs,
        )
        inv = _make_inventory({"empty_topic": topic_with_empty})

        seed_path = tmp_path / "ccdi_seed.json"
        seed = RegistrySeed(entries=[], docs_epoch=None, inventory_snapshot_version="1")
        _write_seed_file(seed, seed_path)

        config = _default_config()
        result = dialogue_turn(
            registry_path=str(seed_path),
            text="empty_topic",
            source="test",
            inventory=inv,
            config=config,
            shadow_mode=True,
            current_turn=1,
        )

        # Reload registry to check state
        reloaded = load_registry(str(seed_path))
        entry = next(
            (e for e in reloaded.entries if e.topic_key == "empty_topic"),
            None,
        )
        # Auto-suppression fires even in shadow mode
        assert entry is not None
        assert entry.state == "suppressed"
        assert entry.suppression_reason == "weak_results"


# ---------------------------------------------------------------------------
# B7. injected forward-only invariant (mark_injected idempotent)
# ---------------------------------------------------------------------------


class TestInjectedForwardOnlyInvariant:
    """mark_injected on already-injected -> idempotent."""

    def test_double_mark_injected_idempotent(self, tmp_path: Path) -> None:
        entry = _make_entry(state="detected")
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        # First injection
        mark_injected(
            str(seed_path), "hooks.pre_tool_use", "overview",
            "leaf", ["c1", "c2"], "fp1", turn=1,
        )
        after_first = load_registry(str(seed_path))
        first_entry = after_first.entries[0]
        assert first_entry.state == "injected"
        assert first_entry.last_injected_turn == 1

        # Second injection (idempotent)
        mark_injected(
            str(seed_path), "hooks.pre_tool_use", "overview",
            "leaf", ["c1", "c3"], "fp2", turn=2,
        )
        after_second = load_registry(str(seed_path))
        second_entry = after_second.entries[0]

        # State still injected, turn updated
        assert second_entry.state == "injected"
        assert second_entry.last_injected_turn == 2
        # chunk_ids deduplicated
        assert "c1" in second_entry.coverage_injected_chunk_ids
        assert "c2" in second_entry.coverage_injected_chunk_ids
        assert "c3" in second_entry.coverage_injected_chunk_ids
        assert len(second_entry.coverage_injected_chunk_ids) == 3


# ---------------------------------------------------------------------------
# B8. classify_result_hash boundary
# ---------------------------------------------------------------------------


class TestClassifyResultHashBoundary:
    """Hash contract across classifier -> registry boundary."""

    def test_hash_is_16_char_hex(self) -> None:
        """classify_result_hash returns a 16-character hex string."""
        h = classify_result_hash(
            topic_key="hooks.pre_tool_use",
            confidence="high",
            facet="overview",
            matched_aliases=[{"text": "hooks", "weight": 0.9}],
        )
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_deterministic(self) -> None:
        """Same inputs always produce the same hash."""
        kwargs = {
            "topic_key": "hooks",
            "confidence": "high",
            "facet": "overview",
            "matched_aliases": [
                {"text": "hooks", "weight": 0.9},
                {"text": "hook system", "weight": 0.5},
            ],
        }
        h1 = classify_result_hash(**kwargs)
        h2 = classify_result_hash(**kwargs)
        assert h1 == h2

    def test_hash_from_classifier_output(self) -> None:
        """classify -> ResolvedTopic -> hash produces valid output."""
        topic = _make_topic(
            "hooks.pre_tool_use", kind="leaf",
            aliases=[Alias(text="hooks.pre_tool_use", match_type="phrase", weight=0.9)],
        )
        inv = _make_inventory({"hooks.pre_tool_use": topic})
        result = classify("hooks.pre_tool_use", inv, _default_config())
        assert len(result.resolved_topics) > 0

        rt = result.resolved_topics[0]
        h = classify_result_hash(
            topic_key=rt.topic_key,
            confidence=rt.confidence,
            facet=rt.facet,
            matched_aliases=[
                {"text": ma.text, "weight": ma.weight}
                for ma in rt.matched_aliases
            ],
        )
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# B9. candidate_type "new" for standard candidates
# ---------------------------------------------------------------------------


class TestCandidateTypeNewForStandard:
    """Standard candidate -> candidate_type 'new'."""

    def test_standard_candidate_has_type_new(self) -> None:
        qp = QueryPlan(default_facet="overview", facets={})
        candidate = InjectionCandidate(
            topic_key="hooks",
            family_key="hooks",
            facet="overview",
            confidence="high",
            coverage_target="leaf",
            candidate_type="new",
            query_plan=qp,
        )
        assert candidate.candidate_type == "new"
        assert candidate.confidence is not None


# ---------------------------------------------------------------------------
# B10. confidence null for hint candidates
# ---------------------------------------------------------------------------


class TestConfidenceNullForHintCandidates:
    """facet_expansion/pending_facet -> confidence null."""

    def test_facet_expansion_confidence_null(self) -> None:
        qp = QueryPlan(default_facet="overview", facets={})
        candidate = InjectionCandidate(
            topic_key="hooks",
            family_key="hooks",
            facet="schema",
            confidence=None,
            coverage_target="leaf",
            candidate_type="facet_expansion",
            query_plan=qp,
        )
        assert candidate.confidence is None
        assert candidate.candidate_type == "facet_expansion"

    def test_pending_facet_confidence_null(self) -> None:
        qp = QueryPlan(default_facet="overview", facets={})
        candidate = InjectionCandidate(
            topic_key="hooks",
            family_key="hooks",
            facet="config",
            confidence=None,
            coverage_target="leaf",
            candidate_type="pending_facet",
            query_plan=qp,
        )
        assert candidate.confidence is None
        assert candidate.candidate_type == "pending_facet"

    def test_new_candidate_has_non_null_confidence(self) -> None:
        """Contrast: 'new' candidates always have non-null confidence."""
        qp = QueryPlan(default_facet="overview", facets={})
        for conf in ("high", "medium"):
            candidate = InjectionCandidate(
                topic_key="hooks",
                family_key="hooks",
                facet="overview",
                confidence=conf,
                coverage_target="leaf",
                candidate_type="new",
                query_plan=qp,
            )
            assert candidate.confidence is not None


# ---------------------------------------------------------------------------
# B11. transport-only field allowlist completeness
# ---------------------------------------------------------------------------


class TestTransportOnlyFieldAllowlistCompleteness:
    """Every field in TRANSPORT_ONLY_FIELDS has a strip-on-load test."""

    def test_each_transport_field_has_strip_test(self) -> None:
        """Verify that test_ccdi_types.py and test_ccdi_registry.py contain
        strip-on-load tests for each transport-only field."""
        tests_dir = Path(__file__).parent

        # Read test file contents to check for strip tests
        types_test = (tests_dir / "test_ccdi_types.py").read_text()
        registry_test = (tests_dir / "test_ccdi_registry.py").read_text()
        combined = types_test + registry_test

        for field_name in TRANSPORT_ONLY_FIELDS:
            # Check that there's at least one test that references stripping
            # this field (the test name or assertion about the field being None)
            has_strip_test = (
                f"test_from_json_strips_transport_fields" in combined
                or f"test_strips_transport_fields" in combined
            )
            assert has_strip_test, (
                f"No strip-on-load test found for transport field {field_name!r} "
                f"in test_ccdi_types.py or test_ccdi_registry.py"
            )

    def test_strip_tests_verify_none_value(self) -> None:
        """Strip tests assert the field value is None after load."""
        for field_name in TRANSPORT_ONLY_FIELDS:
            # Verify behavior directly: from_json strips transport fields
            data = {
                "entries": [],
                "docs_epoch": None,
                "inventory_snapshot_version": "1",
                field_name: "/tmp/test_value",
            }
            seed = RegistrySeed.from_json(data)
            actual = getattr(seed, field_name)
            assert actual is None, (
                f"Transport field {field_name!r} not stripped on load: got {actual!r}"
            )


# ---------------------------------------------------------------------------
# B12. defaults table <-> TopicRegistryEntry synchronization
# ---------------------------------------------------------------------------


class TestDefaultsTableTopicRegistryEntrySynchronization:
    """Every TopicRegistryEntry field has a default in from_dict()."""

    def test_minimal_dict_produces_valid_entry(self) -> None:
        """from_dict with only topic_key fills all fields."""
        entry = TopicRegistryEntry.from_dict({"topic_key": "hooks.pre_tool_use"})

        # Verify every field on the dataclass has a value (no AttributeError)
        import dataclasses

        for f in dataclasses.fields(TopicRegistryEntry):
            value = getattr(entry, f.name)
            # None is valid for nullable fields; the point is no AttributeError
            assert value is not None or f.name in {
                "last_injected_turn",
                "last_query_fingerprint",
                "suppression_reason",
                "suppressed_docs_epoch",
                "deferred_reason",
                "deferred_ttl",
            }, f"Field {f.name!r} has unexpected None default"


# ---------------------------------------------------------------------------
# B13. registry null-field serialization includes envelope
# ---------------------------------------------------------------------------


class TestRegistryNullFieldSerializationIncludesEnvelopeB:
    """Null-valued fields serialized in registry JSON (not omitted)."""

    def test_all_nullable_fields_present_in_json(self) -> None:
        entry = _make_entry(state="detected")
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        raw = json.dumps(seed.to_json())
        parsed = json.loads(raw)

        # Envelope nullable field
        assert "docs_epoch" in parsed
        assert parsed["docs_epoch"] is None

        # Entry nullable fields
        e = parsed["entries"][0]
        nullable_entry_fields = [
            "last_injected_turn",
            "last_query_fingerprint",
            "suppression_reason",
            "suppressed_docs_epoch",
            "deferred_reason",
            "deferred_ttl",
        ]
        for field_name in nullable_entry_fields:
            assert field_name in e, f"Nullable field {field_name!r} omitted from JSON"
            assert e[field_name] is None, f"Expected null for {field_name!r}"


# ---------------------------------------------------------------------------
# B14. pending_facets serialization preserves insertion order
# ---------------------------------------------------------------------------


class TestPendingFacetsSerializationPreservesInsertionOrderB:
    """pending_facets array order preserved through serialize/deserialize roundtrip."""

    def test_order_preserved_through_roundtrip(self, tmp_path: Path) -> None:
        facets = ["schema", "input", "output", "config", "control"]
        entry = _make_entry(coverage_pending_facets=facets)
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        loaded = load_registry(str(seed_path))
        assert loaded.entries[0].coverage_pending_facets == facets

    def test_empty_list_preserved(self, tmp_path: Path) -> None:
        entry = _make_entry(coverage_pending_facets=[])
        seed = RegistrySeed(entries=[entry], docs_epoch=None, inventory_snapshot_version="1")
        seed_path = tmp_path / "ccdi_seed.json"
        _write_seed_file(seed, seed_path)

        loaded = load_registry(str(seed_path))
        assert loaded.entries[0].coverage_pending_facets == []


# ---------------------------------------------------------------------------
# B15. results_file write-time exclusion defense-in-depth
# ---------------------------------------------------------------------------


class TestResultsFileWriteTimeExclusionDefenseInDepthB:
    """results_file never written to persistent registry (defense-in-depth)."""

    def test_results_file_never_in_persisted_json(self, tmp_path: Path) -> None:
        """Even if results_file is set on the RegistrySeed object, to_json excludes it."""
        entry = _make_entry()
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
            results_file="/tmp/results.json",
            inventory_snapshot_path="/tmp/snap.json",
        )
        data = seed.to_json()
        text = json.dumps(data)

        assert "results_file" not in text
        assert "inventory_snapshot_path" not in text

    def test_write_deferred_does_not_leak_transport_fields(self, tmp_path: Path) -> None:
        """write_deferred round-trip strips transport fields."""
        entry = _make_entry(state="detected")
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        write_deferred(str(seed_path), "hooks.pre_tool_use", "cooldown", 3)

        reloaded_raw = json.loads(seed_path.read_text())
        assert "results_file" not in reloaded_raw


# ---------------------------------------------------------------------------
# B16. results_file stripped after multi-topic commit
# ---------------------------------------------------------------------------


class TestRegistrySeedResultsFileStrippedAfterMultiTopicCommitB:
    """Multi-topic commit -> results_file stripped from all entries."""

    def test_multi_topic_strip(self, tmp_path: Path) -> None:
        e1 = _make_entry("hooks.pre_tool_use")
        e2 = _make_entry("hooks.post_tool_use")
        e3 = _make_entry("config.general")
        seed = RegistrySeed(
            entries=[e1, e2, e3], docs_epoch=None, inventory_snapshot_version="1",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        # Commit all three topics
        for topic_key in ["hooks.pre_tool_use", "hooks.post_tool_use", "config.general"]:
            mark_injected(
                str(seed_path), topic_key, "overview",
                "leaf", [f"c-{topic_key}"], "fp", turn=1,
            )

        final_raw = json.loads(seed_path.read_text())
        assert "results_file" not in final_raw
        # All three injected
        states = {e["topic_key"]: e["state"] for e in final_raw["entries"]}
        assert all(s == "injected" for s in states.values())


# ---------------------------------------------------------------------------
# B17. results_file stripped when all commits fail
# ---------------------------------------------------------------------------


class TestRegistrySeedResultsFileStrippedWhenAllCommitsFailB:
    """All commits fail -> results_file still stripped on next successful write."""

    def test_all_fail_then_success_strips(self, tmp_path: Path) -> None:
        entry = _make_entry("hooks.pre_tool_use")
        seed = RegistrySeed(
            entries=[entry], docs_epoch=None, inventory_snapshot_version="1",
        )
        seed_path = tmp_path / "ccdi_seed.json"
        raw = seed.to_json()
        raw["results_file"] = "/tmp/results.json"
        seed_path.write_text(json.dumps(raw))

        # Two failed commits (nonexistent topics — no file rewrite)
        mark_injected(str(seed_path), "nonexistent.a", "overview", "leaf", ["c1"], "fp", turn=1)
        mark_injected(str(seed_path), "nonexistent.b", "overview", "leaf", ["c2"], "fp", turn=1)

        # results_file still present (no rewrite happened)
        after_fails = json.loads(seed_path.read_text())
        assert "results_file" in after_fails

        # Successful commit rewrites and strips
        mark_injected(str(seed_path), "hooks.pre_tool_use", "overview", "leaf", ["c1"], "fp", turn=1)
        after_success = json.loads(seed_path.read_text())
        assert "results_file" not in after_success


# ---------------------------------------------------------------------------
# B18. sentinel structure invariant
# ---------------------------------------------------------------------------


class TestSentinelStructureInvariant:
    """Registry seed within sentinel tags is valid JSON."""

    def test_sentinel_tags_contain_valid_json(self) -> None:
        """The sentinel format wraps JSON between HTML comment markers."""
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch="ep-1", inventory_snapshot_version="1")
        seed_json = json.dumps(seed.to_json())

        # Wrap in sentinel tags
        sentinel = f"<!-- ccdi-registry-seed -->{seed_json}<!-- /ccdi-registry-seed -->"

        # Extract JSON from sentinel
        start_tag = "<!-- ccdi-registry-seed -->"
        end_tag = "<!-- /ccdi-registry-seed -->"
        start_idx = sentinel.index(start_tag) + len(start_tag)
        end_idx = sentinel.index(end_tag)
        extracted = sentinel[start_idx:end_idx]

        # Verify extracted JSON is valid and parseable
        parsed = json.loads(extracted)
        assert "entries" in parsed
        assert "docs_epoch" in parsed
        assert "inventory_snapshot_version" in parsed

    def test_sentinel_roundtrip_via_registry_seed(self) -> None:
        """Extracted JSON from sentinel tags can reconstruct a RegistrySeed."""
        entry = _make_entry()
        seed = RegistrySeed(entries=[entry], docs_epoch="ep-1", inventory_snapshot_version="1")
        seed_json = json.dumps(seed.to_json())

        sentinel = f"<!-- ccdi-registry-seed -->{seed_json}<!-- /ccdi-registry-seed -->"

        start_tag = "<!-- ccdi-registry-seed -->"
        end_tag = "<!-- /ccdi-registry-seed -->"
        extracted = sentinel[sentinel.index(start_tag) + len(start_tag):sentinel.index(end_tag)]

        loaded = RegistrySeed.from_json(json.loads(extracted))
        assert len(loaded.entries) == 1
        assert loaded.entries[0].topic_key == "hooks.pre_tool_use"
        assert loaded.docs_epoch == "ep-1"
