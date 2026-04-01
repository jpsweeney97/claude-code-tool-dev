from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.codex_compat import (
    CompatCheckResult,
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    SemVer,
)
from server.control_plane import ControlPlane
from server.journal import OperationJournal
from server.models import (
    AccountState,
    ConsultRequest,
    RepoIdentity,
    RuntimeHandshake,
    StaleAdvisoryContextMarker,
    TurnExecutionResult,
)


class FakeRuntimeSession:
    def __init__(
        self,
        *,
        auth_status: str = "authenticated",
        auth_status_sequence: tuple[str, ...] | None = None,
        requires_openai_auth: bool = True,
        initialize_error: Exception | None = None,
        account_read_error: Exception | None = None,
        run_turn_error: Exception | None = None,
        agent_message: str | None = None,
    ) -> None:
        self.auth_status = auth_status
        self.auth_status_sequence = (
            list(auth_status_sequence) if auth_status_sequence is not None else None
        )
        self.requires_openai_auth = requires_openai_auth
        self.initialize_error = initialize_error
        self.account_read_error = account_read_error
        self.run_turn_error = run_turn_error
        self.agent_message = agent_message or json.dumps(
            {
                "position": "Consulted via thr-start",
                "evidence": [
                    {
                        "claim": "The repo contains the requested file",
                        "citation": "focus.py:1",
                    }
                ],
                "uncertainties": ["No runtime side effects were executed"],
                "follow_up_branches": ["Inspect adjacent tests"],
            }
        )
        self.closed = False
        self.started_threads: list[str] = []
        self.resumed_threads: list[str] = []
        self.last_prompt_text: str | None = None
        self.last_output_schema: dict[str, object] | None = None
        self.last_effort: str | None = None
        self.read_account_calls = 0
        self.run_turn_calls = 0
        self.completed_turn_count: int = 0
        self.read_thread_response: dict | None = None

    def initialize(self) -> RuntimeHandshake:
        if self.initialize_error is not None:
            raise self.initialize_error
        return RuntimeHandshake(
            codex_home="/tmp/codex-home",
            platform_family="unix",
            platform_os="macos",
            user_agent="codex-app-server/0.117.0",
        )

    def read_account(self) -> AccountState:
        if self.account_read_error is not None:
            raise self.account_read_error
        self.read_account_calls += 1
        if self.auth_status_sequence is not None and self.auth_status_sequence:
            current_auth_status = self.auth_status_sequence.pop(0)
        else:
            current_auth_status = self.auth_status
        return AccountState(
            auth_status=current_auth_status,  # type: ignore[arg-type]
            account_type="chatgpt" if current_auth_status == "authenticated" else None,
            requires_openai_auth=self.requires_openai_auth,
        )

    def start_thread(self) -> str:
        self.started_threads.append("start")
        return "thr-start"

    def fork_thread(self, thread_id: str) -> str:
        self.started_threads.append(f"fork:{thread_id}")
        return "thr-forked"

    def run_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        output_schema: dict[str, object],
        effort: str | None = None,
    ) -> TurnExecutionResult:
        if self.run_turn_error is not None:
            raise self.run_turn_error
        self.run_turn_calls += 1
        self.completed_turn_count += 1
        self.last_prompt_text = prompt_text
        self.last_output_schema = output_schema
        self.last_effort = effort  # Capture for assertion in profile tests
        return TurnExecutionResult(
            turn_id="turn-1",
            agent_message=self.agent_message.replace("thr-start", thread_id),
        )

    def close(self) -> None:
        self.closed = True

    def read_thread(self, thread_id: str) -> dict:
        if self.read_thread_response is not None:
            return self.read_thread_response
        turns = [
            {"id": f"turn-{i + 1}", "status": "completed"}
            for i in range(self.completed_turn_count)
        ]
        return {
            "thread": {
                "id": thread_id,
                "turns": turns,
            },
        }

    def resume_thread(self, thread_id: str) -> str:
        self.resumed_threads.append(thread_id)
        return thread_id


def _compat_result() -> CompatCheckResult:
    return CompatCheckResult.from_version_check(
        codex_version=SemVer.parse("0.117.0"),
        available_methods=REQUIRED_METHODS | OPTIONAL_METHODS,
    )


def _repo_identity(repo_root: Path) -> RepoIdentity:
    return RepoIdentity(repo_root=repo_root, branch="main", head="head-123")


def _failed_compat_result() -> CompatCheckResult:
    return CompatCheckResult(
        passed=False,
        codex_version=SemVer.parse("0.117.0"),
        available_methods=frozenset(),
        errors=("missing required methods",),
    )


class _CompatSequence:
    def __init__(self, *results: CompatCheckResult) -> None:
        self._results = list(results)

    def __call__(self) -> CompatCheckResult:
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


def test_codex_status_bootstraps_advisory_runtime(tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: "uuid-1",
    )

    status = plane.codex_status(tmp_path)

    assert status["codex_version"] == "0.117.0"
    assert status["app_server_version"] == "codex-app-server/0.117.0"
    assert status["auth_status"] == "authenticated"
    assert status["advisory_runtime"] == {
        "id": "uuid-1",
        "policy_fingerprint": status["advisory_runtime"]["policy_fingerprint"],
        "thread_count": 0,
        "uptime": 0,
    }
    assert status["required_methods"]["thread/start"] is True
    assert status["optional_methods"]["turn/steer"] is True


def test_codex_status_invalidates_cached_runtime_on_compat_drift(
    tmp_path: Path,
) -> None:
    session = FakeRuntimeSession()
    compat_checker = _CompatSequence(_compat_result(), _failed_compat_result())
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=compat_checker,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: "uuid-1",
    )

    first_status = plane.codex_status(tmp_path)
    second_status = plane.codex_status(tmp_path)

    assert first_status["advisory_runtime"] is not None
    assert second_status["advisory_runtime"] is None
    assert second_status["required_methods"]["thread/start"] is False
    assert "compatibility checks failed" in second_status["errors"][0]
    assert session.closed is True


def test_codex_status_reports_missing_auth_without_runtime(tmp_path: Path) -> None:
    session = FakeRuntimeSession(auth_status="missing")
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    status = plane.codex_status(tmp_path)

    assert status["auth_status"] == "missing"
    assert status["advisory_runtime"] is None
    assert status["app_server_version"] == "codex-app-server/0.117.0"
    assert "advisory auth unavailable" in status["errors"][0]
    assert session.closed is True


def test_codex_status_probes_initialize_failure(tmp_path: Path) -> None:
    session = FakeRuntimeSession(initialize_error=RuntimeError("initialize boom"))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    status = plane.codex_status(tmp_path)

    assert status["advisory_runtime"] is None
    assert "initialize failed" in status["errors"][0]
    assert session.closed is True


def test_codex_consult_returns_structured_result_and_audits_context_size(
    tmp_path: Path,
) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
    )

    assert result.collaboration_id == "collab-1"
    assert result.runtime_id == "runtime-1"
    assert result.position == "Consulted via thr-start"
    assert result.evidence[0].citation == "focus.py:1"
    assert result.context_size > 0
    audit_path = plugin_data / "audit" / "events.jsonl"
    audit_record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert audit_record["action"] == "consult"
    assert audit_record["context_size"] == result.context_size
    assert session.last_output_schema is not None
    assert session.read_account_calls == 1


def test_codex_consult_fails_closed_on_compat_failure(tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_failed_compat_result,
        repo_identity_loader=_repo_identity,
    )

    with pytest.raises(RuntimeError, match="compatibility checks failed"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="Review focus.py",
            )
        )
    assert session.closed is True


def test_codex_consult_fails_closed_on_initialize_failure(tmp_path: Path) -> None:
    session = FakeRuntimeSession(initialize_error=RuntimeError("initialize boom"))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    with pytest.raises(RuntimeError, match="initialize failed"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="Review focus.py",
            )
        )
    assert session.closed is True


def test_codex_consult_consumes_stale_marker_on_success(tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path.resolve()),
            promoted_head="old-head",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    _ = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py after promotion",
            explicit_paths=(Path("focus.py"),),
        )
    )

    assert session.last_prompt_text is not None
    assert "Most recent promoted HEAD: old-head" in session.last_prompt_text
    assert journal.load_stale_marker(tmp_path) is None


def test_codex_consult_invalidates_cached_runtime_after_turn_failure(
    tmp_path: Path,
) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    failing_session = FakeRuntimeSession(run_turn_error=RuntimeError("turn boom"))
    succeeding_session = FakeRuntimeSession()
    sessions = iter((failing_session, succeeding_session))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: next(sessions),
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(
            ("runtime-1", "runtime-2", "collab-2", "event-2", "outcome-2")
        ).__next__,
    )

    with pytest.raises(RuntimeError, match="turn boom"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="First consult fails",
                explicit_paths=(Path("focus.py"),),
            )
        )
    assert failing_session.closed is True

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Second consult uses a fresh runtime",
            explicit_paths=(Path("focus.py"),),
        )
    )
    assert result.runtime_id == "runtime-2"
    assert succeeding_session.closed is False


def test_codex_consult_invalidates_cached_runtime_after_parse_failure(
    tmp_path: Path,
) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    failing_session = FakeRuntimeSession(agent_message="not-json")
    succeeding_session = FakeRuntimeSession()
    sessions = iter((failing_session, succeeding_session))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: next(sessions),
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(
            ("runtime-1", "runtime-2", "collab-2", "event-2", "outcome-2")
        ).__next__,
    )

    with pytest.raises(ValueError, match="expected JSON object"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="Malformed consult result",
                explicit_paths=(Path("focus.py"),),
            )
        )
    assert failing_session.closed is True

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Fresh runtime after malformed output",
            explicit_paths=(Path("focus.py"),),
        )
    )
    assert result.runtime_id == "runtime-2"


def test_codex_consult_revalidates_cached_runtime_auth_before_reuse(
    tmp_path: Path,
) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession(
        auth_status_sequence=("authenticated", "missing"),
    )
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
    )

    first_result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="First consult succeeds",
            explicit_paths=(Path("focus.py"),),
        )
    )

    assert first_result.runtime_id == "runtime-1"
    with pytest.raises(RuntimeError, match="advisory auth unavailable"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="Second consult must fail closed",
                explicit_paths=(Path("focus.py"),),
            )
        )
    assert session.closed is True
    assert session.run_turn_calls == 1


def test_codex_consult_emits_outcome_record(tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
    )

    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    assert outcomes_path.exists()
    record = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
    assert record["outcome_type"] == "consult"
    assert record["collaboration_id"] == "collab-1"
    assert record["runtime_id"] == "runtime-1"
    assert record["context_size"] == result.context_size
    assert record["turn_id"] is not None
    assert record["policy_fingerprint"] is not None
    assert record["repo_root"] == str(tmp_path.resolve())
    assert record["turn_sequence"] is None


def test_codex_consult_failure_does_not_emit_outcome(tmp_path: Path) -> None:
    session = FakeRuntimeSession(run_turn_error=RuntimeError("turn boom"))
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        journal=journal,
    )

    with pytest.raises(RuntimeError, match="turn boom"):
        plane.codex_consult(ConsultRequest(repo_root=tmp_path, objective="Should fail"))

    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    assert (
        not outcomes_path.exists()
        or outcomes_path.read_text(encoding="utf-8").strip() == ""
    )


def test_codex_consult_suppresses_audit_failure(tmp_path: Path, capsys) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    def _boom(event: object) -> None:
        raise OSError("audit boom")

    journal.append_audit_event = _boom  # type: ignore[method-assign]

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
    )

    assert result.collaboration_id == "collab-1"
    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    assert outcomes_path.exists()
    assert "codex_consult_audit failed: audit boom" in capsys.readouterr().err


def test_codex_consult_suppresses_outcome_failure(tmp_path: Path, capsys) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    def _boom(record: object) -> None:
        raise OSError("outcome boom")

    journal.append_outcome = _boom  # type: ignore[method-assign]

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
    )

    assert result.collaboration_id == "collab-1"
    audit_path = plugin_data / "audit" / "events.jsonl"
    assert audit_path.exists()
    assert "codex_consult_outcome failed: outcome boom" in capsys.readouterr().err


def test_codex_consult_rejects_network_widening_in_r1(tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    with pytest.raises(RuntimeError, match="widening is not implemented in R1"):
        plane.codex_consult(
            ConsultRequest(
                repo_root=tmp_path,
                objective="Review with web access",
                network_access=True,
            )
        )


def test_get_advisory_runtime_returns_cached_runtime(tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: "uuid-1",
    )

    runtime = plane.get_advisory_runtime(tmp_path)

    assert runtime is not None
    assert runtime.runtime_id == "uuid-1"
    assert runtime.session is session


def test_get_advisory_runtime_raises_on_failure(tmp_path: Path) -> None:
    session = FakeRuntimeSession(initialize_error=RuntimeError("init boom"))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    with pytest.raises(RuntimeError, match="initialize failed"):
        plane.get_advisory_runtime(tmp_path)


def test_invalidate_runtime_drops_cache(tmp_path: Path) -> None:
    session1 = FakeRuntimeSession()
    session2 = FakeRuntimeSession()
    sessions = iter((session1, session2))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: next(sessions),
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(("rt-1", "rt-2")).__next__,
    )

    rt1 = plane.get_advisory_runtime(tmp_path)
    assert rt1.runtime_id == "rt-1"

    plane.invalidate_runtime(tmp_path)
    assert session1.closed is True

    rt2 = plane.get_advisory_runtime(tmp_path)
    assert rt2.runtime_id == "rt-2"
