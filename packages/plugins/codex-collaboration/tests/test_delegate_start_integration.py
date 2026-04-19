"""Smoke tests for production wiring of codex.delegate.start."""

from __future__ import annotations

from pathlib import Path


def test_delegation_factory_builds_controller(tmp_path: Path, monkeypatch) -> None:
    # Ensure scripts dir is importable
    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    # Publish a fake session id.
    (plugin_data / "session_id").write_text("sess-smoke-1")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    from server.delegation_controller import DelegationController

    assert isinstance(controller, DelegationController)


def test_delegation_factory_passes_shared_runtime_registry(
    tmp_path: Path, monkeypatch
) -> None:
    """A single registry is shared across controller instances from one factory.

    The registry is constructed in main() and passed into the factory.
    The factory is called at most once per McpServer instance (lazy pin),
    so sharing the registry across callers within one McpServer is the
    correct default — it is the live view of THIS plugin instance.
    """

    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    (plugin_data / "session_id").write_text("sess-smoke-2")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    # The registry the controller received must be the same object main()
    # constructed — otherwise main()'s reference cannot observe registered
    # runtimes later.
    assert controller._runtime_registry is runtime_registry  # type: ignore[attr-defined]
