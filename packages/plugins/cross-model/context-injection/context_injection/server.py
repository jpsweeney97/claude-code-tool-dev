"""Context injection MCP server.

Entry point: python -m context_injection
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP

from context_injection.execute import execute_scout
from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import ScoutRequest, TurnRequest


def _check_posix() -> None:
    """Startup gate: reject non-POSIX platforms."""
    if os.name != "posix":
        raise RuntimeError(
            f"context-injection requires POSIX (macOS/Linux/WSL). "
            f"Got: os.name={os.name!r}"
        )


def _check_git_available() -> None:
    """Startup gate: reject if git is not on PATH."""
    if shutil.which("git") is None:
        raise RuntimeError(
            "context-injection requires git. git not found on PATH."
        )


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize per-process state: HMAC key, git file list, store.

    Startup gates: POSIX platform + git availability (fail-fast).
    """
    _check_posix()
    _check_git_available()
    repo_root = os.environ.get("REPO_ROOT", os.getcwd())
    git_files = _load_git_files(repo_root)
    ctx = AppContext.create(repo_root=repo_root, git_files=git_files)
    yield ctx


def _load_git_files(repo_root: str) -> set[str]:
    """Load tracked file list from git ls-files.

    Fail closed: empty set means all files denied by git gating.
    """
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


def create_server() -> FastMCP:
    """Create the FastMCP instance. Useful for testing without starting stdio."""
    mcp = FastMCP(
        "context-injection",
        lifespan=app_lifespan,
    )

    @mcp.tool(name="process_turn")
    def process_turn_tool(
        request: TurnRequest,
        ctx: Context,
    ) -> dict:
        """Process a TurnRequest (Call 1) and return a TurnPacket."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        result = process_turn(request, app_ctx)
        # Return dict to avoid FastMCP double-serialization of discriminated unions.
        # TurnPacket uses Annotated[Union[...], Discriminator(...)] which the SDK's
        # serializer may not handle correctly.
        return result.model_dump(mode="json")

    @mcp.tool(name="execute_scout")
    def execute_scout_tool(
        request: ScoutRequest,
        ctx: Context,
    ) -> dict:
        """Execute a scout (Call 2) and return a ScoutResult."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        result = execute_scout(app_ctx, request)
        # Same model_dump workaround as process_turn_tool -- ScoutResult is
        # a discriminated union that the SDK may not serialize correctly.
        return result.model_dump(mode="json")

    return mcp


def main() -> None:
    """Entry point for python -m context_injection."""
    server = create_server()
    server.run()
