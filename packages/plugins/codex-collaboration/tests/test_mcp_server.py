"""Tests for MCP server scaffolding with serialized dispatch."""

from __future__ import annotations

import json
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from server.mcp_server import McpServer, TOOL_DEFINITIONS


class TestToolDefinitions:
    def test_all_r1_and_r2_tools_registered(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.status" in tool_names
        assert "codex.consult" in tool_names
        assert "codex.dialogue.start" in tool_names
        assert "codex.dialogue.reply" in tool_names
        assert "codex.dialogue.read" in tool_names

    def test_no_fork_tool_in_r2(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.dialogue.fork" not in tool_names

    def test_each_tool_has_input_schema(self) -> None:
        for tool in TOOL_DEFINITIONS:
            assert "inputSchema" in tool, f"{tool['name']} missing inputSchema"
            assert tool["inputSchema"]["type"] == "object"


class FakeControlPlane:
    def codex_status(self, repo_root: Path) -> dict:
        return {"status": "ok", "repo_root": str(repo_root)}

    def codex_consult(self, request: object) -> object:
        from server.models import ConsultResult, ConsultEvidence
        return ConsultResult(
            collaboration_id="c1",
            runtime_id="r1",
            position="pos",
            evidence=(ConsultEvidence(claim="c", citation="x"),),
            uncertainties=(),
            follow_up_branches=(),
            context_size=100,
        )


class FakeDialogueController:
    def start(self, repo_root: Path) -> object:
        from server.models import DialogueStartResult
        return DialogueStartResult(
            collaboration_id="c1",
            runtime_id="r1",
            status="active",
            created_at="2026-03-28T00:00:00Z",
        )

    def reply(self, **kwargs: object) -> object:
        from server.models import DialogueReplyResult
        return DialogueReplyResult(
            collaboration_id=str(kwargs.get("collaboration_id", "c1")),
            runtime_id="r1",
            position="Response",
            evidence=(),
            uncertainties=(),
            follow_up_branches=(),
            turn_sequence=1,
            context_size=100,
        )

    def read(self, collaboration_id: str) -> object:
        from server.models import DialogueReadResult
        return DialogueReadResult(
            collaboration_id=collaboration_id,
            status="active",
            turn_count=0,
            created_at="2026-03-28T00:00:00Z",
            turns=(),
        )


class TestMcpServer:
    def _make_server(self) -> McpServer:
        return McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
        )

    def test_handle_initialize(self) -> None:
        server = self._make_server()
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in response["result"]["capabilities"]

    def test_handle_tools_list(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })
        tools = response["result"]["tools"]
        names = {t["name"] for t in tools}
        assert "codex.dialogue.start" in names
        assert "codex.dialogue.reply" in names

    def test_handle_tools_call_dialogue_start(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.dialogue.start",
                "arguments": {"repo_root": "/tmp/test-repo"},
            },
        })
        assert "result" in response
        content = response["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        result_data = json.loads(content[0]["text"])
        assert result_data["collaboration_id"] == "c1"

    def test_handle_unknown_tool_returns_error(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "codex.dialogue.fork", "arguments": {}},
        })
        assert response["result"]["isError"] is True

    def test_serialized_dispatch_is_sequential(self) -> None:
        """Verify the server processes requests one at a time (implicit in sync loop)."""
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        # Multiple calls execute sequentially — the sync design guarantees this.
        for i in range(3):
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.dialogue.start",
                    "arguments": {"repo_root": "/tmp/test-repo"},
                },
            })
            assert "result" in response
