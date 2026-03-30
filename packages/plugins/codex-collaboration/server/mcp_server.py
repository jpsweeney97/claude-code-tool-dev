"""MCP server scaffolding with serialized dispatch.

Stdio JSON-RPC 2.0 server exposing all R1+R2 tools. Processes one tool call
at a time (serialization invariant per delivery.md §R2 in-scope).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "codex.status",
        "description": "Health, auth, version, and runtime diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string", "description": "Repository root path"},
            },
            "required": ["repo_root"],
        },
    },
    {
        "name": "codex.consult",
        "description": "One-shot second opinion using the advisory runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string"},
                "objective": {"type": "string"},
                "explicit_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo_root", "objective"],
        },
    },
    {
        "name": "codex.dialogue.start",
        "description": "Create a durable dialogue thread in the advisory runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string", "description": "Repository root path"},
            },
            "required": ["repo_root"],
        },
    },
    {
        "name": "codex.dialogue.reply",
        "description": "Continue a dialogue turn on an existing handle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collaboration_id": {"type": "string"},
                "objective": {"type": "string"},
                "explicit_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["collaboration_id", "objective"],
        },
    },
    {
        "name": "codex.dialogue.read",
        "description": "Read dialogue state for a given collaboration_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collaboration_id": {"type": "string"},
            },
            "required": ["collaboration_id"],
        },
    },
]


class McpServer:
    """Synchronous MCP server with serialized tool dispatch."""

    def __init__(
        self,
        *,
        control_plane: Any,
        dialogue_controller: Any,
    ) -> None:
        self._control_plane = control_plane
        self._dialogue_controller = dialogue_controller
        self._initialized = False
        self._recovery_completed = False

    def startup(self) -> None:
        """One-shot startup recovery. Idempotent — second call is a no-op."""
        if self._recovery_completed:
            return
        self._dialogue_controller.recover_startup()
        self._recovery_completed = True

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a single JSON-RPC 2.0 request and return the response."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return self._handle_initialize(req_id, params)
        if method == "notifications/initialized":
            return {}  # notification, no response
        if method == "tools/list":
            return self._handle_tools_list(req_id)
        if method == "tools/call":
            return self._handle_tools_call(req_id, params)
        return _error_response(req_id, -32601, f"Method not found: {method}")

    def run(self) -> None:
        """Main loop: run startup recovery, then read JSON-RPC from stdin."""
        self.startup()
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                _write_response(_error_response(None, -32700, "Parse error"))
                continue
            response = self.handle_request(request)
            if response:
                _write_response(response)

    def _handle_initialize(
        self, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        self._initialized = True
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "codex-collaboration",
                    "version": "0.2.0",
                },
            },
        }

    def _handle_tools_list(self, req_id: Any) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOL_DEFINITIONS},
        }

    def _handle_tools_call(
        self, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = self._dispatch_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result, default=str)},
                    ],
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": str(exc)},
                    ],
                    "isError": True,
                },
            }

    def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Route a tool call to the appropriate handler. Serialization is
        guaranteed by the synchronous single-threaded main loop."""
        # Release posture item 3 is accepted only while this remains the sole
        # dispatch chokepoint and tool calls stay serialized. Any concurrent
        # dispatch model must revisit advisory locking and turn sequencing.
        if name == "codex.status":
            return self._control_plane.codex_status(Path(arguments["repo_root"]))
        if name == "codex.consult":
            from .models import ConsultRequest

            request = ConsultRequest(
                repo_root=Path(arguments["repo_root"]),
                objective=arguments["objective"],
                explicit_paths=tuple(
                    Path(p) for p in arguments.get("explicit_paths", ())
                ),
            )
            result = self._control_plane.codex_consult(request)
            return asdict(result)
        if name == "codex.dialogue.start":
            result = self._dialogue_controller.start(Path(arguments["repo_root"]))
            return asdict(result)
        if name == "codex.dialogue.reply":
            result = self._dialogue_controller.reply(
                collaboration_id=arguments["collaboration_id"],
                objective=arguments["objective"],
                explicit_paths=tuple(
                    Path(p) for p in arguments.get("explicit_paths", ())
                ),
            )
            return asdict(result)
        if name == "codex.dialogue.read":
            result = self._dialogue_controller.read(arguments["collaboration_id"])
            return asdict(result)
        raise ValueError(f"Unknown tool: {name!r:.100}")


def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _write_response(response: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
