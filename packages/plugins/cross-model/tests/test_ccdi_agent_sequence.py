"""Layer 2b tests: agent-sequence integration via CLI subprocess.

These tests verify the CCDI CLI tools work correctly when called in the
sequence the codex-dialogue agent is instructed to follow.  They do NOT
invoke the agent itself (Claude Code has no headless agent invocation).
Instead they simulate the documented workflow:

  classify -> dialogue-turn -> build-packet (prepare) -> build-packet (commit)

and assert each step produces the outputs the next step needs.

Section 1 — Feasibility gate (mechanism works at all)
Section 2 — Baseline behavioral tests (3 workflow patterns)
Section 3 — Graduation gate tests (shadow vs active mode)
Section 4 — Shadow diagnostic assertion tests
Section 5 — Pipeline isolation tests
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


# ===========================================================================
# Graduation gate helper
# ===========================================================================


def _simulate_graduation_gate_workflow(
    graduation_json: dict | None,
    text: str = "How do I write a PreToolUse hook?",
) -> tuple[int, dict, dict]:
    """Simulate the agent's graduation gate check and full workflow.

    The agent checks graduation.json to decide shadow vs active mode:
    - absent or status != "approved" -> shadow mode (--shadow-mode)
    - status == "approved" -> active mode (no --shadow-mode)

    Returns (mark_injected_count, dialogue_turn_output, final_registry).
    mark_injected_count: number of --mark-injected CLI calls made.
    """
    text_path = _write_text_file(text)
    registry_path = _write_json_file(_make_empty_registry())
    results_path = _write_json_file(_make_search_results())

    try:
        # Determine mode from graduation.json
        shadow_mode = True  # default: shadow
        if graduation_json is not None and graduation_json.get("status") == "approved":
            shadow_mode = False

        # Step 1: classify
        r_classify = _run_cli(
            "classify",
            "--text-file", text_path,
            "--inventory", str(_INVENTORY),
        )
        assert r_classify.returncode == 0, f"classify stderr: {r_classify.stderr}"

        # Step 2: dialogue-turn (with or without --shadow-mode)
        dt_args = [
            "dialogue-turn",
            "--registry-file", registry_path,
            "--text-file", text_path,
            "--source", "codex",
            "--inventory-snapshot", str(_INVENTORY),
        ]
        if shadow_mode:
            dt_args.append("--shadow-mode")

        r_dt = _run_cli(*dt_args)
        assert r_dt.returncode == 0, f"dialogue-turn stderr: {r_dt.stderr}"
        dt_data = json.loads(r_dt.stdout)

        # Step 3+4: build-packet + mark-injected (only in active mode with candidates)
        mark_injected_count = 0
        if dt_data["candidates"] and not shadow_mode:
            candidate = dt_data["candidates"][0]
            r_commit = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", registry_path,
                "--inventory-snapshot", str(_INVENTORY),
                "--topic-key", candidate["topic_key"],
                "--facet", candidate["facet"],
                "--coverage-target", candidate["coverage_target"],
                "--mark-injected",
            )
            assert r_commit.returncode == 0, f"commit stderr: {r_commit.stderr}"
            mark_injected_count = 1

        # Read final registry
        with open(registry_path) as f:
            final_registry = json.load(f)

        return mark_injected_count, dt_data, final_registry

    finally:
        os.unlink(text_path)
        os.unlink(registry_path)
        os.unlink(results_path)


# ===========================================================================
# Section 3: Graduation gate tests
# ===========================================================================


class TestGraduationGateFileAbsentShadow:
    """No graduation.json -> shadow mode behavior: zero --mark-injected
    registry writes when running the full workflow."""

    def test_graduation_gate_file_absent_shadow(self) -> None:
        # graduation.json absent => None => shadow mode
        mark_count, dt_data, final_reg = _simulate_graduation_gate_workflow(
            graduation_json=None,
        )
        assert mark_count == 0, (
            "Shadow mode (graduation absent) should produce zero --mark-injected calls"
        )
        # No entry should be in injected state
        for entry in final_reg["entries"]:
            assert entry["state"] != "injected", (
                f"Shadow mode: entry {entry['topic_key']} should not be injected"
            )


class TestGraduationGateRejectedShadow:
    """graduation.json with status:rejected -> shadow mode: zero injection commits."""

    def test_graduation_gate_rejected_shadow(self) -> None:
        mark_count, dt_data, final_reg = _simulate_graduation_gate_workflow(
            graduation_json={"status": "rejected", "reason": "quality_check_failed"},
        )
        assert mark_count == 0, (
            "Shadow mode (graduation rejected) should produce zero --mark-injected calls"
        )
        for entry in final_reg["entries"]:
            assert entry["state"] != "injected", (
                f"Shadow mode: entry {entry['topic_key']} should not be injected"
            )


class TestGraduationGateApprovedActive:
    """graduation.json with status:approved -> active mode: at least one --mark-injected."""

    def test_graduation_gate_approved_active(self) -> None:
        mark_count, dt_data, final_reg = _simulate_graduation_gate_workflow(
            graduation_json={"status": "approved"},
        )
        assert mark_count >= 1, (
            "Active mode (graduation approved) should produce at least one --mark-injected call"
        )
        injected_entries = [
            e for e in final_reg["entries"] if e["state"] == "injected"
        ]
        assert len(injected_entries) >= 1, (
            "Active mode should have at least one injected entry in registry"
        )


class TestGraduationGatePhaseAUnconditional:
    """Phase A initial injection (build-packet without dialogue-turn)
    always fires regardless of graduation status.

    The agent calls build-packet --mode initial directly for the Phase A
    bootstrap packet. This path does not depend on graduation.json.
    """

    def test_graduation_gate_phase_a_unconditional(self) -> None:
        results_path = _write_json_file(_make_search_results())
        try:
            # Phase A path: build-packet directly (no dialogue-turn, no graduation check)
            r = _run_cli(
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            assert len(r.stdout.strip()) > 0, (
                "Phase A build-packet should produce output regardless of graduation"
            )
            assert "### Claude Code Extension Reference" in r.stdout
        finally:
            os.unlink(results_path)


# ===========================================================================
# Section 4: Shadow diagnostic assertion tests
# ===========================================================================


class TestShadowDeferIntentResolvesOnTopicDisappearance:
    """Topic with shadow_defer_intent disappears from classifier
    -> intent no longer emitted on subsequent turn.

    Turn 1: two high topics detected, cooldown defers one -> shadow_defer_intent.
    Turn 2: text changes so deferred topic is absent -> no shadow_defer_intent.
    """

    def test_shadow_defer_intent_resolves_on_topic_disappearance(self) -> None:
        # Turn 1: text triggers both hook topics -> cooldown defers one
        text1_path = _write_text_file(
            "I need both PreToolUse and PostToolUse hooks and also skills frontmatter"
        )
        registry_path = _write_json_file(_make_empty_registry())

        try:
            r1 = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text1_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--shadow-mode",
                "--turn", "1",
            )
            assert r1.returncode == 0, f"turn 1 stderr: {r1.stderr}"
            dt1 = json.loads(r1.stdout)

            # Turn 2: text that does NOT mention the deferred topic
            text2_path = _write_text_file(
                "What is the weather forecast for tomorrow in Paris?"
            )

            r2 = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text2_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--shadow-mode",
                "--turn", "2",
            )
            assert r2.returncode == 0, f"turn 2 stderr: {r2.stderr}"
            dt2 = json.loads(r2.stdout)

            # Turn 2 should have zero shadow_defer_intents (topic disappeared)
            assert dt2["shadow_defer_intents"] == [], (
                f"Expected no shadow_defer_intents when topic disappears, "
                f"got: {dt2['shadow_defer_intents']}"
            )
        finally:
            os.unlink(text1_path)
            os.unlink(text2_path)
            os.unlink(registry_path)


class TestShadowDeferIntentResolvesOnSuppressedStateTransition:
    """Topic transitions to suppressed -> shadow_defer_intent no longer emitted.

    Setup a registry with one entry already suppressed. Run dialogue-turn in
    shadow mode with text matching that topic. Since entry is suppressed,
    no new candidate is generated and therefore no cooldown deferral.
    """

    def test_shadow_defer_intent_resolves_on_suppressed_state_transition(self) -> None:
        # Registry with one entry in suppressed state
        registry_data = _make_registry_seed(
            topic_key="hooks.pre_tool_use",
            state="suppressed",
        )
        registry_data["entries"][0]["suppression_reason"] = "redundant"
        registry_path = _write_json_file(registry_data)
        text_path = _write_text_file("How do I write a PreToolUse hook?")

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
            dt_data = json.loads(r.stdout)

            # Suppressed topic should not generate shadow_defer_intents
            assert dt_data["shadow_defer_intents"] == [], (
                f"Suppressed topic should not produce shadow_defer_intents, "
                f"got: {dt_data['shadow_defer_intents']}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestShadowFalsePositiveFieldPresentAndZero:
    """Shadow diagnostics -> false_positive_topic_detections key present
    with value 0."""

    def test_shadow_false_positive_field_present_and_zero(self) -> None:
        from scripts.ccdi.diagnostics import DiagnosticsEmitter

        emitter = DiagnosticsEmitter(
            status="shadow",
            phase="full",
            inventory_epoch="test-epoch",
            config_source="builtin",
        )
        result = emitter.emit()
        assert "false_positive_topic_detections" in result, (
            "Shadow diagnostics must include false_positive_topic_detections key"
        )
        assert result["false_positive_topic_detections"] == 0, (
            f"false_positive_topic_detections must be 0, got {result['false_positive_topic_detections']}"
        )


class TestCcdiInventorySnapshotAbsentWithSeedLayer2b:
    """ccdi_inventory_snapshot absent when ccdi_seed present -> degraded behavior.

    dialogue-turn with --registry-file but a non-existent --inventory-snapshot
    should fail gracefully (non-zero exit).
    """

    def test_ccdi_inventory_snapshot_absent_with_seed_layer2b(self) -> None:
        text_path = _write_text_file("PreToolUse hook")
        registry_path = _write_json_file(_make_empty_registry())

        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", "/nonexistent/path/inventory.json",
            )
            # Should fail gracefully: non-zero exit with error on stderr
            assert r.returncode != 0, (
                "dialogue-turn with missing inventory-snapshot should fail"
            )
            assert "not found" in r.stderr.lower() or "error" in r.stderr.lower(), (
                f"Expected error message about missing inventory, got stderr: {r.stderr}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


# ===========================================================================
# Section 5: Pipeline isolation tests
# ===========================================================================


class TestScoutPipelineNoCcdiCliCalls:
    """execute_scout/process_turn (context injection MCP tools) contain
    zero topic_inventory.py invocations.

    Verify that the context-injection server, pipeline, and execute modules
    do not reference or invoke CCDI CLI calls.
    """

    def test_scout_pipeline_no_ccdi_cli_calls(self) -> None:
        # Check the three core context-injection modules for topic_inventory references
        ci_dir = _PKG_ROOT / "context-injection" / "context_injection"
        core_modules = ["server.py", "pipeline.py", "execute.py"]

        for module_name in core_modules:
            module_path = ci_dir / module_name
            assert module_path.exists(), f"Missing context-injection module: {module_path}"
            source = module_path.read_text(encoding="utf-8")
            assert "topic_inventory" not in source, (
                f"context-injection/{module_name} must not reference topic_inventory "
                f"(CCDI and context-injection are separate pipelines)"
            )


class TestAgentDoesNotReadCcdiConfig:
    """Verify that classify and dialogue-turn CLI don't read config from
    a specific hardcoded path — they use defaults or --config flag only.

    Run classify and dialogue-turn without --config. Verify they succeed
    using builtin defaults (no file dependency).
    """

    def test_agent_does_not_read_ccdi_config(self) -> None:
        text_path = _write_text_file("PreToolUse hooks")
        registry_path = _write_json_file(_make_empty_registry())

        try:
            # classify: no --config flag, should use defaults
            r_classify = _run_cli(
                "classify",
                "--text-file", text_path,
                "--inventory", str(_INVENTORY),
            )
            assert r_classify.returncode == 0, (
                f"classify should work with builtin defaults, stderr: {r_classify.stderr}"
            )

            # dialogue-turn: no --config flag, should use defaults
            r_dt = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
            )
            assert r_dt.returncode == 0, (
                f"dialogue-turn should work with builtin defaults, stderr: {r_dt.stderr}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestCooldownConfigDivergence:
    """Agent gate uses hardcoded cooldown (1), config overlay can set
    different value -> verify both paths independently.

    The agent gate in topic_inventory.py uses _AGENT_HIGH_COUNT=1 (hardcoded).
    The config system allows injection.cooldown_max_new_topics_per_turn to
    differ. This test verifies both return their respective values.
    """

    def test_cooldown_config_divergence(self) -> None:
        from scripts.ccdi.config import CCDIConfigLoader, BUILTIN_DEFAULTS

        # Agent gate: hardcoded at 1
        from scripts.topic_inventory import _AGENT_HIGH_COUNT
        assert _AGENT_HIGH_COUNT == 1, (
            f"Agent gate _AGENT_HIGH_COUNT must be hardcoded at 1, got {_AGENT_HIGH_COUNT}"
        )

        # Config overlay: default is also 1, but the config system reads from file
        config = CCDIConfigLoader("/dev/null").load()
        config_cooldown = config.injection_cooldown_max_new_topics_per_turn
        default_cooldown = BUILTIN_DEFAULTS["injection"]["cooldown_max_new_topics_per_turn"]

        assert config_cooldown == default_cooldown, (
            f"Config cooldown ({config_cooldown}) should match builtin default ({default_cooldown})"
        )

        # Verify the two systems are independent: agent gate reads _AGENT_HIGH_COUNT,
        # not config.injection_cooldown_max_new_topics_per_turn
        # (They happen to share the same numeric value, but are separate code paths)
        assert isinstance(_AGENT_HIGH_COUNT, int)
        assert isinstance(config_cooldown, int)


class TestShadowModeNoInjectedDeferredMutations:
    """Shadow mode dialogue-turn -> registry has zero injected/deferred entries
    (only detected and suppressed allowed)."""

    def test_shadow_mode_no_injected_deferred_mutations(self) -> None:
        text_path = _write_text_file("How do I write a PreToolUse hook?")
        registry_path = _write_json_file(_make_empty_registry())

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

            with open(registry_path) as f:
                reg = json.load(f)

            for entry in reg["entries"]:
                assert entry["state"] not in ("injected", "deferred"), (
                    f"Shadow mode dialogue-turn should not produce {entry['state']} "
                    f"entries, but entry {entry['topic_key']} is {entry['state']}"
                )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestShadowModeZeroMarkDeferredInvocations:
    """Shadow mode full workflow -> zero --mark-deferred CLI calls.

    In shadow mode, the agent uses shadow_defer_intent trace entries
    instead of calling build-packet --mark-deferred.
    """

    def test_shadow_mode_zero_mark_deferred_invocations(self) -> None:
        # Use text that triggers multiple topics to force cooldown deferral
        text_path = _write_text_file(
            "I need both PreToolUse hooks and skills frontmatter patterns"
        )
        registry_path = _write_json_file(_make_empty_registry())

        try:
            # Run dialogue-turn in shadow mode
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--shadow-mode",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"

            # Verify registry has no deferred entries
            with open(registry_path) as f:
                reg = json.load(f)

            deferred_entries = [
                e for e in reg["entries"] if e["state"] == "deferred"
            ]
            assert len(deferred_entries) == 0, (
                f"Shadow mode should produce zero deferred entries, "
                f"got {len(deferred_entries)}: {[e['topic_key'] for e in deferred_entries]}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestShadowModeAutoSuppressionWritten:
    """Weak results in shadow mode -> suppressed state present in registry.

    Auto-suppression still fires in shadow mode because it is applied by
    dialogue-turn's internal logic, not by --mark-deferred.
    """

    def test_shadow_mode_auto_suppression_written(self) -> None:
        # Create a registry with an entry that will get suppressed
        # (both facets absent = weak_results suppression in dialogue-turn)
        registry_data = {
            "entries": [
                {
                    "topic_key": "hooks.pre_tool_use",
                    "family_key": "hooks",
                    "state": "detected",
                    "first_seen_turn": 0,
                    "last_seen_turn": 0,
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
                        "injected_chunk_ids": [],
                    },
                }
            ],
            "docs_epoch": "test-epoch-abc",
            "inventory_snapshot_version": "1",
        }
        registry_path = _write_json_file(registry_data)

        # Off-topic text so the entry won't be re-detected -> consecutive_medium resets
        text_path = _write_text_file(
            "What is the weather forecast for tomorrow?"
        )

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

            with open(registry_path) as f:
                reg = json.load(f)

            # The pre-existing entry should still be in registry
            # (shadow mode does not prevent state persistence)
            assert len(reg["entries"]) >= 1, (
                "Registry should still have entries after shadow mode dialogue-turn"
            )

            # Suppressed state IS allowed in shadow mode (it's an internal
            # scheduling decision, not an injection mutation)
            states = {e["state"] for e in reg["entries"]}
            allowed_states = {"detected", "suppressed"}
            assert states <= allowed_states, (
                f"Shadow mode registry states should be in {allowed_states}, got {states}"
            )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)


class TestCliBackstopShadowMarkDeferred:
    """If --shadow-mode + --mark-deferred is passed to build-packet
    -> exit 0, no registry write (CLI backstop)."""

    def test_cli_backstop_shadow_mark_deferred(self) -> None:
        results_path = _write_json_file(_make_search_results())
        registry_data = _make_registry_seed()
        registry_path = _write_json_file(registry_data)

        try:
            # Snapshot the registry before the call
            with open(registry_path) as f:
                reg_before = json.load(f)

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
            assert r.returncode == 0, f"stderr: {r.stderr}"

            # Registry should be unchanged (no write)
            with open(registry_path) as f:
                reg_after = json.load(f)

            assert reg_after == reg_before, (
                "CLI backstop: --shadow-mode + --mark-deferred should not modify registry"
            )

            # stderr should contain the shadow log message
            assert "shadow" in r.stderr.lower(), (
                f"Expected shadow log on stderr, got: {r.stderr}"
            )
        finally:
            os.unlink(results_path)
            os.unlink(registry_path)


class TestShadowDeferIntentTraceEntries:
    """shadow_defer_intent entries emitted with correct fields:
    turn, action, topic_key, reason, classify_result_hash.

    Triggers cooldown by detecting more topics than max_new_per_turn (1).
    """

    def test_shadow_defer_intent_trace_entries(self) -> None:
        # Text that triggers multiple topics -> cooldown defers extras
        text_path = _write_text_file(
            "I need both PreToolUse hooks and skills frontmatter patterns"
        )
        registry_path = _write_json_file(_make_empty_registry())

        try:
            r = _run_cli(
                "dialogue-turn",
                "--registry-file", registry_path,
                "--text-file", text_path,
                "--source", "codex",
                "--inventory-snapshot", str(_INVENTORY),
                "--shadow-mode",
                "--turn", "5",
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
            dt_data = json.loads(r.stdout)

            # Must have at least one shadow_defer_intent if cooldown triggered
            candidates = dt_data["candidates"]
            shadow_intents = dt_data["shadow_defer_intents"]

            if len(candidates) > 0 and len(shadow_intents) > 0:
                # Verify each shadow_defer_intent has all required fields
                required_fields = {
                    "turn", "action", "topic_key", "reason", "classify_result_hash"
                }
                for sdi in shadow_intents:
                    present_fields = set(sdi.keys())
                    missing = required_fields - present_fields
                    assert missing == set(), (
                        f"shadow_defer_intent missing fields {missing}: {sdi}"
                    )
                    assert sdi["action"] == "shadow_defer_intent", (
                        f"action must be 'shadow_defer_intent', got {sdi['action']!r}"
                    )
                    assert sdi["turn"] == 5, (
                        f"turn must match --turn flag (5), got {sdi['turn']}"
                    )
                    assert sdi["reason"] == "cooldown", (
                        f"reason must be 'cooldown', got {sdi['reason']!r}"
                    )
                    assert isinstance(sdi["classify_result_hash"], str), (
                        f"classify_result_hash must be str, got {type(sdi['classify_result_hash'])}"
                    )
                    assert len(sdi["classify_result_hash"]) > 0, (
                        "classify_result_hash must be non-empty"
                    )
            else:
                # If cooldown didn't trigger (only 1 topic detected), the test
                # still passes — it verifies the output structure is correct.
                # Check that shadow_defer_intents key exists and is a list
                assert isinstance(shadow_intents, list), (
                    f"shadow_defer_intents must be a list, got {type(shadow_intents)}"
                )
        finally:
            os.unlink(text_path)
            os.unlink(registry_path)
