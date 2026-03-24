"""CCDI replay harness — parametrized fixture-driven CLI pipeline tests.

Reads all *.replay.json fixtures from tests/fixtures/ccdi/, parametrizes
them as pytest test cases, and replays the CLI pipeline per turn.

Each fixture defines:
- Initial registry state (optional)
- Inventory snapshot reference
- Per-turn inputs (text, source, hints, search results)
- Per-turn expected outputs (classifier result, candidates)
- End-of-fixture assertions (CLI sequence, registry state, trace)

The harness invokes the CCDI CLI via subprocess, exactly as the agent would.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_DIR = _PKG_ROOT / "tests" / "fixtures" / "ccdi"


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CCDI CLI as a subprocess."""
    return subprocess.run(
        ["uv", "run", "python", "-m", "scripts.topic_inventory", *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(_PKG_ROOT),
    )


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


def load_fixtures() -> list[tuple[str, dict]]:
    """Glob all *.replay.json from the fixture directory.

    Returns list of (fixture_name, fixture_data) tuples.
    """
    fixtures: list[tuple[str, dict]] = []
    for path in sorted(_FIXTURE_DIR.glob("*.replay.json")):
        with open(path) as f:
            data = json.load(f)
        name = data.get("name", path.stem)
        fixtures.append((name, data))
    return fixtures


def _fixture_ids() -> list[str]:
    """Return fixture names for pytest parametrize ids."""
    return [name for name, _ in load_fixtures()]


# ---------------------------------------------------------------------------
# Temp file helpers
# ---------------------------------------------------------------------------


def _write_text_file(text: str, suffix: str = ".txt") -> str:
    """Write text to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


def _write_json_file(data: dict | list, suffix: str = ".json") -> str:
    """Write JSON to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


# ---------------------------------------------------------------------------
# JSON path resolver for registry assertions
# ---------------------------------------------------------------------------


def _resolve_json_path(data: object, path: str) -> object:
    """Resolve a dot-notation path with array indexing on a JSON structure.

    Examples:
        "entries[0].state" -> data["entries"][0]["state"]
        "entries[0].coverage.injected_chunk_ids" -> data["entries"][0]["coverage"]["injected_chunk_ids"]
    """
    current = data
    for segment in path.replace("[", ".[").split("."):
        if not segment:
            continue
        if segment.startswith("[") and segment.endswith("]"):
            idx = int(segment[1:-1])
            current = current[idx]
        else:
            current = current[segment]
    return current


# ---------------------------------------------------------------------------
# Assertion operators
# ---------------------------------------------------------------------------


def _apply_operator(actual: object, operator: str, expected: object) -> None:
    """Apply an assertion operator."""
    if operator == "equals":
        assert actual == expected, (
            f"equals failed: {actual!r} != {expected!r}"
        )
    elif operator == "contains":
        assert expected in actual, (
            f"contains failed: {expected!r} not in {actual!r}"
        )
    elif operator == "length_gte":
        assert len(actual) >= expected, (
            f"length_gte failed: len({actual!r}) = {len(actual)} < {expected}"
        )
    elif operator == "is_null":
        assert actual is None, (
            f"is_null failed: {actual!r} is not None"
        )
    elif operator == "not_null":
        assert actual is not None, (
            f"not_null failed: value is None"
        )
    else:
        raise ValueError(f"Unknown assertion operator: {operator!r}")


# ---------------------------------------------------------------------------
# Trace assertion operators
# ---------------------------------------------------------------------------


def _apply_trace_operator(
    trace_entry: dict, operator: str, expected: object
) -> None:
    """Apply a trace-level assertion operator."""
    if operator == "assert_key_present":
        assert expected in trace_entry, (
            f"assert_key_present failed: key {expected!r} not in trace entry. "
            f"Keys present: {list(trace_entry.keys())}"
        )
    elif operator == "action":
        assert trace_entry.get("action") == expected, (
            f"action failed: {trace_entry.get('action')!r} != {expected!r}"
        )
    else:
        raise ValueError(f"Unknown trace assertion operator: {operator!r}")


# ---------------------------------------------------------------------------
# Registry comparison
# ---------------------------------------------------------------------------


def assert_registry_unchanged(before_path: str, after_path: str) -> None:
    """Deep JSON equality including null-valued keys."""
    with open(before_path) as f:
        before = json.load(f)
    with open(after_path) as f:
        after = json.load(f)
    assert before == after, (
        f"Registry changed unexpectedly.\n"
        f"Before: {json.dumps(before, indent=2)}\n"
        f"After:  {json.dumps(after, indent=2)}"
    )


# ---------------------------------------------------------------------------
# ReplayRunner — per-fixture runner
# ---------------------------------------------------------------------------


class ReplayRunner:
    """Runs a single replay fixture, maintaining state across turns."""

    def __init__(self, fixture: dict, tmp_dir: str) -> None:
        self.fixture = fixture
        self.tmp_dir = tmp_dir
        self.cli_log: list[dict] = []
        self.trace: list[dict] = []
        self.temp_files: list[str] = []

        # Resolve inventory snapshot path
        inv_ref = fixture.get("inventory_snapshot", "test_inventory.json")
        self.inventory_path = str(_FIXTURE_DIR / inv_ref)

        # Set up registry file
        initial_reg = fixture.get("initial_registry")
        self.registry_path = os.path.join(tmp_dir, "registry.json")
        if initial_reg is not None:
            with open(self.registry_path, "w") as f:
                json.dump(initial_reg, f)

        # Config file (optional)
        config_data = fixture.get("config")
        self.config_path: str | None = None
        if config_data is not None:
            self.config_path = os.path.join(tmp_dir, "config.json")
            with open(self.config_path, "w") as f:
                json.dump(config_data, f)

    def _record_cli(self, subcommand: str, **key_args: object) -> None:
        """Record a CLI invocation for sequence assertions."""
        entry = {"subcommand": subcommand}
        entry.update(key_args)
        self.cli_log.append(entry)

    def _temp_file(self, content: str, suffix: str = ".txt") -> str:
        """Create a temp file and track it for cleanup."""
        path = _write_text_file(content, suffix=suffix)
        self.temp_files.append(path)
        return path

    def _temp_json(self, data: dict | list, suffix: str = ".json") -> str:
        """Create a temp JSON file and track it for cleanup."""
        path = _write_json_file(data, suffix=suffix)
        self.temp_files.append(path)
        return path

    def run_turn(self, turn: dict) -> None:
        """Execute a single turn of the replay fixture."""
        turn_number = turn["turn_number"]
        input_text = turn["input_text"]
        source = turn.get("source", "codex")
        shadow_mode = turn.get("shadow_mode", False)
        docs_epoch = turn.get("docs_epoch")
        semantic_hints = turn.get("semantic_hints")
        expected_classifier = turn.get("expected_classifier_result")
        expected_candidates = turn.get("expected_candidates")
        search_results = turn.get("search_results", {})
        composed_target = turn.get("composed_target")
        codex_reply_error = turn.get("codex_reply_error", False)

        # Initialize per-turn trace entry
        trace_entry: dict = {
            "turn": turn_number,
            "action": "replay_turn",
            "topics_detected": [],
            "candidates": [],
            "packet_staged": False,
            "scout_conflict": False,
            "commit": False,
            "shadow_suppressed": shadow_mode,
            "semantic_hints": semantic_hints or [],
        }

        # ---------------------------------------------------------------
        # Step 1: Classify
        # ---------------------------------------------------------------
        text_path = self._temp_file(input_text)
        classify_result = _run_cli(
            "classify",
            "--text-file", text_path,
            "--inventory", self.inventory_path,
        )
        self._record_cli("classify", text_file=text_path)
        assert classify_result.returncode == 0, (
            f"classify failed (turn {turn_number}): {classify_result.stderr}"
        )
        classifier_data = json.loads(classify_result.stdout)

        if expected_classifier is not None:
            self._assert_classifier(classifier_data, expected_classifier, turn_number)

        # Record detected topics in trace
        trace_entry["topics_detected"] = [
            t["topic_key"] for t in classifier_data.get("resolved_topics", [])
        ]

        # ---------------------------------------------------------------
        # Step 2: dialogue-turn
        # ---------------------------------------------------------------
        dt_args = [
            "dialogue-turn",
            "--registry-file", self.registry_path,
            "--text-file", text_path,
            "--source", source,
            "--inventory-snapshot", self.inventory_path,
            "--turn", str(turn_number),
        ]
        if shadow_mode:
            dt_args.append("--shadow-mode")
        if docs_epoch is not None:
            dt_args.extend(["--docs-epoch", docs_epoch])
        if self.config_path is not None:
            dt_args.extend(["--config", self.config_path])

        # Write semantic hints file if provided
        if semantic_hints is not None:
            hints_path = self._temp_json(semantic_hints, suffix=".hints.json")
            dt_args.extend(["--semantic-hints-file", hints_path])

        dt_result = _run_cli(*dt_args)
        self._record_cli("dialogue-turn", source=source, turn=turn_number)
        assert dt_result.returncode == 0, (
            f"dialogue-turn failed (turn {turn_number}): {dt_result.stderr}"
        )
        dt_data = json.loads(dt_result.stdout)
        candidates = dt_data.get("candidates", [])

        if expected_candidates is not None:
            self._assert_candidates(candidates, expected_candidates, turn_number)

        trace_entry["candidates"] = [c["topic_key"] for c in candidates]

        # ---------------------------------------------------------------
        # Steps 3-4: For each candidate with search_results, build-packet
        # ---------------------------------------------------------------
        prepare_chunk_ids: dict[str, list[str]] = {}

        for candidate in candidates:
            topic_key = candidate["topic_key"]
            if topic_key not in search_results:
                continue

            results_data = search_results[topic_key]
            results_path = self._temp_json(results_data, suffix=".results.json")
            facet = candidate.get("facet", "overview")
            coverage_target = candidate.get("coverage_target", "leaf")

            # --- Prepare phase (no --mark-injected) ---
            prepare_args = [
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", self.registry_path,
                "--inventory-snapshot", self.inventory_path,
                "--topic-key", topic_key,
                "--facet", facet,
                "--coverage-target", coverage_target,
            ]
            if shadow_mode:
                prepare_args.append("--shadow-mode")

            prepare_result = _run_cli(*prepare_args)
            self._record_cli(
                "build-packet",
                phase="prepare",
                topic_key=topic_key,
                facet=facet,
            )
            assert prepare_result.returncode == 0, (
                f"build-packet prepare failed (turn {turn_number}, "
                f"topic {topic_key}): {prepare_result.stderr}"
            )

            if prepare_result.stdout.strip():
                trace_entry["packet_staged"] = True

                # Extract chunk_ids from the packet output by re-reading the
                # results file (since build-packet uses the same results)
                chunk_ids_for_prepare = [
                    r["chunk_id"] for r in results_data
                    if "chunk_id" in r
                ]
                prepare_chunk_ids[f"{topic_key}:{facet}"] = chunk_ids_for_prepare

            # --- Target-match check ---
            if composed_target is not None:
                canonical_label = candidate.get("canonical_label")
                target_relevant = False

                # Substring check: does any candidate's canonical_label
                # appear in the composed target?
                if canonical_label and canonical_label.lower() in composed_target.lower():
                    target_relevant = True
                else:
                    # Fallback: classify the composed target
                    target_text_path = self._temp_file(composed_target)
                    target_cls = _run_cli(
                        "classify",
                        "--text-file", target_text_path,
                        "--inventory", self.inventory_path,
                    )
                    self._record_cli("classify", purpose="target-match")
                    if target_cls.returncode == 0:
                        target_data = json.loads(target_cls.stdout)
                        target_topics = {
                            t["topic_key"]
                            for t in target_data.get("resolved_topics", [])
                        }
                        if topic_key in target_topics:
                            target_relevant = True

                if not target_relevant:
                    # Target mismatch: mark deferred, skip commit
                    self._record_cli(
                        "build-packet",
                        phase="mark-deferred",
                        topic_key=topic_key,
                        reason="target_mismatch",
                    )
                    continue

            # --- Commit phase ---
            if codex_reply_error:
                # Simulate send failure: skip commit
                trace_entry["commit"] = False
                continue

            commit_args = [
                "build-packet",
                "--results-file", results_path,
                "--mode", "initial",
                "--registry-file", self.registry_path,
                "--inventory-snapshot", self.inventory_path,
                "--topic-key", topic_key,
                "--facet", facet,
                "--coverage-target", coverage_target,
                "--mark-injected",
            ]

            commit_result = _run_cli(*commit_args)
            self._record_cli(
                "build-packet",
                phase="commit",
                topic_key=topic_key,
                facet=facet,
            )
            assert commit_result.returncode == 0, (
                f"build-packet commit failed (turn {turn_number}, "
                f"topic {topic_key}): {commit_result.stderr}"
            )
            trace_entry["commit"] = True

            # Verify chunk ID determinism: prepare chunk IDs match
            # what was committed (same results file + facet)
            key = f"{topic_key}:{facet}"
            if key in prepare_chunk_ids:
                # Read registry to verify committed chunk_ids match
                with open(self.registry_path) as f:
                    reg_after = json.load(f)
                for entry in reg_after.get("entries", []):
                    if entry["topic_key"] == topic_key:
                        committed_ids = entry.get("coverage", {}).get(
                            "injected_chunk_ids", []
                        )
                        for cid in prepare_chunk_ids[key]:
                            assert cid in committed_ids, (
                                f"Chunk ID determinism failed: {cid!r} from "
                                f"prepare not in committed IDs {committed_ids}"
                            )

        self.trace.append(trace_entry)

    def _assert_classifier(
        self,
        actual: dict,
        expected: dict,
        turn: int,
    ) -> None:
        """Assert classifier result matches expectations."""
        if "resolved_topic_keys" in expected:
            actual_keys = [
                t["topic_key"] for t in actual.get("resolved_topics", [])
            ]
            for key in expected["resolved_topic_keys"]:
                assert key in actual_keys, (
                    f"Turn {turn}: expected topic {key!r} in classifier result, "
                    f"got {actual_keys}"
                )
        if "min_resolved_count" in expected:
            actual_count = len(actual.get("resolved_topics", []))
            assert actual_count >= expected["min_resolved_count"], (
                f"Turn {turn}: expected >= {expected['min_resolved_count']} "
                f"resolved topics, got {actual_count}"
            )

    def _assert_candidates(
        self,
        actual: list[dict],
        expected: list[dict],
        turn: int,
    ) -> None:
        """Assert dialogue-turn candidates match expectations."""
        actual_keys = [c["topic_key"] for c in actual]
        for exp in expected:
            if "topic_key" in exp:
                assert exp["topic_key"] in actual_keys, (
                    f"Turn {turn}: expected candidate {exp['topic_key']!r}, "
                    f"got {actual_keys}"
                )
            if "min_count" in exp:
                assert len(actual) >= exp["min_count"], (
                    f"Turn {turn}: expected >= {exp['min_count']} candidates, "
                    f"got {len(actual)}"
                )

    def run_assertions(self) -> None:
        """Run end-of-fixture assertions."""
        assertions = self.fixture.get("assertions", {})

        # CLI pipeline sequence
        if "cli_pipeline_sequence" in assertions:
            expected_seq = assertions["cli_pipeline_sequence"]
            actual_seq = [entry["subcommand"] for entry in self.cli_log]
            assert actual_seq == expected_seq, (
                f"CLI pipeline sequence mismatch.\n"
                f"Expected: {expected_seq}\n"
                f"Actual:   {actual_seq}"
            )

        # CLI calls absent
        if "cli_calls_absent" in assertions:
            actual_subcmds = {entry["subcommand"] for entry in self.cli_log}
            for absent in assertions["cli_calls_absent"]:
                assert absent not in actual_subcmds, (
                    f"CLI call {absent!r} should be absent but was invoked"
                )

        # Final registry state
        if "final_registry_state" in assertions:
            with open(self.registry_path) as f:
                final_reg = json.load(f)
            for key, expected_val in assertions["final_registry_state"].items():
                actual_val = _resolve_json_path(final_reg, key)
                assert actual_val == expected_val, (
                    f"Final registry assertion failed for {key!r}: "
                    f"{actual_val!r} != {expected_val!r}"
                )

        # Final registry file assertions (with operators)
        if "final_registry_file_assertions" in assertions:
            with open(self.registry_path) as f:
                final_reg = json.load(f)
            for assertion in assertions["final_registry_file_assertions"]:
                path = assertion["path"]
                operator = assertion["operator"]
                expected = assertion.get("expected")
                actual = _resolve_json_path(final_reg, path)
                _apply_operator(actual, operator, expected)

        # Trace assertions
        if "trace_assertions" in assertions:
            for ta in assertions["trace_assertions"]:
                turn_idx = ta.get("turn_index", 0)
                assert turn_idx < len(self.trace), (
                    f"Trace assertion references turn_index {turn_idx} but only "
                    f"{len(self.trace)} turns were traced"
                )
                trace_entry = self.trace[turn_idx]
                operator = ta["operator"]
                expected = ta.get("expected")
                _apply_trace_operator(trace_entry, operator, expected)

    def cleanup(self) -> None:
        """Remove tracked temp files."""
        for path in self.temp_files:
            try:
                os.unlink(path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Parametrized test
# ---------------------------------------------------------------------------

_FIXTURES = load_fixtures()


@pytest.mark.parametrize(
    "fixture_name,fixture_data",
    _FIXTURES,
    ids=[name for name, _ in _FIXTURES],
)
def test_replay(fixture_name: str, fixture_data: dict, tmp_path: Path) -> None:
    """Replay a CCDI fixture through the CLI pipeline and verify assertions."""
    runner = ReplayRunner(fixture_data, str(tmp_path))
    try:
        for turn in fixture_data.get("turns", []):
            runner.run_turn(turn)
        runner.run_assertions()
    finally:
        runner.cleanup()
