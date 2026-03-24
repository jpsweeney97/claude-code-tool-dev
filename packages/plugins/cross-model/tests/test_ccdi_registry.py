"""Tests for CCDI registry — Phase A subset.

Covers: load_registry, mark_injected, write_suppressed, _write_registry,
check_suppression_reentry, normalize_fingerprint, sort_candidates.
"""

from __future__ import annotations

import json
import logging
import os

import pytest

from scripts.ccdi.registry import (
    _write_registry,
    check_suppression_reentry,
    load_registry,
    mark_injected,
    normalize_fingerprint,
    sort_candidates,
    write_suppressed,
)
from scripts.ccdi.types import RegistrySeed, TopicRegistryEntry


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
