"""Tests for MCP server scaffolding with serialized dispatch."""

from __future__ import annotations

import json
from pathlib import Path

from server.dialogue import CommittedTurnFinalizationError, CommittedTurnParseError
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
        self.last_explicit_posture: str | None = None
        self.last_explicit_turn_budget: int | None = None

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(
        self,
        repo_root: Path,
        *,
        profile_name: str | None = None,
        explicit_posture: str | None = None,
        explicit_turn_budget: int | None = None,
    ) -> object:
        from server.models import DialogueStartResult

        self.last_explicit_posture = explicit_posture
        self.last_explicit_turn_budget = explicit_turn_budget
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

    def start(
        self,
        repo_root: Path,
        *,
        profile_name: str | None = None,
        explicit_posture: str | None = None,
        explicit_turn_budget: int | None = None,
    ) -> object:
        from server.models import DialogueStartResult

        self.last_explicit_posture = explicit_posture
        self.last_explicit_turn_budget = explicit_turn_budget
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


class FakeDialogueControllerWithFinalizationError:
    """Dialogue controller that raises CommittedTurnFinalizationError on reply."""

    def __init__(self) -> None:
        self.startup_called = False

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(
        self,
        repo_root: Path,
        *,
        profile_name: str | None = None,
        explicit_posture: str | None = None,
        explicit_turn_budget: int | None = None,
    ) -> object:
        from server.models import DialogueStartResult

        self.last_explicit_posture = explicit_posture
        self.last_explicit_turn_budget = explicit_turn_budget
        return DialogueStartResult(
            collaboration_id="c1",
            runtime_id="r1",
            status="active",
            created_at="2026-03-28T00:00:00Z",
        )

    def reply(self, **kwargs: object) -> object:
        raise CommittedTurnFinalizationError(
            "Reply turn committed but local finalization failed: disk full. "
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
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in response["result"]["capabilities"]

    def test_handle_tools_list(self) -> None:
        server = self._make_server()
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
        )
        tools = response["result"]["tools"]
        names = {t["name"] for t in tools}
        assert "codex.dialogue.start" in names
        assert "codex.dialogue.reply" in names

    def test_handle_tools_call_dialogue_start(self) -> None:
        server = self._make_server()
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "codex.dialogue.start",
                    "arguments": {"repo_root": "/tmp/test-repo"},
                },
            }
        )
        assert "result" in response
        content = response["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        result_data = json.loads(content[0]["text"])
        assert result_data["collaboration_id"] == "c1"

    def test_dialogue_start_forwards_explicit_posture(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.dialogue.start",
                    "arguments": {
                        "repo_root": "/tmp/test-repo",
                        "posture": "adversarial",
                        "turn_budget": 6,
                    },
                },
            }
        )
        assert controller.last_explicit_posture == "adversarial"
        assert controller.last_explicit_turn_budget == 6

    def test_dialogue_start_omitted_overrides_forward_none(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.dialogue.start",
                    "arguments": {"repo_root": "/tmp/test-repo"},
                },
            }
        )
        assert controller.last_explicit_posture is None
        assert controller.last_explicit_turn_budget is None

    def test_dialogue_start_schema_has_posture_and_turn_budget(self) -> None:
        start_tool = next(
            t for t in TOOL_DEFINITIONS if t["name"] == "codex.dialogue.start"
        )
        props = start_tool["inputSchema"]["properties"]
        assert "posture" in props
        assert props["posture"]["type"] == "string"
        assert "enum" in props["posture"]
        assert "turn_budget" in props
        assert props["turn_budget"]["type"] == "integer"

    def test_handle_unknown_tool_returns_error(self) -> None:
        server = self._make_server()
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "codex.dialogue.fork", "arguments": {}},
            }
        )
        assert response["result"]["isError"] is True

    def test_serialized_dispatch_is_sequential(self) -> None:
        """Verify the server processes requests one at a time (implicit in sync loop)."""
        server = self._make_server()
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        # Multiple calls execute sequentially — the sync design guarantees this.
        for i in range(3):
            response = server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": "tools/call",
                    "params": {
                        "name": "codex.dialogue.start",
                        "arguments": {"repo_root": "/tmp/test-repo"},
                    },
                }
            )
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

            def start(
                self,
                repo_root: Path,
                *,
                profile_name: str | None = None,
                explicit_posture: str | None = None,
                explicit_turn_budget: int | None = None,
            ) -> object:
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
        assert (
            "no dialogue controller" in response["result"]["content"][0]["text"].lower()
        )

    def test_status_works_without_dialogue(self) -> None:
        """codex.status works when no dialogue controller is configured."""
        server = McpServer(control_plane=FakeControlPlane())
        server.handle_request(self._init_request())
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.status",
                    "arguments": {"repo_root": "/tmp/test-repo"},
                },
            }
        )
        assert "result" in response
        assert "isError" not in response["result"]
        result_data = json.loads(response["result"]["content"][0]["text"])
        assert result_data["status"] == "ok"

    def test_consult_works_without_dialogue(self) -> None:
        """codex.consult works when no dialogue controller is configured."""
        server = McpServer(control_plane=FakeControlPlane())
        server.handle_request(self._init_request())
        response = server.handle_request(
            {
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
            }
        )
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
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        response = server.handle_request(
            {
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
            }
        )

        assert response["result"]["isError"] is True
        error_text = response["result"]["content"][0]["text"]
        assert "turn committed" in error_text.lower()
        assert "codex.dialogue.read" in error_text

    def test_mcp_surfaces_committed_turn_finalization_guidance(self) -> None:
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueControllerWithFinalizationError(),
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test"},
                },
            }
        )
        response = server.handle_request(
            {
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
            }
        )

        assert response["result"]["isError"] is True
        error_text = response["result"]["content"][0]["text"]
        assert "turn committed" in error_text.lower()
        assert "codex.dialogue.read" in error_text


class TestDelegateToolRegistration:
    def test_delegate_start_tool_registered(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.delegate.start" in tool_names

    def test_delegate_start_input_schema_requires_repo_root_and_objective(self) -> None:
        schema = next(
            t["inputSchema"]
            for t in TOOL_DEFINITIONS
            if t["name"] == "codex.delegate.start"
        )
        assert schema["type"] == "object"
        assert "repo_root" in schema["required"]
        assert "objective" in schema["required"]


class FakeDelegationController:
    def __init__(self) -> None:
        self.start_calls: list[dict] = []

    def start(
        self, *, repo_root: Path, base_commit: str | None = None, objective: str = ""
    ) -> object:
        from server.models import DelegationJob

        self.start_calls.append(
            {"repo_root": repo_root, "base_commit": base_commit, "objective": objective}
        )
        return DelegationJob(
            job_id="job-x",
            runtime_id="rt-x",
            collaboration_id="collab-x",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class TestDelegateDispatch:
    def test_delegate_start_dispatch_returns_job_fields(self) -> None:
        controller = FakeDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert "isError" not in response["result"]
        content = response["result"]["content"][0]["text"]
        payload = json.loads(content)
        assert payload["job_id"] == "job-x"
        assert payload["status"] == "queued"
        assert controller.start_calls == [
            {
                "repo_root": Path("/some/repo"),
                "base_commit": None,
                "objective": "Fix bug",
            }
        ]

    def test_delegate_start_forwards_optional_base_commit(self) -> None:
        controller = FakeDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {
                        "repo_root": "/some/repo",
                        "objective": "Fix bug",
                        "base_commit": "explicit-sha",
                    },
                },
            }
        )
        assert controller.start_calls[0]["base_commit"] == "explicit-sha"

    def test_delegate_start_returns_busy_response_payload(self) -> None:
        from server.models import JobBusyResponse

        class _BusyController:
            def start(
                self,
                *,
                repo_root: Path,
                base_commit: str | None = None,
                objective: str = "",
            ) -> object:
                return JobBusyResponse(
                    busy=True,
                    active_job_id="job-1",
                    active_job_status="running",
                    detail="Active.",
                )

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=_BusyController(),
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert "isError" not in response["result"]
        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload["busy"] is True
        assert payload["active_job_id"] == "job-1"


class _RecordingDelegationController:
    """Records recover_startup + start invocations for wiring tests."""

    def __init__(self) -> None:
        self.recover_startup_calls = 0
        self.start_calls: list[dict] = []

    def recover_startup(self) -> None:
        self.recover_startup_calls += 1

    def start(
        self, *, repo_root: Path, base_commit: str | None = None, objective: str = ""
    ) -> object:
        from server.models import DelegationJob

        self.start_calls.append(
            {"repo_root": repo_root, "base_commit": base_commit, "objective": objective}
        )
        return DelegationJob(
            job_id="job-rec",
            runtime_id="rt-rec",
            collaboration_id="collab-rec",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class _FailOnceDelegationController:
    """Controller that raises from ``recover_startup`` a configurable number of
    times before succeeding. Used to prove retry-on-recovery-failure semantics
    of the lazy factory path: if ``recover_startup`` raises, the controller
    must NOT be pinned, and the factory must be re-invoked on the next
    dispatch.
    """

    def __init__(self, *, recovery_fails_remaining: int = 0) -> None:
        self._recovery_fails_remaining = recovery_fails_remaining
        self.recover_startup_calls = 0
        self.start_calls: list[dict] = []

    def recover_startup(self) -> None:
        self.recover_startup_calls += 1
        if self._recovery_fails_remaining > 0:
            self._recovery_fails_remaining -= 1
            raise RuntimeError("simulated transient recovery failure")

    def start(
        self, *, repo_root: Path, base_commit: str | None = None, objective: str = ""
    ) -> object:
        from server.models import DelegationJob

        self.start_calls.append(
            {"repo_root": repo_root, "base_commit": base_commit, "objective": objective}
        )
        return DelegationJob(
            job_id="job-fail-once",
            runtime_id="rt-fail-once",
            collaboration_id="collab-fail-once",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class TestDelegationRecoveryWiring:
    """Recovery is wired at TWO call sites — eager (startup) and lazy
    (_ensure_delegation_controller). Production deploys via factory, so the
    lazy path is the load-bearing one. Both are tested below."""

    def test_ensure_delegation_controller_runs_recover_startup_on_first_dispatch(
        self,
    ) -> None:
        """Lazy factory path happy case: ``recover_startup`` runs once on first
        dispatch; subsequent dispatches reuse the pinned controller without
        re-running recovery. The pin-only-after-successful-recovery retry
        ordering invariant is covered separately by
        ``test_ensure_delegation_controller_does_not_pin_on_recovery_failure``.
        """
        controller = _RecordingDelegationController()

        def factory() -> _RecordingDelegationController:
            return controller

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_factory=factory,
        )
        # First dispatch triggers _ensure_delegation_controller → recover_startup → pin.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert controller.recover_startup_calls == 1
        # Second dispatch reuses the pinned controller — recover_startup is NOT re-called.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert controller.recover_startup_calls == 1
        assert len(controller.start_calls) == 2

    def test_ensure_delegation_controller_does_not_pin_on_recovery_failure(
        self,
    ) -> None:
        """Lazy factory path retry safety: when ``recover_startup`` raises,
        the controller is NOT pinned, ``start()`` is NOT reached, and a
        subsequent dispatch retries by invoking the factory a second time
        rather than reusing a poisoned controller. Protects the ordering
        invariant named in ``_ensure_delegation_controller``'s docstring:
        'Pin only after recovery succeeds — transient failures allow retry.'

        Proof shape (3 dispatches):
          1. First dispatch: recovery raises → error response; factory called
             once; start() not reached; controller not pinned.
          2. Second dispatch: factory invoked AGAIN (proves no pin on first
             call); new controller's recovery succeeds; start() runs.
          3. Third dispatch: factory NOT re-invoked (proves pin happened
             after successful recovery on second dispatch); start() runs
             on the pinned controller.
        """
        factory_controllers: list[_FailOnceDelegationController] = []

        def factory() -> _FailOnceDelegationController:
            # First factory call: recovery fails once. Subsequent calls: no failures.
            controller = _FailOnceDelegationController(
                recovery_fails_remaining=1 if not factory_controllers else 0
            )
            factory_controllers.append(controller)
            return controller

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_factory=factory,
        )

        # Dispatch 1: recovery raises → error response; start() not reached.
        response1 = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert response1["result"]["isError"] is True
        assert len(factory_controllers) == 1
        assert factory_controllers[0].recover_startup_calls == 1
        assert (
            factory_controllers[0].start_calls == []
        )  # start not reached on failed recovery

        # Dispatch 2: factory re-invoked (proves no pin on first call);
        # second controller's recovery succeeds; start() runs.
        response2 = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert "isError" not in response2["result"]
        assert len(factory_controllers) == 2  # factory re-invoked — retry, not reuse
        assert factory_controllers[1].recover_startup_calls == 1
        assert len(factory_controllers[1].start_calls) == 1

        # Dispatch 3: NOW pinned — factory NOT re-invoked.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo", "objective": "Fix bug"},
                },
            }
        )
        assert len(factory_controllers) == 2  # still 2 — second controller pinned
        assert len(factory_controllers[1].start_calls) == 2

    def test_startup_runs_delegation_recover_startup_when_controller_provided_directly(
        self,
    ) -> None:
        """Eager session-init path: startup() fires recover_startup once."""
        controller = _RecordingDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        server.startup()
        assert controller.recover_startup_calls == 1
        # Idempotent — second startup call is a no-op.
        server.startup()
        assert controller.recover_startup_calls == 1


class FakeDelegationControllerWithPoll:
    def __init__(self) -> None:
        self.startup_called = False

    def recover_startup(self) -> None:
        self.startup_called = True

    def poll(self, *, job_id: str) -> object:
        from server.models import DelegationJob, DelegationPollResult

        return DelegationPollResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="pending",
                status="completed",
            ),
        )


def test_handle_tools_call_delegate_poll() -> None:
    controller = FakeDelegationControllerWithPoll()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": "job-1"},
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["job"]["job_id"] == "job-1"
    assert payload["job"]["promotion_state"] == "pending"


class FakeDelegationControllerWithDecide:
    def __init__(self) -> None:
        self.startup_called = False
        self.last_decide_args: dict[str, object] | None = None

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(self, **kwargs: object) -> object:
        from server.models import DelegationJob

        return DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="abc123",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="completed",
        )

    def decide(
        self,
        *,
        job_id: str,
        request_id: str,
        decision: str,
        answers: dict[str, tuple[str, ...]] | None = None,
    ) -> object:
        from server.models import DelegationDecisionResult, DelegationJob

        self.last_decide_args = {
            "job_id": job_id,
            "request_id": request_id,
            "decision": decision,
            "answers": answers,
        }
        return DelegationDecisionResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="pending",
                status="completed",
            ),
            decision=decision,
            resumed=(decision == "approve"),
        )


def test_delegate_poll_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.poll" in tool_names


def test_delegate_decide_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.decide" in tool_names


def test_handle_tools_call_delegate_decide() -> None:
    controller = FakeDelegationControllerWithDecide()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": "job-1",
                    "request_id": "req-1",
                    "decision": "approve",
                    "answers": {"q1": {"answers": ["yes"]}},
                },
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["decision"] == "approve"
    assert payload["resumed"] is True
    assert controller.last_decide_args == {
        "job_id": "job-1",
        "request_id": "req-1",
        "decision": "approve",
        "answers": {"q1": ("yes",)},
    }


def _decide_with_answers(answers: object) -> dict[str, object]:
    """Helper: send a codex.delegate.decide call with the given answers payload."""
    controller = FakeDelegationControllerWithDecide()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )
    return server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": "job-1",
                    "request_id": "req-1",
                    "decision": "approve",
                    "answers": answers,
                },
            },
        }
    )


def test_decide_rejects_non_dict_answers() -> None:
    response = _decide_with_answers(["not", "a", "dict"])
    assert response["result"]["isError"] is True
    assert "must be an object" in response["result"]["content"][0]["text"]


def test_decide_rejects_malformed_answer_entry() -> None:
    response = _decide_with_answers({"q1": "not-an-entry-dict"})
    assert response["result"]["isError"] is True
    assert "must have shape" in response["result"]["content"][0]["text"]


def test_decide_rejects_non_string_answer_values() -> None:
    response = _decide_with_answers({"q1": {"answers": [123, True]}})
    assert response["result"]["isError"] is True
    assert "must be strings" in response["result"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# codex.delegate.promote and codex.delegate.discard
# ---------------------------------------------------------------------------


def test_delegate_promote_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.promote" in tool_names


def test_delegate_discard_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.discard" in tool_names


class FakeDelegationControllerWithPromoteDiscard:
    def __init__(self) -> None:
        self.startup_called = False
        self.last_promote_job_id: str | None = None
        self.last_discard_job_id: str | None = None

    def recover_startup(self) -> None:
        self.startup_called = True

    def promote(self, *, job_id: str) -> object:
        from server.models import DelegationJob, PromotionResult

        self.last_promote_job_id = job_id
        return PromotionResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="verified",
                status="completed",
            ),
            artifact_hash="sha256-abc",
            changed_files=("file_a.py",),
            stale_advisory_context=False,
        )

    def discard(self, *, job_id: str) -> object:
        from server.models import DelegationJob, DiscardResult

        self.last_discard_job_id = job_id
        return DiscardResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="discarded",
                status="completed",
            ),
        )


def test_handle_tools_call_delegate_promote() -> None:
    controller = FakeDelegationControllerWithPromoteDiscard()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.promote",
                "arguments": {"job_id": "job-promote-1"},
            },
        }
    )

    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["job"]["job_id"] == "job-promote-1"
    assert payload["job"]["promotion_state"] == "verified"
    assert controller.last_promote_job_id == "job-promote-1"


def test_handle_tools_call_delegate_discard() -> None:
    controller = FakeDelegationControllerWithPromoteDiscard()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.discard",
                "arguments": {"job_id": "job-discard-1"},
            },
        }
    )

    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["job"]["job_id"] == "job-discard-1"
    assert payload["job"]["promotion_state"] == "discarded"
    assert controller.last_discard_job_id == "job-discard-1"


def test_delegate_promote_returns_promote_policy() -> None:
    """promote returns PromotionResult or PromotionRejectedResponse, not an error."""
    from server.models import PromotionRejectedResponse

    class _RejectedController:
        def recover_startup(self) -> None:
            pass

        def promote(self, *, job_id: str) -> object:
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_completed",
                detail="Job is not in a promotable state.",
                job_id=job_id,
            )

    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=_RejectedController(),
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.promote",
                "arguments": {"job_id": "job-rej"},
            },
        }
    )

    # Rejection is a typed response, not an MCP-level error
    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["rejected"] is True
    assert payload["job_id"] == "job-rej"


def test_delegate_discard_returns_discard_policy() -> None:
    """discard returns DiscardResult or DiscardRejectedResponse, not an error."""
    from server.models import DiscardRejectedResponse

    class _RejectedController:
        def recover_startup(self) -> None:
            pass

        def discard(self, *, job_id: str) -> object:
            return DiscardRejectedResponse(
                rejected=True,
                reason="job_not_discardable",
                detail="Job is not in a discardable state.",
                job_id=job_id,
            )

    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=_RejectedController(),
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.discard",
                "arguments": {"job_id": "job-rej"},
            },
        }
    )

    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["rejected"] is True
    assert payload["job_id"] == "job-rej"
