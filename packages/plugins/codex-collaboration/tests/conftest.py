"""Shared fixtures for codex-collaboration tests."""

from pathlib import Path

import pytest

from server.codex_compat import TESTED_CODEX_VERSION

FIXTURES_DIR = (
    Path(__file__).parent / "fixtures" / "codex-app-server" / TESTED_CODEX_VERSION
)


@pytest.fixture
def vendored_schema_dir() -> Path:
    """Path to the vendored schema bundle for the tested version."""
    if not FIXTURES_DIR.is_dir():
        pytest.skip(f"Vendored schema not found at {FIXTURES_DIR}")
    return FIXTURES_DIR


@pytest.fixture
def client_request_schema(vendored_schema_dir: Path) -> Path:
    """Path to the vendored ClientRequest.json."""
    path = vendored_schema_dir / "ClientRequest.json"
    if not path.exists():
        pytest.skip("ClientRequest.json not found in vendored schema")
    return path


from server.models import CollaborationHandle


def make_test_handle(
    collaboration_id: str = "collab-1",
    runtime_id: str = "rt-1",
    thread_id: str = "thr-1",
    session_id: str = "sess-1",
    repo_root: str = "/repo",
    status: str = "active",
) -> CollaborationHandle:
    """Factory for test CollaborationHandle instances."""
    return CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="advisory",
        runtime_id=runtime_id,
        codex_thread_id=thread_id,
        claude_session_id=session_id,
        repo_root=repo_root,
        created_at="2026-03-28T00:00:00Z",
        status=status,
    )
