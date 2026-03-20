"""Thin MCP compatibility shim for codex consultation.

Exposes two FastMCP tools (``codex`` and ``codex-reply``) that translate
MCP tool parameters to the codex_consult adapter and format responses
as structuredContent with threadId.

Translation-only: no safety, analytics, or continuity logic.
Safety is enforced by codex_guard.py PreToolUse hook (fires on MCP tool
name prefix ``mcp__plugin_cross-model_codex__``). Analytics are owned
by skills.

Design: D-prime architecture — adapter owns transport, shim provides
backward-compatible MCP interface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

if __package__:
    from scripts.codex_consult import consult
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from codex_consult import consult  # type: ignore[import-not-found,no-redef]


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def _extract_reasoning_effort(config: dict[str, Any] | None) -> str:
    """Extract model_reasoning_effort from MCP config object."""
    if config and isinstance(config.get("model_reasoning_effort"), str):
        return config["model_reasoning_effort"]
    return "xhigh"
