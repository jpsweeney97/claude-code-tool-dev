"""Shared fixtures for codex-collaboration tests."""

from pathlib import Path

import pytest

from server.codex_compat import TESTED_CODEX_VERSION

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "codex-app-server" / TESTED_CODEX_VERSION


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
