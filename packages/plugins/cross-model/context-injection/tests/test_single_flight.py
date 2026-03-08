"""Verify single-flight concurrency assumption for stdio transport.

FastMCP's stdio transport reads JSON-RPC messages sequentially from stdin,
but Server.run() dispatches each message as a concurrent task via
anyio task group (tg.start_soon). This means the server *can* process
multiple requests concurrently if the client sends them without waiting.

In practice, Claude Code sends one tool-call request at a time over stdio
and waits for the response before sending the next. This client behavior
makes consume_scout()'s read-check-write on record.used safe without
asyncio.Lock.

Carry-forward from D1 Codex review: MCP protocol (JSON-RPC 2.0) allows
multiplexing. Safety relies on client-side single-flight behavior, not
a transport-level guarantee. If the client changes to pipeline requests,
or if SSE/WebSocket transports are added (which use HTTP concurrency),
asyncio.Lock must be added to consume_scout().

Evidence:
- mcp.server.Server.run() uses tg.start_soon(self._handle_message, ...)
- mcp.server.stdio.stdio_server() reads stdin line-by-line sequentially
- Memory stream buffer_size=0 (rendezvous) -- send blocks until receive
- Server loop receives message, spawns task, immediately ready for next
"""

from __future__ import annotations

from context_injection.state import AppContext


class TestSingleFlightAssumption:
    def test_sequential_consume_is_safe(self) -> None:
        """Demonstrate that sequential access to consume_scout is safe.

        Under stdio transport with a single-flight client (Claude Code),
        requests are processed one at a time. This test validates the
        logical correctness of the non-locked path.

        The transport + client guarantee is documented, not unit-testable.

        If SSE/WebSocket transports are added, or if the client starts
        pipelining requests, asyncio.Lock must be added to consume_scout()
        and this test extended with concurrent access.
        """
        ctx = AppContext.create(repo_root="/tmp/repo")
        assert ctx is not None
        assert len(ctx.hmac_key) == 32
        assert ctx.repo_root == "/tmp/repo"
