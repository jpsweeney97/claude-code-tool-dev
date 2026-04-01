"""Tests for shared JSONL replay helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from server.replay import (
    SchemaViolation,
    UnknownOperation,
    replay_jsonl,
)


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    """Pass-through callback that returns the record as-is."""
    return record


def _write_lines(path: Path, lines: list[str]) -> None:
    """Write raw lines to a file (one per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


class TestBasicReplay:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "missing.jsonl"
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert diags.diagnostics == ()

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert diags.diagnostics == ()

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "blank.jsonl"
        _write_lines(path, ["", "  ", "\t", json.dumps({"a": 1}), ""])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert results[0] == {"a": 1}
        assert diags.diagnostics == ()

    def test_single_valid_record(self, tmp_path: Path) -> None:
        path = tmp_path / "single.jsonl"
        _write_lines(path, [json.dumps({"key": "value"})])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert results[0] == {"key": "value"}

    def test_multiple_valid_records_preserve_order(self, tmp_path: Path) -> None:
        path = tmp_path / "multi.jsonl"
        _write_lines(path, [json.dumps({"n": i}) for i in range(3)])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 3
        assert [r["n"] for r in results] == [0, 1, 2]

    def test_callback_returning_none_not_collected(self, tmp_path: Path) -> None:
        path = tmp_path / "none.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), json.dumps({"a": 2})])
        results, _ = replay_jsonl(path, lambda r: None)
        assert results == ()


class TestCorruptionClassification:
    def test_trailing_truncation_after_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "trailing.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), "not valid json"])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "trailing_truncation"
        assert diags.diagnostics[0].line_number == 2

    def test_mid_file_corruption_before_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "midfile.jsonl"
        _write_lines(path, ["corrupt", json.dumps({"a": 1})])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "mid_file_corruption"
        assert diags.diagnostics[0].line_number == 1

    def test_mixed_trailing_and_mid_file(self, tmp_path: Path) -> None:
        path = tmp_path / "mixed.jsonl"
        _write_lines(
            path,
            [
                "corrupt1",  # line 1 — mid-file
                json.dumps({"a": 1}),  # line 2 — valid
                "corrupt2",  # line 3 — trailing
            ],
        )
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[3] == "trailing_truncation"

    def test_all_corrupt_file_is_mid_file_corruption(self, tmp_path: Path) -> None:
        """No valid JSON prefix → all failures are mid-file corruption."""
        path = tmp_path / "allcorrupt.jsonl"
        _write_lines(path, ["bad1", "bad2", "bad3"])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 3
        assert all(d.label == "mid_file_corruption" for d in diags.diagnostics)

    def test_non_dict_json_counts_as_valid_json_for_classification(
        self, tmp_path: Path
    ) -> None:
        """Non-dict JSON (array) is a schema violation but counts as
        successful JSON parse for trailing-truncation classification."""
        path = tmp_path / "nondict.jsonl"
        _write_lines(
            path,
            [
                "corrupt1",  # line 1 — mid-file (before valid JSON)
                json.dumps([1, 2]),  # line 2 — valid JSON, schema violation
                "corrupt2",  # line 3 — trailing (after valid JSON)
            ],
        )
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[2] == "schema_violation"
        assert labels[3] == "trailing_truncation"

    def test_schema_violation_counts_as_valid_json_for_classification(
        self, tmp_path: Path
    ) -> None:
        """Callback SchemaViolation still counts as successful JSON parse
        for trailing-truncation classification."""
        path = tmp_path / "schemaclass.jsonl"
        _write_lines(
            path,
            [
                "corrupt",  # line 1 — mid-file
                json.dumps({"bad": 1}),  # line 2 — callback raises SchemaViolation
                "corrupt2",  # line 3 — trailing
            ],
        )

        def rejecting(record: dict[str, Any]) -> dict[str, Any]:
            raise SchemaViolation("always rejects")

        _, diags = replay_jsonl(path, rejecting)
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[2] == "schema_violation"
        assert labels[3] == "trailing_truncation"

    def test_unknown_operation_counts_as_valid_json_for_classification(
        self, tmp_path: Path
    ) -> None:
        """Callback UnknownOperation still counts as successful JSON parse
        for trailing-truncation classification."""
        path = tmp_path / "unknownclass.jsonl"
        _write_lines(
            path,
            [
                "corrupt",  # line 1 — mid-file
                json.dumps(
                    {"op": "bogus"}
                ),  # line 2 — callback raises UnknownOperation
                "corrupt2",  # line 3 — trailing
            ],
        )

        def unknown(record: dict[str, Any]) -> dict[str, Any]:
            raise UnknownOperation(record.get("op"))

        _, diags = replay_jsonl(path, unknown)
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[2] == "unknown_operation"
        assert labels[3] == "trailing_truncation"

    def test_partial_final_line_without_newline(self, tmp_path: Path) -> None:
        """A crash-truncated final line (no trailing newline) is classified
        as trailing truncation, not mid-file corruption."""
        path = tmp_path / "partial.jsonl"
        # Write a valid line followed by a partial line with no newline
        path.write_text(json.dumps({"a": 1}) + "\n" + '{"truncat')
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "trailing_truncation"
        assert diags.diagnostics[0].line_number == 2


class TestExceptionHandling:
    def test_schema_violation_from_callback(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])

        def bad_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise SchemaViolation("test violation")

        results, diags = replay_jsonl(path, bad_callback)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "test violation" in diags.diagnostics[0].detail

    def test_unknown_operation_from_callback(self, tmp_path: Path) -> None:
        path = tmp_path / "unknown.jsonl"
        _write_lines(path, [json.dumps({"op": "bogus"})])

        def unknown_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise UnknownOperation(record.get("op"))

        results, diags = replay_jsonl(path, unknown_callback)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "unknown_operation"
        assert "bogus" in diags.diagnostics[0].detail

    def test_programmer_bug_propagates(self, tmp_path: Path) -> None:
        path = tmp_path / "bug.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])

        def buggy_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise ValueError("this is a bug")

        with pytest.raises(ValueError, match="this is a bug"):
            replay_jsonl(path, buggy_callback)

    def test_non_dict_json_array_produces_schema_violation(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "array.jsonl"
        _write_lines(path, [json.dumps([1, 2, 3])])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "list" in diags.diagnostics[0].detail

    def test_non_dict_json_string_produces_schema_violation(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "string.jsonl"
        _write_lines(path, [json.dumps("hello")])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "str" in diags.diagnostics[0].detail


class TestDiagnosticsModel:
    def test_diagnostics_sorted_by_line_number(self, tmp_path: Path) -> None:
        path = tmp_path / "sorted.jsonl"
        _write_lines(
            path,
            [
                "corrupt",  # line 1 — mid-file corruption
                json.dumps({"a": 1}),  # line 2 — valid
                json.dumps([1]),  # line 3 — schema violation (non-dict)
                "corrupt2",  # line 4 — trailing truncation
            ],
        )
        _, diags = replay_jsonl(path, _identity)
        line_numbers = [d.line_number for d in diags.diagnostics]
        assert line_numbers == [1, 3, 4]

    def test_has_warnings_true_for_mid_file_corruption(self, tmp_path: Path) -> None:
        path = tmp_path / "midwarn.jsonl"
        _write_lines(path, ["corrupt", json.dumps({"a": 1})])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is True

    def test_has_warnings_false_for_trailing_only(self, tmp_path: Path) -> None:
        path = tmp_path / "trail.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), "corrupt"])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is False

    def test_has_warnings_false_for_no_diagnostics(self, tmp_path: Path) -> None:
        path = tmp_path / "clean.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is False

    def test_unknown_operation_carries_op_attribute(self) -> None:
        exc = UnknownOperation("test_op")
        assert exc.op == "test_op"
        assert "test_op" in str(exc)

    def test_unknown_operation_with_none_op(self) -> None:
        exc = UnknownOperation(None)
        assert exc.op is None
        assert "None" in str(exc)
