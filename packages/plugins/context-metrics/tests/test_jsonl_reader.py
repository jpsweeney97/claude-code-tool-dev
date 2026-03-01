"""Tests for JSONL reader."""

import json
from pathlib import Path

from scripts.jsonl_reader import (
    compute_occupancy,
    count_messages,
    is_main_thread_response,
    tail_read_last_valid,
)


class TestIsMainThreadResponse:
    """Test the 4-condition positive-only selector (Amendment 4 F2)."""

    def test_valid_assistant_record(self) -> None:
        record = {
            "type": "assistant",
            "message": {
                "id": "msg_01",
                "role": "assistant",
                "usage": {"input_tokens": 1, "cache_read_input_tokens": 50000,
                          "cache_creation_input_tokens": 1000, "output_tokens": 500},
            },
        }
        assert is_main_thread_response(record) is True

    def test_rejects_user_type(self) -> None:
        record = {"type": "user", "content": "hello"}
        assert is_main_thread_response(record) is False

    def test_rejects_missing_usage(self) -> None:
        record = {"type": "assistant", "message": {"role": "assistant"}}
        assert is_main_thread_response(record) is False

    def test_rejects_missing_input_tokens(self) -> None:
        record = {
            "type": "assistant",
            "message": {"role": "assistant", "usage": {"output_tokens": 500}},
        }
        assert is_main_thread_response(record) is False

    def test_rejects_wrong_message_role(self) -> None:
        record = {
            "type": "assistant",
            "message": {"role": "user", "usage": {"input_tokens": 1}},
        }
        assert is_main_thread_response(record) is False

    def test_rejects_agent_progress(self) -> None:
        record = {
            "type": "agent_progress",
            "message": {"role": "assistant", "usage": {"input_tokens": 5000}},
        }
        assert is_main_thread_response(record) is False


class TestComputeOccupancy:
    def test_all_fields_present(self) -> None:
        usage = {
            "input_tokens": 1,
            "cache_read_input_tokens": 158000,
            "cache_creation_input_tokens": 2000,
            "output_tokens": 900,
        }
        assert compute_occupancy(usage) == 160001

    def test_missing_cache_fields_default_zero(self) -> None:
        usage = {"input_tokens": 5000}
        assert compute_occupancy(usage) == 5000

    def test_non_integer_token_values_treated_as_zero(self) -> None:
        """Fail-closed: non-int values from format drift are treated as 0."""
        usage = {
            "input_tokens": "1",
            "cache_read_input_tokens": 50000,
            "cache_creation_input_tokens": None,
        }
        assert compute_occupancy(usage) == 50000  # only the valid int field counts


class TestCountMessages:
    def test_counts_user_and_assistant_records(self, normal_session: Path) -> None:
        """normal_session.jsonl has 5 assistant + 4 user = 9 messages."""
        assert count_messages(normal_session) == 9

    def test_empty_file_returns_zero(self, empty_session: Path) -> None:
        assert count_messages(empty_session) == 0

    def test_skips_malformed_lines(self, malformed_session: Path) -> None:
        count = count_messages(malformed_session)
        assert count > 0  # Should count valid records, skip malformed ones

    def test_nonexistent_file_returns_zero(self, tmp_path: Path) -> None:
        assert count_messages(tmp_path / "nonexistent.jsonl") == 0


class TestTailReadLastValid:
    def test_normal_session_returns_last_record(self, normal_session: Path) -> None:
        record = tail_read_last_valid(normal_session)
        assert record is not None
        assert record["message"]["id"] == "msg_05"
        assert compute_occupancy(record["message"]["usage"]) == 160001

    def test_malformed_skips_bad_records(self, malformed_session: Path) -> None:
        record = tail_read_last_valid(malformed_session)
        assert record is not None
        # Should find the last valid assistant record, deduplicating msg_31
        assert record["message"]["id"] == "msg_31"

    def test_empty_file_returns_none(self, empty_session: Path) -> None:
        record = tail_read_last_valid(empty_session)
        assert record is None

    def test_compaction_session_returns_post_compaction(
        self, compaction_session: Path
    ) -> None:
        record = tail_read_last_valid(compaction_session)
        assert record is not None
        assert record["message"]["id"] == "msg_11"
        assert compute_occupancy(record["message"]["usage"]) == 31001

    def test_partial_line_at_eof_discarded(self, tmp_path: Path) -> None:
        """Simulate concurrent write: last line is incomplete."""
        fixture = tmp_path / "partial.jsonl"
        valid = {"type": "assistant", "message": {"id": "msg_40", "role": "assistant",
                 "usage": {"input_tokens": 1, "cache_read_input_tokens": 50000,
                           "cache_creation_input_tokens": 1000, "output_tokens": 500}}}
        fixture.write_text(json.dumps(valid) + "\n" + '{"type":"assistant","mess')
        record = tail_read_last_valid(fixture)
        assert record is not None
        assert record["message"]["id"] == "msg_40"

    def test_deduplicates_by_message_id(self, tmp_path: Path) -> None:
        """Condition 4: deduplicate by message.id -- return first seen from tail."""
        fixture = tmp_path / "dupes.jsonl"
        rec = {"type": "assistant", "message": {"id": "msg_50", "role": "assistant",
               "usage": {"input_tokens": 1, "cache_read_input_tokens": 80000,
                         "cache_creation_input_tokens": 1000, "output_tokens": 500}}}
        fixture.write_text(json.dumps(rec) + "\n" + json.dumps(rec) + "\n")
        record = tail_read_last_valid(fixture)
        assert record is not None
        assert record["message"]["id"] == "msg_50"
