"""MCP server scaffolding with serialized dispatch.

Stdio JSON-RPC 2.0 server exposing all R1+R2 tools. Processes one tool call
at a time (serialization invariant per delivery.md §R2 in-scope).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

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
                "profile": {
                    "type": "string",
                    "description": "Named consultation profile (e.g., quick-check, deep-review)",
                },
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
                "profile": {
                    "type": "string",
                    "description": "Named consultation profile — resolved once at start, persisted for all subsequent replies",
                },
                "posture": {
                    "type": "string",
                    "enum": [
                        "collaborative",
                        "adversarial",
                        "exploratory",
                        "evaluative",
                        "comparative",
                    ],
                    "description": "Explicit posture override — takes precedence over profile posture",
                },
                "turn_budget": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 15,
                    "description": "Explicit turn budget override — takes precedence over profile turn_budget",
                },
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
    {
        "name": "codex.delegate.start",
        "description": "Start an isolated execution job. Creates a worktree and bootstraps an ephemeral execution runtime. Does not dispatch the first turn.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {
                    "type": "string",
                    "description": "Repository root path",
                },
                "base_commit": {
                    "type": "string",
                    "description": "Optional — the commit SHA to base the worktree on. Defaults to current HEAD of repo_root.",
                },
            },
            "required": ["repo_root"],
        },
    },
]


class McpServer:
    """Synchronous MCP server with serialized tool dispatch."""

    def __init__(
        self,
        *,
        control_plane: Any,
        dialogue_controller: Any | None = None,
        dialogue_factory: Callable[[], Any] | None = None,
        delegation_controller: Any | None = None,
        delegation_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._dialogue_controller = dialogue_controller
        self._dialogue_factory = dialogue_factory
        self._delegation_controller = delegation_controller
        self._delegation_factory = delegation_factory
        self._initialized = False
        self._recovery_completed = False

    def startup(self) -> None:
        """One-shot startup recovery. Idempotent — second call is a no-op.

        If a controller was provided directly at construction, runs recovery
        immediately. If a controller is deferred via factory, recovery runs
        on first tool call instead (via _ensure_*_controller).
        """
        if self._recovery_completed:
            return
        if self._dialogue_controller is not None:
            self._dialogue_controller.recover_startup()
        if self._delegation_controller is not None:
            self._delegation_controller.recover_startup()
        self._recovery_completed = True

    def _ensure_dialogue_controller(self) -> Any:
        """Return the dialogue controller, lazily initializing from factory if needed.

        One-way pin: the factory is called at most once. The resulting controller
        is cached for the process lifetime. The factory reference is cleared after
        use to prevent re-initialization.
        """
        if self._dialogue_controller is not None:
            return self._dialogue_controller
        if self._dialogue_factory is None:
            raise RuntimeError(
                "Dialogue dispatch failed: no dialogue controller available. "
                "Session identity may not have been published yet."
            )
        controller = self._dialogue_factory()
        controller.recover_startup()
        # Pin only after recovery succeeds — transient failures allow retry
        self._dialogue_controller = controller
        self._dialogue_factory = None
        return self._dialogue_controller

    def _ensure_delegation_controller(self) -> Any:
        """Return the delegation controller, lazily initializing from factory if needed.

        Mirrors _ensure_dialogue_controller exactly: build from factory, run
        recovery, then pin. The recover_startup() call BEFORE pinning is
        load-bearing — production deploys via delegation_factory (Task 9), so
        without this call the consumer-half of AC 4 would never run on the
        path that matters. See _ensure_dialogue_controller for the dialogue
        precedent. Pin only after recovery succeeds — transient failures allow
        retry.
        """
        if self._delegation_controller is not None:
            return self._delegation_controller
        if self._delegation_factory is None:
            raise RuntimeError(
                "Delegation dispatch failed: no delegation controller available. "
                "Session identity may not have been published yet."
            )
        controller = self._delegation_factory()
        controller.recover_startup()
        # Pin only after recovery succeeds — transient failures allow retry
        self._delegation_controller = controller
        self._delegation_factory = None
        return self._delegation_controller

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

    def _handle_initialize(self, req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
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

    def _handle_tools_call(self, req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
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
        # INVARIANT: safe only while this is the sole serialized dispatch
        # chokepoint. Any concurrent dispatch model must revisit advisory
        # locking and turn sequencing.
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
                profile=arguments.get("profile"),
            )
            result = self._control_plane.codex_consult(request)
            return asdict(result)
        if name == "codex.dialogue.start":
            controller = self._ensure_dialogue_controller()
            result = controller.start(
                Path(arguments["repo_root"]),
                profile_name=arguments.get("profile"),
                explicit_posture=arguments.get("posture"),
                explicit_turn_budget=arguments.get("turn_budget"),
            )
            return asdict(result)
        if name == "codex.dialogue.reply":
            controller = self._ensure_dialogue_controller()
            result = controller.reply(
                collaboration_id=arguments["collaboration_id"],
                objective=arguments["objective"],
                explicit_paths=tuple(
                    Path(p) for p in arguments.get("explicit_paths", ())
                ),
            )
            return asdict(result)
        if name == "codex.dialogue.read":
            controller = self._ensure_dialogue_controller()
            result = controller.read(arguments["collaboration_id"])
            return asdict(result)
        if name == "codex.delegate.start":
            controller = self._ensure_delegation_controller()
            result = controller.start(
                repo_root=Path(arguments["repo_root"]),
                base_commit=arguments.get("base_commit"),
            )
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
