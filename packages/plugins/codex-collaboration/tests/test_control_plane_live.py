"""Live control-plane checks against the installed codex binary."""

from __future__ import annotations

import shutil

from pathlib import Path

import pytest

from server.codex_compat import get_codex_version
from server.control_plane import ControlPlane

pytestmark = pytest.mark.skipif(
    shutil.which("codex") is None,
    reason="codex binary not found on PATH",
)


def test_codex_status_live_reports_runtime_surface(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]
    plane = ControlPlane(plugin_data_path=tmp_path / "plugin-data")
    try:
        status = plane.codex_status(repo_root)
    finally:
        plane.close()

    assert status["codex_version"] == str(get_codex_version())
    assert status["app_server_version"] is not None
    assert status["auth_status"] in {"authenticated", "missing", "expired"}
    assert status["required_methods"]["thread/start"] is True
    assert isinstance(status["optional_methods"]["turn/steer"], bool)
