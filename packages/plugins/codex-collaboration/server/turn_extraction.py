"""Agent message extraction from thread/read projection shapes."""

from __future__ import annotations

from collections.abc import Mapping


def extract_agent_message(raw_turn: Mapping[str, object]) -> str:
    """Extract agent message text from a thread/read turn projection.

    Handles two server projection shapes:
    - Top-level ``agentMessage`` field (current App Server projection)
    - Nested ``items[]`` with ``type: "agentMessage"`` (legacy projection)
    """

    agent_message = raw_turn.get("agentMessage")
    if isinstance(agent_message, str):
        return agent_message

    items = raw_turn.get("items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "agentMessage":
                continue
            text = item.get("text")
            if isinstance(text, str):
                return text
    return ""
