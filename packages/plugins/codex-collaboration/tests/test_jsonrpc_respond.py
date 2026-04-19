"""Tests for JsonRpcClient server-request response support."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from server.jsonrpc_client import JsonRpcClient


class TestRespond:
    """Tests for JsonRpcClient.respond()."""

    def test_respond_writes_jsonrpc_response_to_stdin(self) -> None:
        """respond() sends a JSON-RPC 2.0 response with the given request_id and result."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        client.respond("req-42", {"decision": "cancel"})

        written = mock_stdin.write.call_args[0][0]
        payload = json.loads(written.strip())
        assert payload == {
            "jsonrpc": "2.0",
            "id": "req-42",
            "result": {"decision": "cancel"},
        }
        mock_stdin.flush.assert_called_once()

    def test_respond_with_integer_request_id(self) -> None:
        """respond() preserves integer request IDs (JSON-RPC allows string or int)."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        client.respond(7, {"permissions": {}})

        written = mock_stdin.write.call_args[0][0]
        payload = json.loads(written.strip())
        assert payload["id"] == 7

    def test_respond_raises_if_not_started(self) -> None:
        """respond() raises RuntimeError if called before start()."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))

        with pytest.raises(RuntimeError, match="not started"):
            client.respond("req-1", {})

    def test_respond_raises_on_broken_pipe(self) -> None:
        """respond() wraps BrokenPipeError with context."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_stdin.write.side_effect = BrokenPipeError()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        with pytest.raises(RuntimeError, match="broken stdin pipe"):
            client.respond("req-1", {})
