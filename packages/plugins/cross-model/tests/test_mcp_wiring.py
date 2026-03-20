"""Tests for .mcp.json codex entry wiring.

Validates that the codex MCP server entry in .mcp.json points to the local
codex_shim.py FastMCP server (not the upstream codex mcp-server binary).
"""

import json
from pathlib import Path

import pytest

_MCP_JSON = Path(__file__).resolve().parent.parent / ".mcp.json"


@pytest.fixture
def mcp_config():
    """Load .mcp.json config."""
    with open(_MCP_JSON) as f:
        return json.load(f)


@pytest.fixture
def codex_entry(mcp_config):
    """Extract the codex server entry."""
    return mcp_config["mcpServers"]["codex"]


class TestMcpJsonWiring:
    """Verify .mcp.json codex entry is wired to the local shim."""

    def test_uses_uv_command(self, codex_entry):
        """Codex entry must use uv to resolve deps from pyproject.toml."""
        assert codex_entry["command"] == "uv"

    def test_uses_direct_script_path(self, codex_entry):
        """Direct script path required — python -m has cwd fragility."""
        args = codex_entry["args"]
        assert "-m" not in args, "Must use direct script path, not python -m"
        assert any("codex_shim.py" in arg for arg in args)

    def test_preserves_sandbox_env(self, codex_entry):
        """CODEX_SANDBOX=seatbelt must be set for defense-in-depth."""
        assert codex_entry["env"]["CODEX_SANDBOX"] == "seatbelt"

    def test_server_key_is_codex(self, mcp_config):
        """Server key must be 'codex' for MCP tool name derivation."""
        assert "codex" in mcp_config["mcpServers"]
