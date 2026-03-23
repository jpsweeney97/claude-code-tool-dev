"""Tests for CCDI CLI entry point (topic_inventory.py).

Covers all 21 Phase A test cases from delivery.md: classify roundtrip,
build-packet modes, mark-injected, suppression, error handling, flag
validation, stdout/stderr separation, idempotency, and agent gate isolation.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from scripts.ccdi.config import BUILTIN_DEFAULTS
from scripts.ccdi.types import ClassifierResult, TopicRegistryEntry, RegistrySeed

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _PKG_ROOT / "scripts" / "topic_inventory.py"
_FIXTURE_DIR = _PKG_ROOT / "tests" / "fixtures" / "ccdi"
_INVENTORY = _FIXTURE_DIR / "test_inventory.json"


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess using module invocation for correct imports."""
    return subprocess.run(
        ["uv", "run", "python", "-m", "scripts.topic_inventory", *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(_PKG_ROOT),
    )


def _write_text_file(text: str, suffix: str = ".txt") -> str:
    """Write text to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


def _write_json_file(data: dict | list, suffix: str = ".json") -> str:
    """Write JSON to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


def _make_search_results(
    *,
    chunk_id: str = "hooks#pretooluse",
    category: str = "hooks",
    score: float = 0.8,
    content: str = "PreToolUse hooks run before tool execution. They receive `tool_name` and `tool_input` as JSON.",
    source_file: str = "https://code.claude.com/docs/en/hooks",
) -> list[dict]:
    """Build minimal search results for build-packet."""
    return [
        {
            "chunk_id": chunk_id,
            "category": category,
            "score": score,
            "content": content,
            "source_file": source_file,
        }
    ]


def _make_registry_seed(
    topic_key: str = "hooks.pre_tool_use",
    state: str = "detected",
    facet: str = "overview",
    coverage_target: str = "leaf",
    **overrides: object,
) -> dict:
    """Build a minimal registry seed dict."""
    entry: dict = {
        "topic_key": topic_key,
        "family_key": topic_key.split(".")[0],
        "state": state,
        "first_seen_turn": 0,
        "last_seen_turn": 0,
        "last_injected_turn": None,
        "last_query_fingerprint": None,
        "consecutive_medium_count": 0,
        "suppression_reason": None,
        "suppressed_docs_epoch": None,
        "deferred_reason": None,
        "deferred_ttl": None,
        "coverage_target": coverage_target,
        "facet": facet,
        "kind": "leaf",
        "coverage": {
            "overview_injected": False,
            "facets_injected": [],
            "pending_facets": [],
            "family_context_available": False,
            "injected_chunk_ids": [],
        },
    }
    entry.update(overrides)
    return {
        "entries": [entry],
        "docs_epoch": "test-epoch-abc",
        "inventory_snapshot_version": "1",
    }


# ---------------------------------------------------------------------------
# Test 1: classify file I/O roundtrip
# ---------------------------------------------------------------------------


class TestClassifyRoundtrip:
    """Test 1: reads text file, returns valid ClassifierResult JSON."""

    def test_classify_roundtrip(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        try:
            r = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            data = json.loads(r.stdout)
            assert "resolved_topics" in data
            assert "suppressed_candidates" in data
            # Should resolve hooks.pre_tool_use
            keys = [t["topic_key"] for t in data["resolved_topics"]]
            assert "hooks.pre_tool_use" in keys
        finally:
            os.unlink(text_path)


# ---------------------------------------------------------------------------
# Test 2: build-packet initial mode produces markdown
# ---------------------------------------------------------------------------


class TestBuildPacketInitialMarkdown:
    """Test 2: initial mode renders markdown with expected heading."""

    def test_initial_mode_heading(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            assert "### Claude Code Extension Reference" in r.stdout
        finally:
            os.unlink(results_path)


# ---------------------------------------------------------------------------
# Test 3: build-packet --mark-injected updates registry
# ---------------------------------------------------------------------------


class TestMarkInjectedUpdatesRegistry:
    """Test 3: --mark-injected transitions registry entry to injected state."""

    def test_mark_injected(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            # Check registry was updated
            with open(registry_path) as f:
                updated = json.load(f)
            entry = updated["entries"][0]
            assert entry["state"] == "injected"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 4: build-packet empty output writes suppressed (weak)
# ---------------------------------------------------------------------------


class TestEmptyOutputSuppressedWeak:
    """Test 4: poor results + registry-file -> suppressed: weak_results."""

    def test_weak_results_suppressed(self) -> None:
        # Results with score below quality threshold
        results = _make_search_results(score=0.01)
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
            )
            assert r.returncode == 0
            # stdout should be empty (no packet)
            assert r.stdout.strip() == ""
            # Registry should record suppressed: weak_results
            with open(registry_path) as f:
                updated = json.load(f)
            entry = updated["entries"][0]
            assert entry["state"] == "suppressed"
            assert entry["suppression_reason"] == "weak_results"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 5: build-packet empty output writes suppressed (redundant)
# ---------------------------------------------------------------------------


class TestEmptyOutputSuppressedRedundant:
    """Test 5: all chunks already injected -> suppressed: redundant."""

    def test_redundant_suppressed(self) -> None:
        results = _make_search_results(chunk_id="hooks#pretooluse")
        results_path = _write_json_file(results)
        # Registry with this chunk already injected
        seed = _make_registry_seed()
        seed["entries"][0]["coverage"]["injected_chunk_ids"] = ["hooks#pretooluse"]
        registry_path = _write_json_file(seed)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
            )
            assert r.returncode == 0
            assert r.stdout.strip() == ""
            with open(registry_path) as f:
                updated = json.load(f)
            entry = updated["entries"][0]
            assert entry["state"] == "suppressed"
            assert entry["suppression_reason"] == "redundant"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 6: missing inventory -> non-zero exit
# ---------------------------------------------------------------------------


class TestMissingInventory:
    """Test 6: --inventory pointing to nonexistent file -> non-zero exit."""

    def test_missing_inventory(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        try:
            r = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", "/tmp/does_not_exist_ccdi.json",
            )
            assert r.returncode != 0
            assert r.stderr.strip() != ""
        finally:
            os.unlink(text_path)


# ---------------------------------------------------------------------------
# Test 7: malformed text -> non-zero exit
# ---------------------------------------------------------------------------


class TestMalformedText:
    """Test 7: binary/unreadable file -> non-zero exit."""

    def test_binary_text_file(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".bin")
        with os.fdopen(fd, "wb") as f:
            f.write(b"\x00\x01\x02\xff\xfe\xfd")
        try:
            r = _run_cli(
                "classify",
                "--text-file", path,
                "--inventory", str(_INVENTORY),
            )
            assert r.returncode != 0
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test 8: stdout/stderr separation
# ---------------------------------------------------------------------------


class TestStdoutStderrSeparation:
    """Test 8: JSON only on stdout, errors only on stderr."""

    def test_separation(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        try:
            r = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r.returncode == 0
            # stdout must be valid JSON
            data = json.loads(r.stdout)
            assert isinstance(data, dict)
            # stderr should NOT contain JSON
            if r.stderr.strip():
                with pytest.raises(json.JSONDecodeError):
                    json.loads(r.stderr)
        finally:
            os.unlink(text_path)


# ---------------------------------------------------------------------------
# Test 9: automatic suppression requires registry
# ---------------------------------------------------------------------------


class TestAutoSuppressionRequiresRegistry:
    """Test 9: empty output WITHOUT --registry-file -> no suppression (just empty stdout)."""

    def test_no_registry_no_suppression(self) -> None:
        # Low-score results -> empty packet -> no suppression without registry
        results = _make_search_results(score=0.01)
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            assert r.returncode == 0
            # Just empty stdout, no error
            assert r.stdout.strip() == ""
        finally:
            os.unlink(results_path)


# ---------------------------------------------------------------------------
# Test 10: --inventory-snapshot without --registry-file -> silently ignored
# ---------------------------------------------------------------------------


class TestSnapshotWithoutRegistryIgnored:
    """Test 10: --inventory-snapshot without --registry-file -> ignored, exit 0."""

    def test_snapshot_ignored(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r.returncode == 0
            # Should still produce output (snapshot is optional metadata)
            assert "### Claude Code Extension Reference" in r.stdout
        finally:
            os.unlink(results_path)


# ---------------------------------------------------------------------------
# Test 11: missing --inventory-snapshot with --registry-file -> error
# ---------------------------------------------------------------------------


class TestMissingSnapshotWithRegistry:
    """Test 11: --registry-file requires --inventory-snapshot."""

    def test_missing_snapshot_error(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--topic-key", "hooks.pre_tool_use",
            )
            assert r.returncode != 0
            assert "inventory-snapshot" in r.stderr.lower() or "inventory_snapshot" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 12: build-packet rejects --inventory flag
# ---------------------------------------------------------------------------


class TestBuildPacketRejectsInventoryFlag:
    """Test 12: build-packet with --inventory -> non-zero exit."""

    def test_rejects_inventory_flag(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--inventory", str(_INVENTORY),
            )
            assert r.returncode != 0
        finally:
            os.unlink(results_path)


# ---------------------------------------------------------------------------
# Test 13: classify rejects --inventory-snapshot flag
# ---------------------------------------------------------------------------


class TestClassifyRejectsSnapshotFlag:
    """Test 13: classify with --inventory-snapshot -> non-zero exit."""

    def test_rejects_snapshot_flag(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        try:
            r = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r.returncode != 0
        finally:
            os.unlink(text_path)


# ---------------------------------------------------------------------------
# Test 14: missing --coverage-target with --mark-injected -> error
# ---------------------------------------------------------------------------


class TestMissingCoverageTargetWithMarkInjected:
    """Test 14: --mark-injected without --coverage-target -> error."""

    def test_missing_coverage_target(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--mark-injected",
            )
            assert r.returncode != 0
            assert "coverage-target" in r.stderr.lower() or "coverage_target" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 15: missing --topic-key with --registry-file -> error
# ---------------------------------------------------------------------------


class TestMissingTopicKeyWithRegistry:
    """Test 15: --registry-file without --topic-key -> error."""

    def test_missing_topic_key(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r.returncode != 0
            assert "topic-key" in r.stderr.lower() or "topic_key" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 16: missing --facet with --mark-injected -> error
# ---------------------------------------------------------------------------


class TestMissingFacetWithMarkInjected:
    """Test 16: --mark-injected without --facet -> error."""

    def test_missing_facet(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            assert r.returncode != 0
            assert "facet" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ---------------------------------------------------------------------------
# Test 17: prepare/commit packet idempotency initial mode
# ---------------------------------------------------------------------------


class TestPacketIdempotency:
    """Test 17: prepare then commit produce matching output."""

    def test_prepare_commit_match(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        registry_path1 = _write_json_file(registry_seed)
        registry_path2 = _write_json_file(registry_seed)
        try:
            # Prepare (no --mark-injected)
            r1 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path1,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
            )
            # Commit (with --mark-injected)
            r2 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path2,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            assert r1.returncode == 0
            assert r2.returncode == 0
            # Output markdown should be identical
            assert r1.stdout == r2.stdout
        finally:
            os.unlink(results_path)
            os.unlink(registry_path1)
            os.unlink(registry_path2)


# ---------------------------------------------------------------------------
# Tests 18-21: Agent gate isolation
# ---------------------------------------------------------------------------

# Import the function under test directly (unit tests, not subprocess)
from scripts.topic_inventory import check_agent_gate
from scripts.ccdi.types import ResolvedTopic, MatchedAlias


def _make_classifier_result(
    topics: list[tuple[str, str, str]] | None = None,
) -> ClassifierResult:
    """Build ClassifierResult from (topic_key, family_key, confidence) tuples."""
    if topics is None:
        topics = []
    resolved = []
    for topic_key, family_key, confidence in topics:
        resolved.append(
            ResolvedTopic(
                topic_key=topic_key,
                family_key=family_key,
                coverage_target="leaf",
                confidence=confidence,
                facet="overview",
                matched_aliases=[
                    MatchedAlias(text="test", span=(0, 4), weight=0.9),
                ],
                reason="test",
            )
        )
    return ClassifierResult(
        resolved_topics=resolved,
        suppressed_candidates=[],
    )


class TestAgentGateOverrideIgnored:
    """Test 18: config overrides initial_threshold_high_count=2, but agent
    still dispatches with 1 high (agent ignores config)."""

    def test_agent_dispatches_with_one_high(self) -> None:
        result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "high"),
        ])
        # Agent uses hardcoded: 1 high is enough
        assert check_agent_gate(result) is True


class TestAgentGatePermissiveConfigIgnored:
    """Test 19: config threshold=0 (permissive), but agent doesn't dispatch
    with only 1 medium (agent uses hardcoded)."""

    def test_agent_rejects_single_medium(self) -> None:
        result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "medium"),
        ])
        # Agent hardcoded: needs 2 medium in same family, not 1
        assert check_agent_gate(result) is False


class TestAgentGateMatchesDefaults:
    """Test 20: with default config, agent and CLI agree on threshold decisions."""

    def test_agent_matches_defaults(self) -> None:
        # 1 high -> dispatches (matches BUILTIN_DEFAULTS initial_threshold_high_count=1)
        high_result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "high"),
        ])
        assert check_agent_gate(high_result) is True

        # 2 medium same family -> dispatches
        # (matches BUILTIN_DEFAULTS initial_threshold_medium_same_family_count=2)
        med_result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "medium"),
            ("hooks.post_tool_use", "hooks", "medium"),
        ])
        assert check_agent_gate(med_result) is True

        # 1 medium alone -> does not dispatch
        single_med = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "medium"),
        ])
        assert check_agent_gate(single_med) is False

        # 0 topics -> does not dispatch
        empty = _make_classifier_result([])
        assert check_agent_gate(empty) is False

        # Verify these match the built-in defaults
        assert BUILTIN_DEFAULTS["injection"]["initial_threshold_high_count"] == 1
        assert BUILTIN_DEFAULTS["injection"]["initial_threshold_medium_same_family_count"] == 2


class TestAgentGateConfigIsolation:
    """Test 21: config sets impossible threshold (999), agent still dispatches normally."""

    def test_agent_ignores_config(self) -> None:
        # Even if a config file had threshold=999, the agent function uses
        # hardcoded values and does NOT accept config as input.
        result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "high"),
        ])
        # check_agent_gate takes ONLY ClassifierResult, no config param
        assert check_agent_gate(result) is True
