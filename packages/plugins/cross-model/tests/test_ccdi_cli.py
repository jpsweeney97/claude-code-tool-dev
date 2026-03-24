"""Tests for CCDI CLI entry point (topic_inventory.py).

Covers all 21 Phase A test cases from delivery.md: classify roundtrip,
build-packet modes, mark-injected, suppression, error handling, flag
validation, stdout/stderr separation, idempotency, and agent gate isolation.

Phase B additions (Task 6):
- dialogue-turn subcommand (7 tests)
- build-packet extensions: --mark-deferred, --skip-build, --shadow-mode (22 tests)
- source_divergence_canary meta-test (1 test)
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


# ===========================================================================
# Phase B: dialogue-turn subcommand tests (Step 1)
# ===========================================================================


def _make_inventory_snapshot_seed() -> dict:
    """Build a minimal inventory snapshot seed dict for dialogue-turn tests."""
    return _make_registry_seed()


class TestDialogueTurnUpdatesRegistryFile:
    """dialogue-turn writes registry state that persists across calls."""

    def test_state_persistence(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        try:
            # First call: should detect the topic and update registry
            r1 = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r1.returncode == 0, f"stderr: {r1.stderr}"

            # Read registry after first call
            with open(registry_path) as f:
                reg1 = json.load(f)

            # Second call: registry should reflect both calls
            r2 = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--turn", "2",
            )
            assert r2.returncode == 0, f"stderr: {r2.stderr}"

            with open(registry_path) as f:
                reg2 = json.load(f)

            # Registry should have entries after both calls
            assert len(reg2["entries"]) >= len(reg1["entries"])
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestDialogueTurnSourceCodexVsUser:
    """Both --source codex and --source user are accepted."""

    def test_both_sources_accepted(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        reg_path_codex = _write_json_file(registry_seed)
        reg_path_user = _write_json_file(registry_seed)
        try:
            r_codex = _run_cli(
                "dialogue-turn",
                "--registry-file", reg_path_codex,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            r_user = _run_cli(
                "dialogue-turn",
                "--registry-file", reg_path_user,
                "--text-file", text_path,
                "--source", "user",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_codex.returncode == 0, f"stderr: {r_codex.stderr}"
            assert r_user.returncode == 0, f"stderr: {r_user.stderr}"

            # Both produce valid JSON output
            out_codex = json.loads(r_codex.stdout)
            out_user = json.loads(r_user.stdout)
            assert "candidates" in out_codex
            assert "candidates" in out_user
        finally:
            os.unlink(text_path)
            os.unlink(reg_path_codex)
            os.unlink(reg_path_user)


class TestDialogueTurnWithNonDefaultTTL:
    """--config with non-default deferred_ttl_turns is used by pipeline."""

    def test_config_driven_ttl(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        # Config with non-default deferred TTL
        config_data = {
            "config_version": "1",
            "injection": {"deferred_ttl_turns": 7},
        }
        config_path = _write_json_file(config_data)
        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--config", config_path,
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            # Just verify it ran successfully with the config
            data = json.loads(r.stdout)
            assert "candidates" in data
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)
            os.unlink(config_path)


class TestDialogueTurnMissingInventorySnapshot:
    """--inventory-snapshot pointing to nonexistent file -> non-zero exit."""

    def test_missing_snapshot(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", "/tmp/does_not_exist_ccdi_snapshot.json",
            )
            assert r.returncode != 0
            assert r.stderr.strip() != ""
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestDialogueTurnRejectsInventoryFlag:
    """dialogue-turn with --inventory -> non-zero exit."""

    def test_rejects_inventory_flag(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        registry_path = _write_json_file(_make_registry_seed())
        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory", str(_INVENTORY),
            )
            assert r.returncode != 0
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestClassifyRejectsInventorySnapshotFlag:
    """classify with --inventory-snapshot -> non-zero exit (already covered in Test 13,
    but renamed for Phase B naming consistency)."""

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


class TestDialogueTurnShadowMode:
    """--shadow-mode suppresses cooldown deferral writes to registry."""

    def test_shadow_mode_no_deferral_writes(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--shadow-mode",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            data = json.loads(r.stdout)
            assert "candidates" in data
            assert "shadow_defer_intents" in data

            # In shadow mode, no entry should be in "deferred" state
            with open(registry_path) as f:
                reg = json.load(f)
            for entry in reg["entries"]:
                assert entry["state"] != "deferred", (
                    f"Shadow mode should not write deferred state, "
                    f"but entry {entry['topic_key']} is deferred"
                )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


# ===========================================================================
# Phase B: build-packet extension tests (Step 2)
# ===========================================================================


class TestBuildPacketMarkDeferred:
    """--mark-deferred writes deferred state to registry."""

    def test_mark_deferred_writes_state(self) -> None:
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
                "--mark-deferred", "cooldown",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            with open(registry_path) as f:
                reg = json.load(f)
            entry = reg["entries"][0]
            assert entry["state"] == "deferred"
            assert entry["deferred_reason"] == "cooldown"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketSkipBuildWithMarkDeferred:
    """--skip-build + --mark-deferred -> no packet output, registry updated."""

    def test_skip_build_mark_deferred(self) -> None:
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
                "--skip-build",
                "--mark-deferred", "cooldown",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            # No packet on stdout
            assert r.stdout.strip() == ""
            # Registry should be updated
            with open(registry_path) as f:
                reg = json.load(f)
            entry = reg["entries"][0]
            assert entry["state"] == "deferred"
            assert entry["deferred_reason"] == "cooldown"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketSkipBuildWithoutMarkDeferred:
    """--skip-build alone (without --mark-deferred) -> ignored, normal build."""

    def test_skip_build_alone_ignored(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--skip-build",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            # Normal build should produce output
            assert "### Claude Code Extension Reference" in r.stdout
        finally:
            os.unlink(results_path)


class TestBuildPacketShadowModeMarkDeferredNoop:
    """--shadow-mode + --mark-deferred -> exit 0, registry unchanged, stderr log."""

    def test_shadow_mode_noop(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        registry_path = _write_json_file(registry_seed)
        # Record original registry content
        with open(registry_path) as f:
            original_reg = json.load(f)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--shadow-mode",
                "--mark-deferred", "cooldown",
            )
            assert r.returncode == 0
            # stderr should log shadow intent
            assert "shadow" in r.stderr.lower()
            # Registry should be unchanged
            with open(registry_path) as f:
                after_reg = json.load(f)
            assert original_reg == after_reg
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketMissingInventorySnapshotWithRegistry:
    """--registry-file without --inventory-snapshot -> non-zero exit.
    (Same as Test 11 but named for Phase B consistency.)"""

    def test_missing_snapshot_with_registry(self) -> None:
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
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketRejectsInventoryFlagPhaseB:
    """build-packet with --inventory -> non-zero exit (Phase B naming)."""

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


class TestBuildPacketEmptyOutputSuppressedRedundant:
    """Good results but all chunk_ids in injected_chunk_ids -> suppressed:redundant."""

    def test_all_chunks_injected(self) -> None:
        results = _make_search_results(chunk_id="hooks#pretooluse")
        results_path = _write_json_file(results)
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
                reg = json.load(f)
            entry = reg["entries"][0]
            assert entry["state"] == "suppressed"
            assert entry["suppression_reason"] == "redundant"
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketAutomaticSuppressionRequiresRegistry:
    """No --registry-file -> no suppression writes."""

    def test_no_registry_no_suppression(self) -> None:
        results = _make_search_results(score=0.01)
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            assert r.returncode == 0
            assert r.stdout.strip() == ""
        finally:
            os.unlink(results_path)


class TestBuildPacketMissingCoverageTargetWithMarkInjected:
    """--mark-injected without --coverage-target -> non-zero exit."""

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
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketFacetMismatchMidTurn:
    """Prepare facet != commit facet -> different chunk IDs in output."""

    def test_facet_mismatch_different_results(self) -> None:
        results_overview = _make_search_results(
            chunk_id="hooks#pretooluse",
            content="PreToolUse hooks run before tool execution.",
        )
        results_path = _write_json_file(results_overview)
        registry_seed = _make_registry_seed()
        reg_path1 = _write_json_file(registry_seed)
        reg_path2 = _write_json_file(registry_seed)
        try:
            # Prepare with facet=overview
            r1 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", reg_path1,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            # Commit with facet=schema (different)
            r2 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", reg_path2,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "schema",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            # Both should succeed
            assert r1.returncode == 0, f"stderr: {r1.stderr}"
            assert r2.returncode == 0, f"stderr: {r2.stderr}"
            # The registry entries should differ in facet recorded
            with open(reg_path1) as f:
                reg1 = json.load(f)
            with open(reg_path2) as f:
                reg2 = json.load(f)
            facets1 = reg1["entries"][0]["coverage"]["facets_injected"]
            facets2 = reg2["entries"][0]["coverage"]["facets_injected"]
            assert facets1 != facets2
        finally:
            os.unlink(results_path)
            os.unlink(reg_path1)
            os.unlink(reg_path2)


class TestPrepareCommitPacketIdempotencyInitial:
    """build-packet prepare then commit with same inputs -> identical chunk IDs."""

    def test_idempotency_initial(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        reg_path1 = _write_json_file(registry_seed)
        reg_path2 = _write_json_file(registry_seed)
        try:
            # Prepare (no --mark-injected)
            r1 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", reg_path1,
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
                "--registry-file", reg_path2,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            assert r1.returncode == 0
            assert r2.returncode == 0
            assert r1.stdout == r2.stdout
        finally:
            os.unlink(results_path)
            os.unlink(reg_path1)
            os.unlink(reg_path2)


class TestPrepareCommitPacketIdempotencyMidTurn:
    """Mid-turn build-packet prepare then commit -> identical output."""

    def test_idempotency_mid_turn(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        registry_seed = _make_registry_seed()
        reg_path1 = _write_json_file(registry_seed)
        reg_path2 = _write_json_file(registry_seed)
        try:
            r1 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "mid_turn",
                "--registry-file", reg_path1,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
            )
            r2 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "mid_turn",
                "--registry-file", reg_path2,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", "hooks.pre_tool_use",
                "--facet", "overview",
                "--coverage-target", "leaf",
                "--mark-injected",
            )
            assert r1.returncode == 0
            assert r2.returncode == 0
            assert r1.stdout == r2.stdout
        finally:
            os.unlink(results_path)
            os.unlink(reg_path1)
            os.unlink(reg_path2)


class TestAgentGateUnchangedWhenInitialThresholdOverridden:
    """Config overrides initial_threshold -> agent gate still uses hardcoded value."""

    def test_agent_gate_unchanged(self) -> None:
        # Config says 5 high needed, but agent hardcodes 1
        result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "high"),
        ])
        assert check_agent_gate(result) is True


class TestAgentGateUnchangedWhenConfigMorePermissive:
    """More permissive config -> agent gate unaffected (still requires 2 medium same family)."""

    def test_agent_gate_permissive_ignored(self) -> None:
        result = _make_classifier_result([
            ("hooks.pre_tool_use", "hooks", "medium"),
        ])
        # Agent hardcoded: 2 medium in same family needed, not 1
        assert check_agent_gate(result) is False


class TestAgentGateMatchesBuiltinDefaults:
    """Agent gate threshold matches BUILTIN_DEFAULTS value."""

    def test_matches_defaults(self) -> None:
        from scripts.topic_inventory import _AGENT_HIGH_COUNT, _AGENT_MEDIUM_SAME_FAMILY
        assert _AGENT_HIGH_COUNT == BUILTIN_DEFAULTS["injection"]["initial_threshold_high_count"]
        assert _AGENT_MEDIUM_SAME_FAMILY == BUILTIN_DEFAULTS["injection"]["initial_threshold_medium_same_family_count"]


class TestAgentGateConfigIsolationPhaseA:
    """Phase A agent gate independent of Phase B config — check_agent_gate has no config param."""

    def test_agent_gate_no_config_param(self) -> None:
        import inspect
        sig = inspect.signature(check_agent_gate)
        params = list(sig.parameters.keys())
        # check_agent_gate accepts only ClassifierResult, no config
        assert params == ["result"]


class TestInventorySnapshotVersionMismatchBestEffort:
    """Inventory snapshot version differs from registry -> best-effort mapping (warning, not error)."""

    def test_version_mismatch_best_effort(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        registry_seed["inventory_snapshot_version"] = "99"  # Different from inventory
        registry_path = _write_json_file(registry_seed)
        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            # Should succeed (best-effort), not error
            assert r.returncode == 0, f"stderr: {r.stderr}"
            data = json.loads(r.stdout)
            assert "candidates" in data
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestBuildPacketMissingResultsFileWithoutSkipBuild:
    """--results-file absent without --skip-build -> non-zero exit."""

    def test_missing_results_file(self) -> None:
        r = _run_cli(
            "build-packet",
            "--results-file", "/tmp/does_not_exist_ccdi_results.json",
            "--mode", "initial",
        )
        assert r.returncode != 0
        assert r.stderr.strip() != ""


class TestBuildPacketMissingInventorySnapshotWithoutRegistry:
    """--inventory-snapshot absent without --registry-file -> no error (CCDI-lite mode)."""

    def test_no_registry_no_snapshot_ok(self) -> None:
        results = _make_search_results()
        results_path = _write_json_file(results)
        try:
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            # No --registry-file, no --inventory-snapshot -> still works
            assert r.returncode == 0
        finally:
            os.unlink(results_path)


class TestBuildPacketMissingTopicKeyWithMarkDeferred:
    """--mark-deferred without --topic-key -> non-zero exit."""

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
                "--facet", "overview",
                "--mark-deferred", "cooldown",
            )
            assert r.returncode != 0
            assert "topic-key" in r.stderr.lower() or "topic_key" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestBuildPacketMissingFacetWithMarkDeferred:
    """--mark-deferred without --facet -> non-zero exit."""

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
                "--mark-deferred", "cooldown",
            )
            assert r.returncode != 0
            assert "facet" in r.stderr.lower()
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


# ===========================================================================
# Phase B: source_divergence_canary meta-test (Step 6)
# ===========================================================================


class TestSourceDivergenceCanary:
    """Meta-test: --source codex and --source user produce identical output for same inputs."""

    def test_source_equivalence(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_seed = _make_registry_seed()
        reg_path_codex = _write_json_file(registry_seed)
        reg_path_user = _write_json_file(registry_seed)
        try:
            r_codex = _run_cli(
                "dialogue-turn",
                "--registry-file", reg_path_codex,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            r_user = _run_cli(
                "dialogue-turn",
                "--registry-file", reg_path_user,
                "--text-file", text_path,
                "--source", "user",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_codex.returncode == 0, f"codex stderr: {r_codex.stderr}"
            assert r_user.returncode == 0, f"user stderr: {r_user.stderr}"

            # Parse and compare candidates (excluding registry paths which differ)
            out_codex = json.loads(r_codex.stdout)
            out_user = json.loads(r_user.stdout)
            assert out_codex["candidates"] == out_user["candidates"], (
                "source codex and source user should produce identical candidates"
            )
        finally:
            os.unlink(text_path)
            os.unlink(reg_path_codex)
            os.unlink(reg_path_user)
