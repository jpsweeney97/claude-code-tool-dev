"""Tests for MCP server scaffolding with serialized dispatch."""

from __future__ import annotations

import json
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from server.dialogue import CommittedTurnParseError
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
    def __init__(self) -> None:
        self.startup_called = False

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(self, repo_root: Path, *, profile_name: str | None = None) -> object:
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


class FakeDialogueControllerWithParseError:
    """Dialogue controller that raises CommittedTurnParseError on reply."""
    def __init__(self) -> None:
        self.startup_called = False

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(self, repo_root: Path, *, profile_name: str | None = None) -> object:
        from server.models import DialogueStartResult
        return DialogueStartResult(
            collaboration_id="c1",
            runtime_id="r1",
            status="active",
            created_at="2026-03-28T00:00:00Z",
        )

    def reply(self, **kwargs: object) -> object:
        raise CommittedTurnParseError(
            "Reply turn committed but response parsing failed: bad json. "
            "The turn is durably recorded. Use codex.dialogue.read to "
            "inspect the committed turn. Blind retry will create a "
            "duplicate follow-up turn, not replay this one."
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


class TestStartup:
    def test_startup_calls_recover_startup(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.startup()
        assert controller.startup_called is True

    def test_startup_is_idempotent(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.startup()
        server.startup()  # second call should be a no-op
        assert controller.startup_called is True

    def test_startup_without_dialogue_controller_is_noop(self) -> None:
        """Startup completes when no dialogue controller is configured."""
        server = McpServer(control_plane=FakeControlPlane())
        server.startup()  # should not raise


class TestDeferredDialogueInit:
    """Lazy dialogue controller initialization via factory."""

    def _init_request(self) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        }

    def _dialogue_start_request(self, req_id: int = 1) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {
                "name": "codex.dialogue.start",
                "arguments": {"repo_root": "/tmp/test-repo"},
            },
        }

    def test_factory_called_on_first_dialogue_tool(self) -> None:
        """Factory is invoked exactly once on the first dialogue tool call."""
        call_count = 0
        controller = FakeDialogueController()

        def factory() -> FakeDialogueController:
            nonlocal call_count
            call_count += 1
            return controller

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_factory=factory,
        )
        server.handle_request(self._init_request())

        assert call_count == 0
        server.handle_request(self._dialogue_start_request())
        assert call_count == 1

    def test_factory_runs_recovery_on_init(self) -> None:
        """Lazy init calls recover_startup() on the created controller."""
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_factory=lambda: controller,
        )
        server.handle_request(self._init_request())
        server.handle_request(self._dialogue_start_request())
        assert controller.startup_called is True

    def test_factory_pinned_after_first_call(self) -> None:
        """Second dialogue call reuses the cached controller, does not call factory."""
        call_count = 0

        def factory() -> FakeDialogueController:
            nonlocal call_count
            call_count += 1
            return FakeDialogueController()

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_factory=factory,
        )
        server.handle_request(self._init_request())
        server.handle_request(self._dialogue_start_request(1))
        server.handle_request(self._dialogue_start_request(2))
        assert call_count == 1

    def test_transient_recovery_failure_allows_retry(self) -> None:
        """If recover_startup() fails, factory is retained and next call retries."""
        call_count = 0

        class TransientFailController:
            def __init__(self) -> None:
                self.startup_called = False

            def recover_startup(self) -> None:
                nonlocal call_count
                if call_count == 1:
                    raise RuntimeError("transient journal replay failure")
                self.startup_called = True

            def start(self, repo_root: Path, *, profile_name: str | None = None) -> object:
                from server.models import DialogueStartResult
                return DialogueStartResult(
                    collaboration_id="c1",
                    runtime_id="r1",
                    status="active",
                    created_at="2026-03-28T00:00:00Z",
                )

        def factory() -> TransientFailController:
            nonlocal call_count
            call_count += 1
            return TransientFailController()

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_factory=factory,
        )
        server.handle_request(self._init_request())

        # First call: factory builds controller, recovery fails, returns error
        resp1 = server.handle_request(self._dialogue_start_request(1))
        assert resp1["result"]["isError"] is True
        assert call_count == 1

        # Second call: factory invoked again, recovery succeeds, request completes
        resp2 = server.handle_request(self._dialogue_start_request(2))
        assert "isError" not in resp2["result"]
        assert call_count == 2
        result_data = json.loads(resp2["result"]["content"][0]["text"])
        assert result_data["collaboration_id"] == "c1"

    def test_no_controller_no_factory_returns_error(self) -> None:
        """Dialogue tool call without controller or factory returns MCP error."""
        server = McpServer(control_plane=FakeControlPlane())
        server.handle_request(self._init_request())
        response = server.handle_request(self._dialogue_start_request())
        assert response["result"]["isError"] is True
        assert "no dialogue controller" in response["result"]["content"][0]["text"].lower()

    def test_status_works_without_dialogue(self) -> None:
        """codex.status works when no dialogue controller is configured."""
        server = McpServer(control_plane=FakeControlPlane())
        server.handle_request(self._init_request())
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.status",
                "arguments": {"repo_root": "/tmp/test-repo"},
            },
        })
        assert "result" in response
        assert "isError" not in response["result"]
        result_data = json.loads(response["result"]["content"][0]["text"])
        assert result_data["status"] == "ok"

    def test_consult_works_without_dialogue(self) -> None:
        """codex.consult works when no dialogue controller is configured."""
        server = McpServer(control_plane=FakeControlPlane())
        server.handle_request(self._init_request())
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.consult",
                "arguments": {
                    "repo_root": "/tmp/test-repo",
                    "objective": "test question",
                },
            },
        })
        assert "result" in response
        assert "isError" not in response["result"]
        result_data = json.loads(response["result"]["content"][0]["text"])
        assert result_data["collaboration_id"] == "c1"


class TestCommittedTurnParseErrorSurfacing:
    def test_mcp_surfaces_committed_turn_parse_guidance(self) -> None:
        """MCP error text contains both 'turn committed' and 'codex.dialogue.read'."""
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueControllerWithParseError(),
        )
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.dialogue.reply",
                "arguments": {
                    "collaboration_id": "c1",
                    "objective": "test",
                },
            },
        })

        assert response["result"]["isError"] is True
        error_text = response["result"]["content"][0]["text"]
        assert "turn committed" in error_text.lower()
        assert "codex.dialogue.read" in error_text
