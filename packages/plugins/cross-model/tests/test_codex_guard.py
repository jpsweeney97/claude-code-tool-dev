"""Regression tests for codex_guard hook after credential_scan extraction."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.codex_guard import handle_pre, handle_post


def _make_pre_data(prompt: str, tool: str = "mcp__codex") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "session_id": "test-session",
        "tool_input": {"prompt": prompt},
    }


class TestHandlePre:
    """PreToolUse handler blocks on credentials."""

    @patch("scripts.codex_guard._append_log")
    def test_clean_prompt_allows(self, mock_log: object) -> None:
        assert handle_pre(_make_pre_data("fix the auth test")) == 0

    @patch("scripts.codex_guard._append_log")
    def test_aws_key_blocks(self, mock_log: object) -> None:
        assert handle_pre(_make_pre_data("key AKIAIOSFODNN7EXAMPLE")) == 2

    @patch("scripts.codex_guard._append_log")
    def test_broad_tier_allows(self, mock_log: object) -> None:
        """Broad tier is shadow-only, does not block."""
        assert handle_pre(_make_pre_data("password = mysecretvalue123")) == 0


class TestHandlePost:
    """PostToolUse handler always returns 0."""

    @patch("scripts.codex_guard._append_log")
    def test_always_allows(self, mock_log: object) -> None:
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {"content": "response"},
        }
        assert handle_post(data) == 0
