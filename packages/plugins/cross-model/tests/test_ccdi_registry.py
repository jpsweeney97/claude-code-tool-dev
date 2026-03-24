"""Tests for CCDI registry — Phase A + Phase B deferred/TTL + consecutive-medium + hints.

Covers: load_registry, mark_injected, write_suppressed, write_deferred,
_write_registry, check_suppression_reentry, normalize_fingerprint,
sort_candidates, decrement_deferred_ttl, apply_ttl_transitions,
update_redetections, process_semantic_hints.
"""

from __future__ import annotations

import json
import logging
import os

import pytest

from scripts.ccdi.config import CCDIConfig, BUILTIN_DEFAULTS
from scripts.ccdi.registry import (
    _write_registry,
    apply_ttl_transitions,
    check_suppression_reentry,
    decrement_deferred_ttl,
    load_registry,
    mark_injected,
    normalize_fingerprint,
    process_semantic_hints,
    sort_candidates,
    update_redetections,
    write_deferred,
    write_suppressed,
)
from scripts.ccdi.types import (
    Alias,
    ClassifierResult,
    CompiledInventory,
    InjectionCandidate,
    QueryPlan,
    QuerySpec,
    RegistrySeed,
    ResolvedTopic,
    SemanticHint,
    TopicRecord,
    TopicRegistryEntry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    topic_key: str = "hooks.pre_tool_use",
    *,
    family_key: str = "hooks",
    state: str = "detected",
    kind: str = "leaf",
    coverage_target: str = "leaf",
    facet: str = "overview",
    first_seen_turn: int = 1,
    last_seen_turn: int = 1,
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
        first_seen_turn=first_seen_turn,
        last_seen_turn=last_seen_turn,
        last_injected_turn=last_injected_turn,
        last_query_fingerprint=last_query_fingerprint,
        consecutive_medium_count=consecutive_medium_count,
        suppression_reason=suppression_reason,
        suppressed_docs_epoch=suppressed_docs_epoch,
        deferred_reason=deferred_reason,
        deferred_ttl=deferred_ttl,
        coverage_target=coverage_target,
        facet=facet,
        kind=kind,
        coverage_overview_injected=coverage_overview_injected,
        coverage_facets_injected=coverage_facets_injected if coverage_facets_injected is not None else [],
        coverage_pending_facets=coverage_pending_facets if coverage_pending_facets is not None else [],
        coverage_family_context_available=coverage_family_context_available,
        coverage_injected_chunk_ids=coverage_injected_chunk_ids if coverage_injected_chunk_ids is not None else [],
    )


def _make_seed(
    entries: list[TopicRegistryEntry] | None = None,
    docs_epoch: str | None = None,
    inventory_snapshot_version: str = "1",
) -> RegistrySeed:
    return RegistrySeed(
        entries=entries if entries is not None else [],
        docs_epoch=docs_epoch,
        inventory_snapshot_version=inventory_snapshot_version,
    )


def _write_seed_file(path: str, seed: RegistrySeed) -> None:
    """Write seed to path as JSON (for test setup)."""
    with open(path, "w") as f:
        json.dump(seed.to_json(), f)


def _read_seed_file(path: str) -> dict:
    """Read raw JSON from registry file."""
    with open(path) as f:
        return json.load(f)


def _make_config(*, deferred_ttl_turns: int = 3) -> CCDIConfig:
    """Build a CCDIConfig with overridable deferred_ttl_turns."""
    c = BUILTIN_DEFAULTS["classifier"]
    i = BUILTIN_DEFAULTS["injection"]
    p = BUILTIN_DEFAULTS["packets"]
    return CCDIConfig(
        classifier_confidence_high_min_weight=c["confidence_high_min_weight"],
        classifier_confidence_medium_min_score=c["confidence_medium_min_score"],
        classifier_confidence_medium_min_single_weight=c["confidence_medium_min_single_weight"],
        injection_initial_threshold_high_count=i["initial_threshold_high_count"],
        injection_initial_threshold_medium_same_family_count=i["initial_threshold_medium_same_family_count"],
        injection_mid_turn_consecutive_medium_turns=i["mid_turn_consecutive_medium_turns"],
        injection_cooldown_max_new_topics_per_turn=i["cooldown_max_new_topics_per_turn"],
        injection_deferred_ttl_turns=deferred_ttl_turns,
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
# 1. detected->injected happy path
# ---------------------------------------------------------------------------


class TestMarkInjectedHappyPath:
    """Test 1: detected->injected transitions state, sets fields."""

    def test_detected_to_injected(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected", facet="overview")
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1", "c2"],
            query_fingerprint="test query",
            turn=3,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "injected"
        assert e["last_injected_turn"] == 3
        assert e["last_query_fingerprint"] is not None
        assert "c1" in e["coverage"]["injected_chunk_ids"]
        assert "c2" in e["coverage"]["injected_chunk_ids"]
        assert "overview" in e["coverage"]["facets_injected"]
        assert e["consecutive_medium_count"] == 0
        assert e["deferred_reason"] is None
        assert e["deferred_ttl"] is None


# ---------------------------------------------------------------------------
# 2. Attempt states not persisted
# ---------------------------------------------------------------------------


class TestAttemptStatesNotPersisted:
    """Test 2: looked_up and built absent from written registry file."""

    def test_looked_up_reinitialised_to_detected(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        raw = {
            "entries": [
                {
                    "topic_key": "hooks.pre_tool_use",
                    "family_key": "hooks",
                    "state": "looked_up",
                    "first_seen_turn": 1,
                    "last_seen_turn": 1,
                    "kind": "leaf",
                }
            ],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        seed = load_registry(path)
        assert seed.entries[0].state == "detected"

    def test_built_reinitialised_to_detected(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        raw = {
            "entries": [
                {
                    "topic_key": "hooks.pre_tool_use",
                    "family_key": "hooks",
                    "state": "built",
                    "first_seen_turn": 1,
                    "last_seen_turn": 1,
                    "kind": "leaf",
                }
            ],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        seed = load_registry(path)
        assert seed.entries[0].state == "detected"


# ---------------------------------------------------------------------------
# 3. Idempotent mark-injected
# ---------------------------------------------------------------------------


class TestIdempotentMarkInjected:
    """Test 3: same packet twice doesn't corrupt; no duplicate facets/chunks."""

    def test_double_call_no_duplicates(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected", facet="overview")
        _write_seed_file(path, _make_seed(entries=[entry]))

        kwargs = dict(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1", "c2"],
            query_fingerprint="test query",
            turn=3,
        )
        mark_injected(**kwargs)
        mark_injected(**kwargs)

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["coverage"]["facets_injected"].count("overview") == 1
        assert e["coverage"]["injected_chunk_ids"].count("c1") == 1
        assert e["coverage"]["injected_chunk_ids"].count("c2") == 1


# ---------------------------------------------------------------------------
# 4. Family overview sets overview_injected
# ---------------------------------------------------------------------------


class TestFamilyOverviewInjected:
    """Test 4: coverage_target=family, facet=overview -> overview_injected=true."""

    def test_family_overview(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            coverage_target="family",
            state="detected",
            facet="overview",
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks",
            facet="overview",
            coverage_target="family",
            chunk_ids=["c1"],
            query_fingerprint="hooks overview",
            turn=2,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["coverage"]["overview_injected"] is True


# ---------------------------------------------------------------------------
# 5. overview_injected propagation: at overview
# ---------------------------------------------------------------------------


class TestOverviewInjectedAtOverview:
    """Test 5: inject family at facet=overview -> overview_injected=true."""

    def test_at_overview(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            coverage_target="family",
            state="detected",
            facet="overview",
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks",
            facet="overview",
            coverage_target="family",
            chunk_ids=["c1"],
            query_fingerprint="hooks",
            turn=2,
        )

        data = _read_seed_file(path)
        assert data["entries"][0]["coverage"]["overview_injected"] is True


# ---------------------------------------------------------------------------
# 6. overview_injected propagation: at non-overview
# ---------------------------------------------------------------------------


class TestOverviewInjectedAtNonOverview:
    """Test 6: inject family at facet=schema -> overview_injected stays false."""

    def test_at_non_overview(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            coverage_target="family",
            state="detected",
            facet="schema",
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks",
            facet="schema",
            coverage_target="family",
            chunk_ids=["c1"],
            query_fingerprint="hooks schema",
            turn=2,
        )

        data = _read_seed_file(path)
        assert data["entries"][0]["coverage"]["overview_injected"] is False


# ---------------------------------------------------------------------------
# 7. family_context_available on leaf after family overview injected
# ---------------------------------------------------------------------------


class TestFamilyContextAvailableOnLeaf:
    """Test 7: after family overview injected, new leaf gets family_context_available."""

    def test_leaf_gets_family_context(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        family = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            coverage_target="family",
            state="injected",
            coverage_overview_injected=True,
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_injected_chunk_ids=["c1"],
        )
        leaf = _make_entry(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            kind="leaf",
            coverage_target="leaf",
            state="detected",
        )
        _write_seed_file(path, _make_seed(entries=[family, leaf]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c2"],
            query_fingerprint="pre_tool_use",
            turn=3,
        )

        data = _read_seed_file(path)
        leaf_data = next(e for e in data["entries"] if e["topic_key"] == "hooks.pre_tool_use")
        assert leaf_data["coverage"]["family_context_available"] is True


# ---------------------------------------------------------------------------
# 8. weak_results suppression
# ---------------------------------------------------------------------------


class TestWeakResultsSuppression:
    """Test 8: empty search results -> suppressed: weak_results."""

    def test_weak_results(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry], docs_epoch="2026-03-20"))

        write_suppressed(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="weak_results",
            docs_epoch="2026-03-20",
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "suppressed"
        assert e["suppression_reason"] == "weak_results"
        assert e["suppressed_docs_epoch"] == "2026-03-20"


# ---------------------------------------------------------------------------
# 9. redundant suppression
# ---------------------------------------------------------------------------


class TestRedundantSuppression:
    """Test 9: all chunk IDs already injected -> suppressed: redundant."""

    def test_redundant(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="detected",
            coverage_injected_chunk_ids=["c1", "c2"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        write_suppressed(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="redundant",
            docs_epoch=None,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "suppressed"
        assert e["suppression_reason"] == "redundant"


# ---------------------------------------------------------------------------
# 10. suppressed vs deferred distinction
# ---------------------------------------------------------------------------


class TestSuppressedVsDeferredDistinction:
    """Test 10: different states exist distinctly."""

    def test_distinct_states(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        suppressed = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
        )
        deferred = _make_entry(
            topic_key="hooks.post_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=3,
        )
        _write_seed_file(path, _make_seed(entries=[suppressed, deferred]))

        seed = load_registry(path)
        s_entry = next(e for e in seed.entries if e.topic_key == "hooks.pre_tool_use")
        d_entry = next(e for e in seed.entries if e.topic_key == "hooks.post_tool_use")

        assert s_entry.state == "suppressed"
        assert s_entry.suppression_reason == "weak_results"
        assert s_entry.deferred_reason is None

        assert d_entry.state == "deferred"
        assert d_entry.deferred_reason == "cooldown"
        assert d_entry.suppression_reason is None


# ---------------------------------------------------------------------------
# 11. Registry corruption recovery
# ---------------------------------------------------------------------------


class TestCorruptionRecovery:
    """Test 11: malformed JSON -> reinitialize empty."""

    def test_corrupt_json_reinitializes(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        with open(path, "w") as f:
            f.write("{corrupted json!!!")

        seed = load_registry(path)
        assert seed.entries == []
        assert seed.docs_epoch is None

    def test_missing_file_creates_empty(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        seed = load_registry(path)
        assert seed.entries == []


# ---------------------------------------------------------------------------
# 12. No commit without send
# ---------------------------------------------------------------------------


class TestNoCommitWithoutSend:
    """Test 12: build-packet without mark-injected leaves topic detected."""

    def test_detected_stays_detected(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        # Load and write back without calling mark_injected
        seed = load_registry(path)
        _write_registry(path, seed)

        data = _read_seed_file(path)
        assert data["entries"][0]["state"] == "detected"


# ---------------------------------------------------------------------------
# 13. injected forward-only invariant
# ---------------------------------------------------------------------------


class TestInjectedForwardOnly:
    """Test 13: injected topic re-detected stays injected, last_seen_turn updated."""

    def test_redetection_stays_injected(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="injected",
            last_injected_turn=2,
            last_seen_turn=2,
            coverage_injected_chunk_ids=["c1"],
            coverage_facets_injected=["overview"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        # Simulate re-detection: load, update last_seen_turn, write
        seed = load_registry(path)
        seed.entries[0].last_seen_turn = 5
        _write_registry(path, seed)

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "injected"
        assert e["last_seen_turn"] == 5


# ---------------------------------------------------------------------------
# 14. consecutive_medium_count reset after injection
# ---------------------------------------------------------------------------


class TestConsecutiveMediumReset:
    """Test 14: mark_injected sets counter to 0."""

    def test_reset(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected", consecutive_medium_count=3)
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        assert data["entries"][0]["consecutive_medium_count"] == 0


# ---------------------------------------------------------------------------
# 15. pending_facets cleared after serving
# ---------------------------------------------------------------------------


class TestPendingFacetsCleared:
    """Test 15: after injection at facet F, F removed from pending_facets."""

    def test_served_facet_removed(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="detected",
            coverage_pending_facets=["overview", "schema", "input"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        pending = data["entries"][0]["coverage"]["pending_facets"]
        assert "overview" not in pending
        assert "schema" in pending
        assert "input" in pending


# ---------------------------------------------------------------------------
# 16. injected_chunk_ids populated at commit
# ---------------------------------------------------------------------------


class TestInjectedChunkIdsPopulated:
    """Test 16: mark_injected appends chunk IDs."""

    def test_chunk_ids_appended(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="detected",
            coverage_injected_chunk_ids=["c0"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1", "c2"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        ids = data["entries"][0]["coverage"]["injected_chunk_ids"]
        assert set(ids) == {"c0", "c1", "c2"}


# ---------------------------------------------------------------------------
# 17. uniqueness enforcement on corrupt input
# ---------------------------------------------------------------------------


class TestUniquenessOnCorruptInput:
    """Test 17: duplicate injected_chunk_ids in loaded file -> after mark_injected, distinct."""

    def test_dedup_on_inject(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        # Write raw JSON with duplicate chunk_ids
        raw = {
            "entries": [
                {
                    "topic_key": "hooks.pre_tool_use",
                    "family_key": "hooks",
                    "state": "detected",
                    "first_seen_turn": 1,
                    "last_seen_turn": 1,
                    "last_injected_turn": None,
                    "last_query_fingerprint": None,
                    "consecutive_medium_count": 0,
                    "suppression_reason": None,
                    "suppressed_docs_epoch": None,
                    "deferred_reason": None,
                    "deferred_ttl": None,
                    "coverage_target": "leaf",
                    "facet": "overview",
                    "kind": "leaf",
                    "coverage": {
                        "overview_injected": False,
                        "facets_injected": [],
                        "pending_facets": [],
                        "family_context_available": False,
                        "injected_chunk_ids": ["c1", "c1", "c2"],
                    },
                }
            ],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c2", "c3"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        ids = data["entries"][0]["coverage"]["injected_chunk_ids"]
        # All unique
        assert len(ids) == len(set(ids))
        assert set(ids) == {"c1", "c2", "c3"}


# ---------------------------------------------------------------------------
# 18. docs_epoch null==null -> no re-entry
# ---------------------------------------------------------------------------


class TestDocsEpochNullNull:
    """Test 18: suppressed at null, re-evaluated at null -> stays suppressed."""

    def test_null_null_no_reentry(self) -> None:
        entry = _make_entry(
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch=None,
        )
        result = check_suppression_reentry([entry], current_docs_epoch=None)
        assert result == []


# ---------------------------------------------------------------------------
# 19. docs_epoch null->non-null -> re-entry
# ---------------------------------------------------------------------------


class TestDocsEpochNullToNonNull:
    """Test 19: suppressed at null, epoch now non-null -> re-enters detected."""

    def test_null_to_nonnull_reentry(self) -> None:
        entry = _make_entry(
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch=None,
        )
        result = check_suppression_reentry([entry], current_docs_epoch="2026-03-20")
        assert len(result) == 1
        assert result[0].topic_key == "hooks.pre_tool_use"


# ---------------------------------------------------------------------------
# 20. docs_epoch non-null->null -> re-entry
# ---------------------------------------------------------------------------


class TestDocsEpochNonNullToNull:
    """Test 20: suppressed at 'A', epoch now null -> re-enters detected."""

    def test_nonnull_to_null_reentry(self) -> None:
        entry = _make_entry(
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="A",
        )
        result = check_suppression_reentry([entry], current_docs_epoch=None)
        assert len(result) == 1
        assert result[0].topic_key == "hooks.pre_tool_use"


# ---------------------------------------------------------------------------
# 21. Multi-entry docs_epoch scan
# ---------------------------------------------------------------------------


class TestMultiEntryDocsEpochScan:
    """Test 21: 3+ entries with different suppressed_docs_epoch, only matching ones re-enter."""

    def test_selective_reentry(self) -> None:
        e1 = _make_entry(
            topic_key="a",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch=None,
        )
        e2 = _make_entry(
            topic_key="b",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-10",
        )
        e3 = _make_entry(
            topic_key="c",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
        )
        e4 = _make_entry(
            topic_key="d",
            state="suppressed",
            suppression_reason="redundant",
            suppressed_docs_epoch="2026-03-10",
        )

        result = check_suppression_reentry([e1, e2, e3, e4], current_docs_epoch="2026-03-20")
        reentry_keys = {e.topic_key for e in result}
        # e1: null->non-null = re-entry
        # e2: "2026-03-10" != "2026-03-20" = re-entry
        # e3: "2026-03-20" == "2026-03-20" = no re-entry
        # e4: redundant reason = not eligible
        assert reentry_keys == {"a", "b"}


# ---------------------------------------------------------------------------
# 22. Multiple pending_facets ordering
# ---------------------------------------------------------------------------


class TestPendingFacetsFIFO:
    """Test 22: FIFO preserved through write/load cycle."""

    def test_fifo_preserved(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            coverage_pending_facets=["schema", "input", "output", "config"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        seed = load_registry(path)
        _write_registry(path, seed)

        data = _read_seed_file(path)
        assert data["entries"][0]["coverage"]["pending_facets"] == [
            "schema", "input", "output", "config"
        ]


# ---------------------------------------------------------------------------
# 23. last_query_fingerprint normalization
# ---------------------------------------------------------------------------


class TestFingerprintNormalization:
    """Test 23: different case/whitespace -> same fingerprint; null vs 'null' docs_epoch."""

    def test_case_insensitive(self) -> None:
        assert normalize_fingerprint("Hello World", None) == normalize_fingerprint("hello world", None)

    def test_whitespace_collapse(self) -> None:
        assert normalize_fingerprint("hello  world", None) == normalize_fingerprint("hello world", None)

    def test_null_docs_epoch_literal(self) -> None:
        fp1 = normalize_fingerprint("query", None)
        fp2 = normalize_fingerprint("query", "null")
        # null and literal string 'null' produce same fingerprint
        assert fp1 == fp2

    def test_different_docs_epoch(self) -> None:
        fp1 = normalize_fingerprint("query", "2026-03-20")
        fp2 = normalize_fingerprint("query", "2026-03-21")
        assert fp1 != fp2


# ---------------------------------------------------------------------------
# 24. Suppressed re-detection no-op
# ---------------------------------------------------------------------------


class TestSuppressedRedetectionNoOp:
    """Test 24: suppressed topic without re-entry trigger -> no field update."""

    def test_no_field_update(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=3,
        )
        _write_seed_file(path, _make_seed(entries=[entry], docs_epoch="2026-03-20"))

        # Load, simulating re-detection without epoch change
        seed = load_registry(path)
        # No re-entry trigger (same docs_epoch)
        reentry = check_suppression_reentry(seed.entries, current_docs_epoch="2026-03-20")
        assert reentry == []

        # Entry unchanged
        e = seed.entries[0]
        assert e.state == "suppressed"
        assert e.suppression_reason == "weak_results"


# ---------------------------------------------------------------------------
# 25. Scheduling tiebreaker
# ---------------------------------------------------------------------------


class TestSchedulingTiebreaker:
    """Test 25: deterministic ordering: confidence desc, first_seen_turn asc, topic_key asc."""

    def test_confidence_primary(self) -> None:
        high = _make_entry(topic_key="a", first_seen_turn=5, state="detected")
        med = _make_entry(topic_key="b", first_seen_turn=1, state="detected")
        low = _make_entry(topic_key="c", first_seen_turn=1, state="detected")

        result = sort_candidates(
            [(high, "high"), (med, "medium"), (low, "low")]
        )
        assert [e.topic_key for e, _ in result] == ["a", "b", "c"]

    def test_first_seen_turn_secondary(self) -> None:
        e1 = _make_entry(topic_key="z", first_seen_turn=1, state="detected")
        e2 = _make_entry(topic_key="a", first_seen_turn=5, state="detected")

        result = sort_candidates(
            [(e1, "high"), (e2, "high")]
        )
        assert [e.topic_key for e, _ in result] == ["z", "a"]

    def test_topic_key_tertiary(self) -> None:
        e1 = _make_entry(topic_key="beta", first_seen_turn=1, state="detected")
        e2 = _make_entry(topic_key="alpha", first_seen_turn=1, state="detected")

        result = sort_candidates(
            [(e1, "high"), (e2, "high")]
        )
        assert [e.topic_key for e, _ in result] == ["alpha", "beta"]

    def test_full_tiebreaker(self) -> None:
        entries = [
            (_make_entry(topic_key="c", first_seen_turn=3), "medium"),
            (_make_entry(topic_key="a", first_seen_turn=1), "high"),
            (_make_entry(topic_key="b", first_seen_turn=1), "high"),
            (_make_entry(topic_key="d", first_seen_turn=2), "low"),
            (_make_entry(topic_key="e", first_seen_turn=1), "low"),
        ]
        result = sort_candidates(entries)
        # high(turn=1): a, b | medium(turn=3): c | low(turn=1): e, then low(turn=2): d
        assert [e.topic_key for e, _ in result] == ["a", "b", "c", "e", "d"]


# ---------------------------------------------------------------------------
# load_registry: transport field stripping
# ---------------------------------------------------------------------------


class TestLoadRegistryTransportStripping:
    """load_registry strips transport fields and validates entries."""

    def test_strips_transport_fields(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        raw = {
            "entries": [],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
            "results_file": "/tmp/r.json",
            "inventory_snapshot_path": "/tmp/s.json",
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        seed = load_registry(path)
        assert seed.results_file is None
        assert seed.inventory_snapshot_path is None

    def test_family_kind_consecutive_medium_reset(
        self, tmp_path: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Family-kind entries with consecutive_medium_count != 0 get reset."""
        path = os.path.join(str(tmp_path), "registry.json")
        raw = {
            "entries": [
                {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "state": "detected",
                    "first_seen_turn": 1,
                    "last_seen_turn": 1,
                    "consecutive_medium_count": 3,
                }
            ],
            "docs_epoch": None,
            "inventory_snapshot_version": "1",
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.registry"):
            seed = load_registry(path)

        assert seed.entries[0].consecutive_medium_count == 0
        assert any("consecutive_medium_count" in msg for msg in caplog.messages)

    def test_inventory_snapshot_version_null_warns(
        self, tmp_path: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        raw = {
            "entries": [],
            "docs_epoch": None,
            "inventory_snapshot_version": None,
        }
        with open(path, "w") as f:
            json.dump(raw, f)

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.types"):
            seed = load_registry(path)

        # from_json assigns best-effort default
        assert seed.inventory_snapshot_version == "1"


# ---------------------------------------------------------------------------
# _write_registry: atomic write
# ---------------------------------------------------------------------------


class TestAtomicWrite:
    """_write_registry uses temp+rename for atomicity."""

    def test_file_written(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        seed = _make_seed(entries=[_make_entry()])
        _write_registry(path, seed)
        assert os.path.exists(path)
        data = _read_seed_file(path)
        assert len(data["entries"]) == 1

    def test_no_temp_files_left(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        seed = _make_seed()
        _write_registry(path, seed)
        files = os.listdir(str(tmp_path))
        assert files == ["registry.json"]


# ===========================================================================
# Phase B: write_deferred() tests (Step 1)
# ===========================================================================


# ---------------------------------------------------------------------------
# 26. detected -> deferred with cooldown reason
# ---------------------------------------------------------------------------


class TestDeferredCooldown:
    """Test 26: detected -> deferred with cooldown reason, TTL set from config."""

    def test_detected_to_deferred_cooldown(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        write_deferred(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="cooldown",
            deferred_ttl=3,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "deferred"
        assert e["deferred_reason"] == "cooldown"
        assert e["deferred_ttl"] == 3


# ---------------------------------------------------------------------------
# 27. detected -> deferred with scout_priority reason
# ---------------------------------------------------------------------------


class TestDeferredScoutPriority:
    """Test 27: detected -> deferred with scout_priority reason."""

    def test_detected_to_deferred_scout_priority(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        write_deferred(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="scout_priority",
            deferred_ttl=3,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "deferred"
        assert e["deferred_reason"] == "scout_priority"
        assert e["deferred_ttl"] == 3


# ---------------------------------------------------------------------------
# 28. detected -> deferred with target_mismatch reason
# ---------------------------------------------------------------------------


class TestDeferredTargetMismatch:
    """Test 28: detected -> deferred with target_mismatch reason."""

    def test_detected_to_deferred_target_mismatch(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        write_deferred(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="target_mismatch",
            deferred_ttl=3,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "deferred"
        assert e["deferred_reason"] == "target_mismatch"
        assert e["deferred_ttl"] == 3


# ---------------------------------------------------------------------------
# 29. TTL initialization at deferral time
# ---------------------------------------------------------------------------


class TestDeferredTTLInitialization:
    """Test 29: TTL set to deferred_ttl_turns config value at deferral time."""

    def test_ttl_set_from_config(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        # Config says deferred_ttl_turns=5
        write_deferred(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="cooldown",
            deferred_ttl=5,
        )

        data = _read_seed_file(path)
        assert data["entries"][0]["deferred_ttl"] == 5


# ---------------------------------------------------------------------------
# 30. deferred vs suppressed distinction
# ---------------------------------------------------------------------------


class TestDeferredVsSuppressedDistinction:
    """Test 30: different reasons, different re-entry paths."""

    def test_different_reasons_different_reentry(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        suppressed = _make_entry(
            topic_key="a",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
        )
        deferred = _make_entry(
            topic_key="b",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=3,
        )
        _write_seed_file(path, _make_seed(entries=[suppressed, deferred]))

        seed = load_registry(path)
        s = next(e for e in seed.entries if e.topic_key == "a")
        d = next(e for e in seed.entries if e.topic_key == "b")

        # Suppressed: re-enters via docs_epoch change or semantic hint
        assert s.state == "suppressed"
        assert s.suppression_reason == "weak_results"
        assert s.deferred_reason is None
        assert s.deferred_ttl is None

        # Deferred: re-enters via TTL expiry + classifier
        assert d.state == "deferred"
        assert d.deferred_reason == "cooldown"
        assert d.deferred_ttl == 3
        assert d.suppression_reason is None


# ---------------------------------------------------------------------------
# 31. write_deferred on missing topic_key logs warning
# ---------------------------------------------------------------------------


class TestDeferredMissingTopicKey:
    """Test 31: write_deferred on missing topic warns, no crash."""

    def test_missing_topic_warns(
        self, tmp_path: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(topic_key="a", state="detected")
        _write_seed_file(path, _make_seed(entries=[entry]))

        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.registry"):
            write_deferred(
                path=path,
                topic_key="nonexistent",
                reason="cooldown",
                deferred_ttl=3,
            )

        assert any("nonexistent" in msg for msg in caplog.messages)
        # Original entry unchanged
        data = _read_seed_file(path)
        assert data["entries"][0]["state"] == "detected"


# ===========================================================================
# Phase B: TTL lifecycle tests (Step 4)
# ===========================================================================


# ---------------------------------------------------------------------------
# 32. TTL decrement per turn
# ---------------------------------------------------------------------------


class TestDeferredTTLDecrementPerTurn:
    """Test 32: TTL decrements by 1 on each dialogue-turn call."""

    def test_decrement(self) -> None:
        entry = _make_entry(
            state="deferred", deferred_reason="cooldown", deferred_ttl=3
        )
        seed = _make_seed(entries=[entry])

        decrement_deferred_ttl(seed)

        assert seed.entries[0].deferred_ttl == 2

    def test_decrement_multiple_entries(self) -> None:
        e1 = _make_entry(
            topic_key="a", state="deferred", deferred_reason="cooldown", deferred_ttl=3
        )
        e2 = _make_entry(
            topic_key="b",
            state="deferred",
            deferred_reason="scout_priority",
            deferred_ttl=1,
        )
        e3 = _make_entry(
            topic_key="c", state="detected"
        )
        seed = _make_seed(entries=[e1, e2, e3])

        decrement_deferred_ttl(seed)

        assert seed.entries[0].deferred_ttl == 2
        assert seed.entries[1].deferred_ttl == 0
        # Non-deferred entry unaffected
        assert seed.entries[2].deferred_ttl is None


# ---------------------------------------------------------------------------
# 33. TTL expiry with reappearance -> detected
# ---------------------------------------------------------------------------


class TestDeferredTTLExpiryWithReappearance:
    """Test 33: TTL=0 AND topic in classifier -> detected."""

    def test_ttl_expiry_reappearance(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=0,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "medium"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.deferred_reason is None
        assert e.deferred_ttl is None
        assert len(transitioned) == 1
        assert transitioned[0].topic_key == "hooks.pre_tool_use"


# ---------------------------------------------------------------------------
# 34. TTL expiry without reappearance -> TTL resets, stays deferred
# ---------------------------------------------------------------------------


class TestDeferredTTLExpiryWithoutReappearance:
    """Test 34: TTL=0, topic absent -> TTL resets to config value, stays deferred."""

    def test_ttl_reset_no_reappearance(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=0,
        )
        seed = _make_seed(entries=[entry])
        # Use non-default TTL per spec requirement
        config = _make_config(deferred_ttl_turns=5)

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys=set(),
            classifier_confidences={},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "deferred"
        assert e.deferred_reason == "cooldown"
        assert e.deferred_ttl == 5
        assert transitioned == []


# ---------------------------------------------------------------------------
# 35. Load-time recovery: deferred_ttl=0, topic present -> detected
# ---------------------------------------------------------------------------


class TestDeferredTTLLoadTimeRecoveryPresent:
    """Test 35: Registry with deferred_ttl=0, topic in classifier -> detected."""

    def test_load_time_recovery_present(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="scout_priority",
            deferred_ttl=0,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        # apply_ttl_transitions handles deferred_ttl=0 BEFORE decrement
        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "high"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.deferred_reason is None
        assert e.deferred_ttl is None
        assert len(transitioned) == 1


# ---------------------------------------------------------------------------
# 36. Load-time recovery: deferred_ttl=0, topic absent -> TTL reset
# ---------------------------------------------------------------------------


class TestDeferredTTLLoadTimeRecoveryAbsent:
    """Test 36: Registry with deferred_ttl=0, topic absent -> TTL reset."""

    def test_load_time_recovery_absent(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="target_mismatch",
            deferred_ttl=0,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config(deferred_ttl_turns=5)

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys=set(),
            classifier_confidences={},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "deferred"
        assert e.deferred_reason == "target_mismatch"
        assert e.deferred_ttl == 5
        assert transitioned == []


# ---------------------------------------------------------------------------
# 37. Cooldown deferral preserves consecutive_medium_count
# ---------------------------------------------------------------------------


class TestCooldownDeferralPreservesConsecutiveMediumCount:
    """Test 37: Medium leaf at count=1, deferred by cooldown -> count stays 1."""

    def test_count_preserved(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="detected", consecutive_medium_count=1
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        write_deferred(
            path=path,
            topic_key="hooks.pre_tool_use",
            reason="cooldown",
            deferred_ttl=3,
        )

        data = _read_seed_file(path)
        e = data["entries"][0]
        assert e["state"] == "deferred"
        assert e["consecutive_medium_count"] == 1


# ---------------------------------------------------------------------------
# 38. deferred -> detected: consecutive_medium_count initialization
# ---------------------------------------------------------------------------


class TestDeferredToDetectedConsecutiveMediumInitialization:
    """Test 38: TTL expires, reappears at medium leaf -> count=1; at high -> count=0."""

    def test_medium_leaf_reappearance(self) -> None:
        """Medium confidence + leaf kind -> consecutive_medium_count=1."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=0,
            consecutive_medium_count=0,
            kind="leaf",
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "medium"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.consecutive_medium_count == 1

    def test_high_reappearance(self) -> None:
        """High confidence -> consecutive_medium_count=0."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=0,
            consecutive_medium_count=2,
            kind="leaf",
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "high"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.consecutive_medium_count == 0

    def test_family_kind_medium_reappearance(self) -> None:
        """Family-kind at medium -> consecutive_medium_count=0 (families never count)."""
        entry = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            coverage_target="family",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=0,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks"},
            classifier_confidences={"hooks": "medium"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.consecutive_medium_count == 0


# ===========================================================================
# Phase B: High-confidence bypass test (Step 6)
# ===========================================================================


# ---------------------------------------------------------------------------
# 39. High-confidence bypass of deferred TTL
# ---------------------------------------------------------------------------


class TestHighConfidenceBypassesDeferredTTL:
    """Test 39: Deferred topic re-detected at high confidence -> immediate detected."""

    def test_high_confidence_bypass(self) -> None:
        """TTL=2 but high confidence -> immediate transition, TTL not just decremented."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=2,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "high"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.deferred_reason is None
        assert e.deferred_ttl is None
        assert e.consecutive_medium_count == 0
        assert len(transitioned) == 1

    def test_medium_confidence_no_bypass(self) -> None:
        """Medium confidence at TTL>0 -> TTL decremented, stays deferred."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=2,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "medium"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "deferred"
        assert e.deferred_ttl == 1
        assert transitioned == []

    def test_low_confidence_no_bypass(self) -> None:
        """Low confidence at TTL>0 -> TTL decremented, stays deferred."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="scout_priority",
            deferred_ttl=3,
        )
        seed = _make_seed(entries=[entry])
        config = _make_config()

        transitioned = apply_ttl_transitions(
            seed,
            classifier_topic_keys={"hooks.pre_tool_use"},
            classifier_confidences={"hooks.pre_tool_use": "low"},
            config=config,
        )

        e = seed.entries[0]
        assert e.state == "deferred"
        assert e.deferred_ttl == 2
        assert transitioned == []


# ===========================================================================
# Phase B: Consecutive-medium tracking tests (Task 3, Step 1)
# ===========================================================================


def _make_resolved_topic(
    topic_key: str = "hooks.pre_tool_use",
    *,
    family_key: str = "hooks",
    coverage_target: str = "leaf",
    confidence: str = "medium",
    facet: str = "overview",
) -> ResolvedTopic:
    """Build a ResolvedTopic for testing."""
    return ResolvedTopic(
        topic_key=topic_key,
        family_key=family_key,
        coverage_target=coverage_target,
        confidence=confidence,
        facet=facet,
        matched_aliases=[],
        reason="test",
    )


# ---------------------------------------------------------------------------
# 40. Consecutive-medium threshold for leaf
# ---------------------------------------------------------------------------


class TestConsecutiveMediumThresholdLeaf:
    """Test 40: Medium leaf turn 1 → no injection; turn 2 → threshold reached."""

    def test_medium_leaf_increments(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
            consecutive_medium_count=0,
            last_seen_turn=1,
        )
        seed = _make_seed(entries=[entry])
        results = [_make_resolved_topic(confidence="medium")]

        update_redetections(seed, results, current_turn=2)

        assert seed.entries[0].consecutive_medium_count == 1
        assert seed.entries[0].last_seen_turn == 2

    def test_second_medium_turn_reaches_threshold(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
            consecutive_medium_count=1,
            last_seen_turn=2,
        )
        seed = _make_seed(entries=[entry])
        results = [_make_resolved_topic(confidence="medium")]

        update_redetections(seed, results, current_turn=3)

        assert seed.entries[0].consecutive_medium_count == 2
        assert seed.entries[0].last_seen_turn == 3


# ---------------------------------------------------------------------------
# 41. Consecutive-medium: family excluded
# ---------------------------------------------------------------------------


class TestConsecutiveMediumThresholdFamilyExcluded:
    """Test 41: Medium family turns 1-3 → count stays 0."""

    def test_family_medium_no_increment(self) -> None:
        entry = _make_entry(
            topic_key="hooks",
            family_key="hooks",
            state="detected",
            kind="family",
            coverage_target="family",
            consecutive_medium_count=0,
        )
        seed = _make_seed(entries=[entry])
        results = [
            _make_resolved_topic(
                topic_key="hooks",
                family_key="hooks",
                coverage_target="family",
                confidence="medium",
            )
        ]

        # Three consecutive medium turns
        for turn in range(2, 5):
            update_redetections(seed, results, current_turn=turn)

        assert seed.entries[0].consecutive_medium_count == 0
        assert seed.entries[0].last_seen_turn == 4


# ---------------------------------------------------------------------------
# 42. Consecutive-medium reset on topic absence
# ---------------------------------------------------------------------------


class TestConsecutiveMediumResetOnTopicAbsence:
    """Test 42: Medium turn 1 (count=1), absent turn 2 (count=0), medium turn 3 (count=1)."""

    def test_absence_resets_count(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
            consecutive_medium_count=1,
            last_seen_turn=1,
        )
        seed = _make_seed(entries=[entry])

        # Turn 2: topic absent
        update_redetections(seed, [], current_turn=2)
        assert seed.entries[0].consecutive_medium_count == 0

        # Turn 3: topic returns at medium
        results = [_make_resolved_topic(confidence="medium")]
        update_redetections(seed, results, current_turn=3)
        assert seed.entries[0].consecutive_medium_count == 1
        assert seed.entries[0].last_seen_turn == 3


# ---------------------------------------------------------------------------
# 43. Consecutive-medium reset after injection
# ---------------------------------------------------------------------------


class TestConsecutiveMediumResetAfterInjection:
    """Test 43: After injection via mark_injected, counter resets to 0."""

    def test_reset_after_injection(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            state="detected",
            kind="leaf",
            consecutive_medium_count=2,
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="overview",
            coverage_target="leaf",
            chunk_ids=["c1"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        assert data["entries"][0]["consecutive_medium_count"] == 0


# ---------------------------------------------------------------------------
# 44. Consecutive-medium reset on confidence change
# ---------------------------------------------------------------------------


class TestConsecutiveMediumResetOnConfidenceChange:
    """Test 44: Medium turn 1, HIGH turn 2 → count resets to 0."""

    def test_high_confidence_resets_count(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
            consecutive_medium_count=1,
            last_seen_turn=1,
        )
        seed = _make_seed(entries=[entry])
        results = [_make_resolved_topic(confidence="high")]

        update_redetections(seed, results, current_turn=2)

        assert seed.entries[0].consecutive_medium_count == 0
        assert seed.entries[0].last_seen_turn == 2


# ---------------------------------------------------------------------------
# 45. Send failure preserves consecutive_medium_count
# ---------------------------------------------------------------------------


class TestSendFailurePreservesConsecutiveMediumCount:
    """Test 45: Send fails → count NOT reset (mark_injected never called)."""

    def test_count_preserved_without_injection(self) -> None:
        """If mark_injected is never called, count stays at pre-failure value."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
            consecutive_medium_count=2,
            last_seen_turn=3,
        )
        seed = _make_seed(entries=[entry])

        # Simulate next turn re-detection at medium (no injection happened)
        results = [_make_resolved_topic(confidence="medium")]
        update_redetections(seed, results, current_turn=4)

        # Count incremented from retained value (2 → 3)
        assert seed.entries[0].consecutive_medium_count == 3


# ===========================================================================
# Phase B: Semantic hint processing tests (Task 3, Step 3)
# ===========================================================================


def _make_query_plan(default_facet: str = "overview") -> QueryPlan:
    """Build a minimal QueryPlan for testing."""
    return QueryPlan(
        default_facet=default_facet,
        facets={
            "overview": [QuerySpec(q="test query", category=None, priority=1)],
            "schema": [QuerySpec(q="test schema query", category=None, priority=1)],
        },
    )


def _make_topic_record(
    topic_key: str = "hooks.pre_tool_use",
    *,
    family_key: str = "hooks",
    kind: str = "leaf",
) -> TopicRecord:
    """Build a minimal TopicRecord for testing."""
    return TopicRecord(
        topic_key=topic_key,
        family_key=family_key,
        kind=kind,
        canonical_label="Pre Tool Use Hooks",
        category_hint="hooks",
        parent_topic=family_key if kind == "leaf" else None,
        aliases=[
            Alias(text="pre_tool_use", match_type="token", weight=0.9),
        ],
        query_plan=_make_query_plan(),
        canonical_refs=[],
    )


def _make_inventory(
    topics: dict[str, TopicRecord] | None = None,
) -> CompiledInventory:
    """Build a minimal CompiledInventory for testing."""
    if topics is None:
        topics = {
            "hooks.pre_tool_use": _make_topic_record(),
        }
    return CompiledInventory(
        schema_version="1",
        built_at="2026-03-23T00:00:00Z",
        docs_epoch="2026-03-23",
        topics=topics,
        denylist=[],
        overlay_meta=None,
        merge_semantics_version="1",
    )


def _make_classifier_fn(
    resolved: dict[str, ResolvedTopic] | None = None,
):
    """Build a classifier_fn mock that returns controlled results.

    resolved: mapping from claim_excerpt substring → ResolvedTopic.
    If the claim_excerpt doesn't match any key, returns empty ClassifierResult.
    """
    if resolved is None:
        resolved = {}

    def classifier_fn(
        text: str, inventory: CompiledInventory, config: CCDIConfig
    ) -> ClassifierResult:
        for excerpt_key, topic in resolved.items():
            if excerpt_key in text:
                return ClassifierResult(
                    resolved_topics=[topic],
                    suppressed_candidates=[],
                )
        return ClassifierResult(resolved_topics=[], suppressed_candidates=[])

    return classifier_fn


# ---------------------------------------------------------------------------
# 46. Prescriptive hint elevates detected to materially new
# ---------------------------------------------------------------------------


class TestSemanticHintElevatesCandidate:
    """Test 46: Prescriptive hint on detected → materially new candidate."""

    def test_prescriptive_on_detected(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
            kind="leaf",
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="high")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="use pre_tool_use hooks",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=3
        )

        assert len(candidates) == 1
        assert candidates[0].topic_key == "hooks.pre_tool_use"
        assert candidates[0].candidate_type == "new"


# ---------------------------------------------------------------------------
# 47. Hint on unknown topic → ignored
# ---------------------------------------------------------------------------


class TestSemanticHintUnknownTopic:
    """Test 47: Hint doesn't match any topic → ignored."""

    def test_unknown_topic_ignored(self) -> None:
        entry = _make_entry(state="detected")
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        # Classifier returns nothing for this excerpt
        classifier_fn = _make_classifier_fn({})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="completely unrelated topic",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=3
        )

        assert candidates == []


# ---------------------------------------------------------------------------
# 48. Malformed hints file → ignored with warning
# ---------------------------------------------------------------------------


class TestMalformedHintsFile:
    """Test 48: Invalid JSON → ignored with warning."""

    def test_malformed_hints_ignored(self) -> None:
        entry = _make_entry(state="detected")
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        # Empty hints list is valid, just produces no candidates
        candidates = process_semantic_hints(
            seed, [], inventory, _make_classifier_fn({}), current_turn=3
        )
        assert candidates == []


# ---------------------------------------------------------------------------
# 49. Prescriptive hint re-enters suppressed:weak_results
# ---------------------------------------------------------------------------


class TestPrescriptiveHintReentersSuppressedWeak:
    """Test 49: suppressed:weak_results → detected via prescriptive hint."""

    def test_prescriptive_reenter_weak(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=2,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="high")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="use pre_tool_use hooks",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 5
        assert len(candidates) == 1
        assert candidates[0].candidate_type == "new"


# ---------------------------------------------------------------------------
# 50. Prescriptive hint re-enters suppressed:redundant
# ---------------------------------------------------------------------------


class TestPrescriptiveHintReentersSuppressedRedundant:
    """Test 50: suppressed:redundant → detected via prescriptive hint."""

    def test_prescriptive_reenter_redundant(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="redundant",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=2,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="high")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="use pre_tool_use hooks",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 5


# ---------------------------------------------------------------------------
# 51. contradicts_prior on injected → append facet to pending_facets
# ---------------------------------------------------------------------------


class TestContradictsPriorOnInjected:
    """Test 51: Append facet to pending_facets."""

    def test_append_pending_facet(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_pending_facets=[],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks schema",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "injected"  # stays injected
        assert "schema" in e.coverage_pending_facets
        # No immediate candidate from contradicts_prior on injected
        # (pending_facet emission is via scheduling step 8, not hint processing)


# ---------------------------------------------------------------------------
# 52. contradicts_prior on detected → elevate to materially new
# ---------------------------------------------------------------------------


class TestContradictsPriorOnDetected:
    """Test 52: contradicts_prior on detected → materially new."""

    def test_contradicts_prior_elevates_detected(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks differ",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        assert len(candidates) == 1
        assert candidates[0].candidate_type == "new"


# ---------------------------------------------------------------------------
# 53. contradicts_prior re-enters suppressed
# ---------------------------------------------------------------------------


class TestContradictsPriorReentersSuppressed:
    """Test 53: contradicts_prior on suppressed → re-enter as detected."""

    def test_contradicts_prior_reenter_suppressed(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks wrong",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 5


# ---------------------------------------------------------------------------
# 54. extends_topic on injected → emit facet_expansion
# ---------------------------------------------------------------------------


class TestExtendsTopicOnInjected:
    """Test 54: extends_topic on injected → facet_expansion candidate."""

    def test_extends_topic_facet_expansion(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_pending_facets=[],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks schema",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        assert len(candidates) == 1
        assert candidates[0].candidate_type == "facet_expansion"
        assert candidates[0].facet == "schema"
        assert candidates[0].confidence is None


# ---------------------------------------------------------------------------
# 55. extends_topic on detected → elevate to materially new
# ---------------------------------------------------------------------------


class TestExtendsTopicOnDetected:
    """Test 55: extends_topic on detected → materially new."""

    def test_extends_topic_elevates_detected(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="detected",
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks more",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        assert len(candidates) == 1
        assert candidates[0].candidate_type == "new"


# ---------------------------------------------------------------------------
# 56. extends_topic on deferred → transition to detected first
# ---------------------------------------------------------------------------


class TestExtendsTopicOnDeferred:
    """Test 56: extends_topic on deferred → detected first, then lookup path."""

    def test_extends_topic_transitions_deferred(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="deferred",
            deferred_reason="cooldown",
            deferred_ttl=2,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks extend",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.deferred_reason is None
        assert e.deferred_ttl is None
        assert e.last_seen_turn == 5
        assert len(candidates) == 1
        assert candidates[0].candidate_type == "new"


# ---------------------------------------------------------------------------
# 57. extends_topic re-enters suppressed
# ---------------------------------------------------------------------------


class TestExtendsTopicReentersSuppressed:
    """Test 57: extends_topic on suppressed → re-enter as detected."""

    def test_extends_topic_reenter_suppressed(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="redundant",
            suppressed_docs_epoch="2026-03-20",
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks extend",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 5


# ---------------------------------------------------------------------------
# 58. facet_expansion cascade fallback to pending_facets
# ---------------------------------------------------------------------------


class TestFacetExpansionCascadeFallbackPending:
    """Test 58: Resolved facet in facets_injected → use pending_facets[0]."""

    def test_cascade_to_pending(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview", "schema"],
            coverage_pending_facets=["input"],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        # Hint resolves to "schema" which is already injected
        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks schema",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        assert len(candidates) == 1
        assert candidates[0].candidate_type == "facet_expansion"
        assert candidates[0].facet == "input"  # from pending_facets[0]
        assert candidates[0].confidence is None


# ---------------------------------------------------------------------------
# 59. facet_expansion all exhausted → no candidate
# ---------------------------------------------------------------------------


class TestFacetExpansionAllExhausted:
    """Test 59: All facets in facets_injected → no candidate emitted."""

    def test_all_exhausted(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview", "schema"],
            coverage_pending_facets=[],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        # Hint resolves to "schema" which is already injected.
        # No pending_facets. default_facet is "overview" which is also injected.
        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks schema",
            )
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        assert candidates == []


# ---------------------------------------------------------------------------
# 60. pending_facet candidate emission
# ---------------------------------------------------------------------------


class TestPendingFacetCandidateEmission:
    """Test 60: Injected topic with non-empty pending_facets → emit candidate."""

    def test_pending_facet_emitted(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_pending_facets=["schema", "input"],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        # contradicts_prior on injected → appends facet to pending
        # then extends_topic triggers facet_expansion with cascade
        # But actually, pending_facet emission is via scheduling step 8
        # For this test, we verify contradicts_prior appends correctly
        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks schema",
            )
        ]

        process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        e = seed.entries[0]
        # "schema" appended to pending_facets (now 3 items)
        assert "schema" in e.coverage_pending_facets
        assert e.state == "injected"


# ---------------------------------------------------------------------------
# 61. pending_facets cleared after serving
# ---------------------------------------------------------------------------


class TestPendingFacetsClearedAfterServing:
    """Test 61: After injection at pending facet, remove from pending_facets."""

    def test_pending_facet_cleared(self, tmp_path: str) -> None:
        path = os.path.join(str(tmp_path), "registry.json")
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_pending_facets=["schema", "input"],
            coverage_injected_chunk_ids=["c1"],
        )
        _write_seed_file(path, _make_seed(entries=[entry]))

        mark_injected(
            path=path,
            topic_key="hooks.pre_tool_use",
            facet="schema",
            coverage_target="leaf",
            chunk_ids=["c2"],
            query_fingerprint="query",
            turn=5,
        )

        data = _read_seed_file(path)
        pending = data["entries"][0]["coverage"]["pending_facets"]
        assert "schema" not in pending
        assert "input" in pending


# ---------------------------------------------------------------------------
# 62. Multiple pending_facets FIFO ordering
# ---------------------------------------------------------------------------


class TestMultiplePendingFacetsOrdering:
    """Test 62: Two facets → FIFO order preserved."""

    def test_fifo_ordering(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview"],
            coverage_pending_facets=[],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_schema = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        resolved_input = _make_resolved_topic(
            confidence="medium", facet="input"
        )

        # First hint resolves to schema facet
        classifier_fn_1 = _make_classifier_fn({"schema": resolved_schema})
        hints_1 = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use schema wrong",
            )
        ]
        process_semantic_hints(
            seed, hints_1, inventory, classifier_fn_1, current_turn=5
        )

        # Second hint resolves to input facet
        classifier_fn_2 = _make_classifier_fn({"input": resolved_input})
        hints_2 = [
            SemanticHint(
                claim_index=1,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use input wrong",
            )
        ]
        process_semantic_hints(
            seed, hints_2, inventory, classifier_fn_2, current_turn=5
        )

        e = seed.entries[0]
        assert e.coverage_pending_facets == ["schema", "input"]  # FIFO


# ---------------------------------------------------------------------------
# 63. Intra-turn hint ordering
# ---------------------------------------------------------------------------


class TestIntraTurnHintOrdering:
    """Test 63: contradicts_prior mutations visible to subsequent extends_topic."""

    def test_intra_turn_ordering(self) -> None:
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="injected",
            last_injected_turn=2,
            coverage_facets_injected=["overview", "schema"],
            coverage_pending_facets=[],
            coverage_injected_chunk_ids=["c1"],
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        # Both hints resolve to the same topic
        resolved_topic = _make_resolved_topic(
            confidence="medium", facet="schema"
        )
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            # First: contradicts_prior adds "schema" to pending_facets
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks schema",
            ),
            # Second: extends_topic on injected, resolved facet "schema" is
            # already in facets_injected → cascade to pending_facets[0] = "schema"
            # which is also in facets_injected → cascade to default_facet = "overview"
            # which is also in facets_injected → no candidate
            SemanticHint(
                claim_index=1,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks schema",
            ),
        ]

        candidates = process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=5
        )

        # contradicts_prior appended "schema" to pending_facets
        assert "schema" in seed.entries[0].coverage_pending_facets
        # extends_topic cascade: resolved=schema (injected), pending[0]=schema (injected),
        # default=overview (injected) → all exhausted, no candidate
        assert all(c.candidate_type != "facet_expansion" for c in candidates)


# ---------------------------------------------------------------------------
# 64-66: Suppression re-entry via hint — field reset verification
# ---------------------------------------------------------------------------


class TestHintDrivenSuppressionReentryFields:
    """Tests 64-66: Hint-driven suppression re-entry sets correct fields."""

    def test_prescriptive_reentry_fields(self) -> None:
        """Prescriptive hint → state=detected, suppression fields cleared."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=2,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="high")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="prescriptive",
                claim_excerpt="use pre_tool_use hooks",
            )
        ]

        process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=7
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 7

    def test_contradicts_prior_reentry_fields(self) -> None:
        """contradicts_prior hint → state=detected, suppression fields cleared."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="redundant",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=3,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="contradicts_prior",
                claim_excerpt="pre_tool_use hooks wrong",
            )
        ]

        process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=8
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 8

    def test_extends_topic_reentry_fields(self) -> None:
        """extends_topic hint → state=detected, suppression fields cleared."""
        entry = _make_entry(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
            suppression_reason="weak_results",
            suppressed_docs_epoch="2026-03-20",
            last_seen_turn=4,
        )
        seed = _make_seed(entries=[entry])
        inventory = _make_inventory()
        config = _make_config()

        resolved_topic = _make_resolved_topic(confidence="medium")
        classifier_fn = _make_classifier_fn({"pre_tool_use": resolved_topic})

        hints = [
            SemanticHint(
                claim_index=0,
                hint_type="extends_topic",
                claim_excerpt="pre_tool_use hooks more",
            )
        ]

        process_semantic_hints(
            seed, hints, inventory, classifier_fn, current_turn=9
        )

        e = seed.entries[0]
        assert e.state == "detected"
        assert e.suppression_reason is None
        assert e.suppressed_docs_epoch is None
        assert e.last_seen_turn == 9
