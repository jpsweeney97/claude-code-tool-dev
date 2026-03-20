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


def _build_response(result: dict) -> CallToolResult:
    """Translate adapter result to MCP CallToolResult with structuredContent.

    Success responses include structuredContent.threadId for consumers.
    Timeout responses include structuredContent with partial continuation_id
    (agents may use it for recovery). Block/error responses omit structuredContent.
    """
    status = result.get("status", "error")
    response_text = result.get("response_text") or ""
    continuation_id = result.get("continuation_id")

    if status == "timeout_uncertain":
        error_msg = result.get("error", "unknown error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Timeout: {error_msg}")],
            structuredContent={"threadId": continuation_id, "content": ""},
            isError=True,
        )

    if status in ("blocked", "error"):
        error_label = "Blocked" if status == "blocked" else "Error"
        error_msg = result.get("error", "unknown error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"{error_label}: {error_msg}")],
            isError=True,
        )

    return CallToolResult(
        content=[TextContent(type="text", text=response_text)],
        structuredContent={
            "threadId": continuation_id,
            "content": response_text,
        },
    )


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------


def create_server() -> FastMCP:
    """Create the codex MCP shim server."""
    mcp = FastMCP("codex")

    @mcp.tool(name="codex")
    def codex_tool(
        prompt: str,
        sandbox: str | None = None,
        model: str | None = None,
        approval_policy: str | None = None,
        config: dict | None = None,
        profile: str | None = None,
    ) -> CallToolResult:
        """Start a new Codex consultation."""
        result = consult(
            prompt=prompt,
            model=model,
            reasoning_effort=_extract_reasoning_effort(config),
        )
        return _build_response(result)

    @mcp.tool(name="codex-reply")
    def codex_reply_tool(prompt: str, threadId: str) -> CallToolResult:
        """Continue an existing Codex conversation."""
        result = consult(prompt=prompt, thread_id=threadId)
        return _build_response(result)

    return mcp


def main() -> None:
    """Entry point for the codex MCP shim server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
