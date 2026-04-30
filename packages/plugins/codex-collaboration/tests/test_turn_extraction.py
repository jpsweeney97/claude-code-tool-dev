from __future__ import annotations

from server.turn_extraction import extract_agent_message


class TestExtractAgentMessage:
    """Tests #1-#3: shared extractor for thread/read projection shapes."""

    def test_extracts_top_level_agent_message(self) -> None:
        raw_turn = {"id": "t1", "status": "completed", "agentMessage": "hello world"}
        assert extract_agent_message(raw_turn) == "hello world"

    def test_extracts_from_items_list(self) -> None:
        raw_turn = {
            "id": "t1",
            "status": "completed",
            "items": [
                {"type": "agentMessage", "text": "from items"},
            ],
        }
        assert extract_agent_message(raw_turn) == "from items"

    def test_returns_empty_when_neither_shape_exists(self) -> None:
        assert extract_agent_message({"id": "t1", "status": "completed"}) == ""

    def test_ignores_malformed_items(self) -> None:
        raw_turn = {
            "id": "t1",
            "status": "completed",
            "items": [
                "not a dict",
                42,
                None,
                {"type": "toolCall", "text": "wrong type"},
                {"type": "agentMessage"},  # missing text
            ],
        }
        assert extract_agent_message(raw_turn) == ""

    def test_top_level_takes_precedence_over_items(self) -> None:
        raw_turn = {
            "id": "t1",
            "agentMessage": "top-level wins",
            "items": [{"type": "agentMessage", "text": "items loses"}],
        }
        assert extract_agent_message(raw_turn) == "top-level wins"
