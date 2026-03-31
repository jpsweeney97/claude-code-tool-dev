"""Tests for plugin bootstrap wiring and session identity publication."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Bootstrap script is not a package module — import its functions directly.
_bootstrap_path = Path(__file__).resolve().parent.parent / "scripts" / "codex_runtime_bootstrap.py"
_hook_path = Path(__file__).resolve().parent.parent / "scripts" / "publish_session_id.py"


def _import_bootstrap():
    """Import bootstrap module from scripts/ path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("codex_runtime_bootstrap", _bootstrap_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestReadSessionId:
    """Tests for _read_session_id from the bootstrap script."""

    def test_reads_published_session_id(self, tmp_path: Path) -> None:
        (tmp_path / "session_id").write_text("sess-abc-123", encoding="utf-8")
        mod = _import_bootstrap()
        assert mod._read_session_id(tmp_path) == "sess-abc-123"

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        (tmp_path / "session_id").write_text("  sess-abc  \n", encoding="utf-8")
        mod = _import_bootstrap()
        assert mod._read_session_id(tmp_path) == "sess-abc"

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        mod = _import_bootstrap()
        with pytest.raises(RuntimeError, match="session identity not yet available"):
            mod._read_session_id(tmp_path)

    def test_raises_when_file_empty(self, tmp_path: Path) -> None:
        (tmp_path / "session_id").write_text("", encoding="utf-8")
        mod = _import_bootstrap()
        with pytest.raises(RuntimeError, match="session identity file is empty"):
            mod._read_session_id(tmp_path)


class TestBuildDialogueFactory:
    """Tests for _build_dialogue_factory from the bootstrap script."""

    def test_factory_returns_dialogue_controller(self, tmp_path: Path) -> None:
        (tmp_path / "session_id").write_text("sess-test", encoding="utf-8")
        mod = _import_bootstrap()

        from server.control_plane import ControlPlane
        from server.journal import OperationJournal

        journal = OperationJournal(tmp_path)
        # Use a minimal control plane with a no-op compat checker
        control_plane = ControlPlane(
            plugin_data_path=tmp_path,
            journal=journal,
            compat_checker=lambda: type("R", (), {"codex_version": None, "passed": False, "errors": (), "available_methods": frozenset()})(),
        )

        factory = mod._build_dialogue_factory(
            plugin_data_path=tmp_path,
            control_plane=control_plane,
            journal=journal,
        )
        controller = factory()

        from server.dialogue import DialogueController
        assert isinstance(controller, DialogueController)

    def test_factory_raises_when_session_id_missing(self, tmp_path: Path) -> None:
        mod = _import_bootstrap()

        from server.control_plane import ControlPlane
        from server.journal import OperationJournal

        journal = OperationJournal(tmp_path)
        control_plane = ControlPlane(
            plugin_data_path=tmp_path,
            journal=journal,
            compat_checker=lambda: type("R", (), {"codex_version": None, "passed": False, "errors": (), "available_methods": frozenset()})(),
        )

        factory = mod._build_dialogue_factory(
            plugin_data_path=tmp_path,
            control_plane=control_plane,
            journal=journal,
        )
        with pytest.raises(RuntimeError, match="session identity not yet available"):
            factory()


class TestPublishSessionIdHook:
    """Tests for the SessionStart hook script."""

    def test_writes_session_id_to_plugin_data(self, tmp_path: Path) -> None:
        payload = json.dumps({"session_id": "sess-hook-test", "cwd": "/tmp"})
        result = subprocess.run(
            [sys.executable, str(_hook_path)],
            input=payload,
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_DATA": str(tmp_path)},
            timeout=5,
        )
        assert result.returncode == 0
        assert (tmp_path / "session_id").read_text(encoding="utf-8") == "sess-hook-test"

    def test_overwrites_stale_session_id(self, tmp_path: Path) -> None:
        (tmp_path / "session_id").write_text("old-session", encoding="utf-8")
        payload = json.dumps({"session_id": "new-session"})
        subprocess.run(
            [sys.executable, str(_hook_path)],
            input=payload,
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_DATA": str(tmp_path)},
            timeout=5,
        )
        assert (tmp_path / "session_id").read_text(encoding="utf-8") == "new-session"

    def test_noop_without_plugin_data_env(self) -> None:
        payload = json.dumps({"session_id": "sess-noop"})
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_DATA"}
        result = subprocess.run(
            [sys.executable, str(_hook_path)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )
        assert result.returncode == 0

    def test_noop_on_missing_session_id_in_payload(self, tmp_path: Path) -> None:
        payload = json.dumps({"cwd": "/tmp"})
        subprocess.run(
            [sys.executable, str(_hook_path)],
            input=payload,
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_DATA": str(tmp_path)},
            timeout=5,
        )
        assert not (tmp_path / "session_id").exists()

    def test_noop_on_invalid_json_input(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(_hook_path)],
            input="not json",
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_DATA": str(tmp_path)},
            timeout=5,
        )
        assert result.returncode == 0
        assert not (tmp_path / "session_id").exists()
