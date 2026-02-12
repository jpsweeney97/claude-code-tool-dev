"""Context injection MCP server.

Entry point: python -m context_injection
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP

from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import TurnRequest


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize per-process state: HMAC key, git file list, store."""
    repo_root = os.environ.get("REPO_ROOT", os.getcwd())
    git_files = _load_git_files(repo_root)
    ctx = AppContext.create(repo_root=repo_root, git_files=git_files)
    yield ctx


def _load_git_files(repo_root: str) -> set[str]:
    """Load tracked file list from git ls-files. Fail closed on error."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git ls-files failed: {result.stderr}")
        return set(result.stdout.splitlines())
    except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError):
        # Fail closed: empty set means all files are "not tracked"
        return set()


def create_server(repo_root: str | None = None) -> FastMCP:
    """Create the FastMCP instance (useful for testing without running)."""
    mcp = FastMCP(
        "context-injection",
        lifespan=app_lifespan,
    )

    @mcp.tool()
    def process_turn_tool(
        request: TurnRequest,
        ctx: Context,
    ) -> dict:
        """Process a TurnRequest (Call 1) and return a TurnPacket."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        result = process_turn(request, app_ctx)
        return result.model_dump(mode="json")

    return mcp


def main() -> None:
    """Entry point for python -m context_injection."""
    server = create_server()
    server.run()
