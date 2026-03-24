"""Layer 2b tests: agent-sequence integration via CLI subprocess.

These tests verify the CCDI CLI tools work correctly when called in the
sequence the codex-dialogue agent is instructed to follow.  They do NOT
invoke the agent itself (Claude Code has no headless agent invocation).
Instead they simulate the documented workflow:

  classify -> dialogue-turn -> build-packet (prepare) -> build-packet (commit)

and assert each step produces the outputs the next step needs.

Section 1 — Feasibility gate (mechanism works at all)
Section 2 — Baseline behavioral tests (3 workflow patterns)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_DIR = _PKG_ROOT / "tests" / "fixtures" / "ccdi"
_INVENTORY = _FIXTURE_DIR / "test_inventory.json"


# ---------------------------------------------------------------------------
# Helpers (same pattern as test_ccdi_cli.py)
# ---------------------------------------------------------------------------


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CCDI CLI as a subprocess using module invocation."""
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


def _make_empty_registry() -> dict:
    """Build an empty registry seed (no pre-existing entries).

    Use this when dialogue-turn needs to treat classified topics as
    materially new — dialogue-turn only emits candidates for topics that
    are *newly created* in the current call or transitioned from deferred.
    """
    return {
        "entries": [],
        "docs_epoch": "test-epoch-abc",
        "inventory_snapshot_version": "1",
    }


def _make_registry_seed(
    topic_key: str = "hooks.pre_tool_use",
    state: str = "detected",
    facet: str = "overview",
    coverage_target: str = "leaf",
) -> dict:
    """Build a registry seed with one pre-existing entry."""
    return {
        "entries": [
            {
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
        ],
        "docs_epoch": "test-epoch-abc",
        "inventory_snapshot_version": "1",
    }


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


# ===========================================================================
# Section 1: Feasibility gate
# ===========================================================================


class TestLayer2bMechanismSelection:
    """Assert the subprocess test mechanism works: can invoke CLI and get
    expected exit codes for both success and failure paths."""

    def test_help_exits_zero(self) -> None:
        r = _run_cli("--help")
        assert r.returncode == 0, f"--help failed: {r.stderr}"
        assert "classify" in r.stdout
        assert "build-packet" in r.stdout
        assert "dialogue-turn" in r.stdout

    def test_bad_subcommand_exits_nonzero(self) -> None:
        r = _run_cli("nonexistent-subcommand")
        assert r.returncode != 0


class TestShimIdentityCheck:
    """CLI invocation via `uv run python -m scripts.topic_inventory` produces
    expected --help output identifying all three subcommands."""

    def test_help_contains_subcommands(self) -> None:
        r = _run_cli("--help")
        assert r.returncode == 0, f"stderr: {r.stderr}"
        # Verify the three subcommands the agent uses are present
        assert "classify" in r.stdout
        assert "build-packet" in r.stdout
        assert "dialogue-turn" in r.stdout


class TestShimDoesNotInterceptNonCcdiPython3:
    """Non-CCDI Python invocation doesn't interact with CCDI tooling."""

    def test_plain_python_print(self) -> None:
        r = subprocess.run(
            ["uv", "run", "python", "-c", "print(42)"],
            capture_output=True,
            text=True,
            cwd=str(_PKG_ROOT),
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "42"
        # No CCDI-related output
        assert "topic_inventory" not in r.stdout
        assert "topic_inventory" not in r.stderr


class TestInterceptionCompleteness3Invocations:
    """3 sequential CLI invocations all succeed and produce expected outputs."""

    def test_three_sequential_invocations(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_path = _write_json_file(_make_registry_seed())
        results_path = _write_json_file(_make_search_results())
        try:
            # Invocation 1: classify
            r1 = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r1.returncode == 0, f"classify stderr: {r1.stderr}"
            classify_out = json.loads(r1.stdout)
            assert "resolved_topics" in classify_out

            # Invocation 2: dialogue-turn
            r2 = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r2.returncode == 0, f"dialogue-turn stderr: {r2.stderr}"
            dt_out = json.loads(r2.stdout)
            assert "candidates" in dt_out

            # Invocation 3: build-packet
            r3 = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            assert r3.returncode == 0, f"build-packet stderr: {r3.stderr}"
            assert "### Claude Code Extension Reference" in r3.stdout
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)
            os.unlink(results_path)


# ===========================================================================
# Section 2: Baseline behavioral tests
# ===========================================================================


class TestAgentInvokesClassifyBeforeDialogueTurn:
    """Documented workflow: classify must run before dialogue-turn because
    classify output confirms topic detection that dialogue-turn then
    schedules for injection.

    This test verifies the data-flow contract: classify returns
    resolved_topics, and dialogue-turn (given the same text and inventory)
    produces candidates for those same topics.
    """

    def test_classify_output_feeds_dialogue_turn(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        # Empty registry so dialogue-turn treats classified topics as new
        registry_path = _write_json_file(_make_empty_registry())
        try:
            # Step 1: classify (agent does this first)
            r_classify = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r_classify.returncode == 0, f"classify stderr: {r_classify.stderr}"
            classify_data = json.loads(r_classify.stdout)
            classified_keys = {
                t["topic_key"] for t in classify_data["resolved_topics"]
            }
            assert len(classified_keys) > 0, "classify should detect at least one topic"

            # Step 2: dialogue-turn (agent does this second)
            r_dt = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_dt.returncode == 0, f"dialogue-turn stderr: {r_dt.stderr}"
            dt_data = json.loads(r_dt.stdout)
            candidate_keys = {c["topic_key"] for c in dt_data["candidates"]}

            # The dialogue-turn candidates should be a subset of what
            # classify detected (dialogue-turn may filter some out via
            # scheduling logic, but should not introduce new topics).
            assert candidate_keys <= classified_keys, (
                f"dialogue-turn candidates {candidate_keys} should be a subset of "
                f"classified topics {classified_keys}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestAgentSkipsBuildPacketWhenNoCandidates:
    """When dialogue-turn returns 0 candidates, the agent skips build-packet
    entirely.  This test verifies the contract: text with no matching topics
    produces an empty candidates list, so only 2 CLI calls are needed
    (classify + dialogue-turn), not 3.
    """

    def test_no_candidates_means_no_build_packet(self) -> None:
        # Text that does not match any inventory topic
        text_path = _write_text_file(
            "What is the weather forecast for tomorrow in Paris?"
        )
        registry_path = _write_json_file(_make_empty_registry())
        try:
            # Step 1: classify
            r_classify = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r_classify.returncode == 0, f"classify stderr: {r_classify.stderr}"
            classify_data = json.loads(r_classify.stdout)

            # Step 2: dialogue-turn
            r_dt = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_dt.returncode == 0, f"dialogue-turn stderr: {r_dt.stderr}"
            dt_data = json.loads(r_dt.stdout)

            # With no matching topics, candidates should be empty
            assert dt_data["candidates"] == [], (
                f"Expected 0 candidates for off-topic text, got: {dt_data['candidates']}"
            )

            # The agent would check len(candidates) == 0 and skip build-packet.
            # No third CLI call needed.  We verify this by simply asserting
            # the data-flow condition that gates the third call.
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestAgentCallsMarkInjectedAfterCodexReply:
    """Full workflow: classify -> dialogue-turn -> build-packet (prepare) ->
    build-packet (commit with --mark-injected) -> verify registry shows
    injected state.

    This mirrors the agent's Step 6.5 sequence end-to-end.
    """

    def test_full_workflow_mark_injected(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        # Empty registry so dialogue-turn treats classified topics as new
        registry_path = _write_json_file(_make_empty_registry())
        results_path = _write_json_file(_make_search_results())
        try:
            # --- Step 1: classify ---
            r_classify = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r_classify.returncode == 0, f"classify stderr: {r_classify.stderr}"
            classify_data = json.loads(r_classify.stdout)
            assert len(classify_data["resolved_topics"]) > 0

            # --- Step 2: dialogue-turn ---
            r_dt = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_dt.returncode == 0, f"dialogue-turn stderr: {r_dt.stderr}"
            dt_data = json.loads(r_dt.stdout)
            assert len(dt_data["candidates"]) > 0, "Expected at least one candidate"

            # Use the first candidate's details for build-packet
            candidate = dt_data["candidates"][0]
            topic_key = candidate["topic_key"]
            facet = candidate["facet"]
            coverage_target = candidate["coverage_target"]

            # --- Step 3: build-packet prepare (agent previews output) ---
            r_prepare = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", topic_key,
                "--facet", facet,
                "--coverage-target", coverage_target,
            )
            assert r_prepare.returncode == 0, f"prepare stderr: {r_prepare.stderr}"
            packet_content = r_prepare.stdout
            assert len(packet_content.strip()) > 0, "Prepare should produce packet content"

            # Read registry after prepare — should NOT be marked injected yet
            with open(registry_path) as f:
                reg_after_prepare = json.load(f)
            entry = next(
                e for e in reg_after_prepare["entries"]
                if e["topic_key"] == topic_key
            )
            assert entry["state"] != "injected", (
                "Registry should NOT be injected after prepare (no --mark-injected)"
            )

            # --- Step 4: build-packet commit (after Codex reply sent) ---
            r_commit = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", topic_key,
                "--facet", facet,
                "--coverage-target", coverage_target,
                "--mark-injected",
            )
            assert r_commit.returncode == 0, f"commit stderr: {r_commit.stderr}"

            # Commit output should match prepare output (idempotency)
            assert r_commit.stdout == packet_content, (
                "Prepare and commit should produce identical packet content"
            )

            # --- Step 5: verify registry shows injected ---
            with open(registry_path) as f:
                reg_final = json.load(f)
            final_entry = next(
                e for e in reg_final["entries"]
                if e["topic_key"] == topic_key
            )
            assert final_entry["state"] == "injected", (
                f"Expected state 'injected', got '{final_entry['state']}'"
            )
            # Verify coverage tracking was updated
            assert facet in final_entry["coverage"]["facets_injected"], (
                f"Expected facet '{facet}' in facets_injected, "
                f"got: {final_entry['coverage']['facets_injected']}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)
            os.unlink(results_path)
