"""Sidecar HTTP server for context metrics.

Shared server on port 7432. Manages sessions, reads JSONL, evaluates
triggers, and returns injection decisions. Fail-open at injection layer,
fail-closed at data layer.

Architecture: shared sidecar (one per machine) manages sessions via registry,
reads JSONL for occupancy, evaluates trigger thresholds, and returns injection
decisions. Fail-open at injection layer (errors -> no output), fail-closed at
data layer (bad data -> no injection).
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.config import Config, read_config
from scripts.formatter import format_compaction, format_full, format_minimal
from scripts.jsonl_reader import compute_occupancy, count_messages, tail_read_last_valid
from scripts.session_registry import SessionRegistry
from scripts.trigger_engine import SessionState, TriggerEngine

logger = logging.getLogger("context-metrics-sidecar")

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"
CONFIG_PATH = Path.home() / ".claude" / "context-metrics.local.md"


class ContextMetricsSidecar(HTTPServer):
    def __init__(self, port: int = DEFAULT_PORT, config_path: Path | None = None) -> None:
        self.registry = SessionRegistry()
        self.config = read_config(config_path or CONFIG_PATH)
        self.trigger_engine = TriggerEngine(self.config.context_window)
        self.session_states: dict[str, SessionState] = {}
        self._states_lock = threading.Lock()
        super().__init__(("127.0.0.1", port), _RequestHandler)

    def get_or_create_state(self, session_id: str) -> SessionState:
        with self._states_lock:
            if session_id not in self.session_states:
                self.session_states[session_id] = SessionState()
            return self.session_states[session_id]

    def remove_state(self, session_id: str) -> None:
        with self._states_lock:
            self.session_states.pop(session_id, None)


class _RequestHandler(BaseHTTPRequestHandler):
    server: ContextMetricsSidecar

    def log_message(self, format: str, *args: object) -> None:
        logger.debug(format, *args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self._respond_json(200, {
                "status": "ok",
                "active_sessions": self.server.registry.active_count(),
            })
        elif path == "/sessions/register":
            session_id = params.get("session_id", [None])[0]
            transcript_path = params.get("transcript_path", [None])[0]
            if not session_id or not transcript_path:
                self._respond_json(400, {"error": "session_id and transcript_path required"})
                return
            self.server.registry.register(session_id, transcript_path)
            self.server.get_or_create_state(session_id)
            self._respond_json(200, {"registered": True, "session_id": session_id})
        elif path == "/sessions/deregister":
            session_id = params.get("session_id", [None])[0]
            if not session_id:
                self._respond_json(400, {"error": "session_id required"})
                return
            removed = self.server.registry.deregister(session_id)
            if removed:
                self.server.remove_state(session_id)
            self._respond_json(200, {
                "deregistered": removed,
                "active_sessions": self.server.registry.active_count(),
            })
        elif path == "/sessions/compaction":
            session_id = params.get("session_id", [None])[0]
            if not session_id:
                self._respond_json(400, {"error": "session_id required"})
                return
            state = self.server.get_or_create_state(session_id)
            state.compaction_pending = True
            self._respond_json(200, {"compaction_pending": True, "session_id": session_id})
        else:
            self._respond_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/hooks/context-metrics":
            self._respond_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._respond_json(200, {"inject": False, "reason": "invalid input"})
            return

        self._handle_hook(body)

    def _handle_hook(self, hook_input: dict) -> None:
        """Process a hook request. Fail-open: errors -> no injection."""
        session_id = hook_input.get("session_id", "")
        transcript_path = hook_input.get("transcript_path", "")

        # Derive session_id from transcript_path if not provided
        if not session_id and transcript_path:
            session_id = Path(transcript_path).stem

        # Read JSONL — fail-closed (data layer)
        record = tail_read_last_valid(Path(transcript_path)) if transcript_path else None
        if record is None:
            self._respond_json(200, {"inject": False, "reason": "no valid JSONL record"})
            return

        message = record.get("message", {})
        usage = message.get("usage", {})
        occupancy = compute_occupancy(usage)

        # Detect context window: model name (proactive) then occupancy (fallback)
        model = message.get("model", "")
        if model:
            self.server.config.detect_window_from_model(model)
        self.server.config.maybe_upgrade_window(occupancy)
        self.server.trigger_engine.window_size = self.server.config.context_window

        # Renew lease
        self.server.registry.renew(session_id)

        # Evaluate triggers
        state = self.server.get_or_create_state(session_id)
        result = self.server.trigger_engine.evaluate(state, occupancy)

        if not result.should_inject:
            self.server.trigger_engine.apply_result(state, result, occupancy)
            self._respond_json(200, {"inject": False, "reason": "below threshold"})
            return

        # Count messages (forward scan)
        msg_count = count_messages(Path(transcript_path)) if transcript_path else 0

        # Format summary (before apply_result to preserve compaction numbering)
        window = self.server.config.context_window

        if result.format == "minimal":
            summary = format_minimal(occupancy=occupancy, window=window)
        elif result.format == "compaction":
            summary = format_compaction(
                occupancy=occupancy, window=window,
                compaction_number=state.compaction_count + 1,
                message_count=msg_count, cost_usd=None,
                soft_boundary=self.server.config.soft_boundary,
            )
        else:
            summary = format_full(
                occupancy=occupancy, window=window,
                message_count=msg_count, compaction_count=state.compaction_count,
                cost_usd=None, soft_boundary=self.server.config.soft_boundary,
            )

        # Delivered semantics: only advance state if the response is delivered.
        # If the client disconnects, state stays put so the next request re-triggers.
        delivered = self._try_send_hook_response({
            "inject": True,
            "summary": summary,
            "format": result.format,
            "triggers": result.triggers_fired,
        })
        if delivered:
            self.server.trigger_engine.apply_result(state, result, occupancy)

    def _try_send_hook_response(self, data: dict) -> bool:
        """Send hook response, returning True if delivered.

        Catches client-disconnect errors (broken pipe, connection reset)
        without hiding other failures.
        """
        try:
            self._respond_json(200, data)
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return False

    def _respond_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def write_pid_file() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def remove_pid_file() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    """Start the sidecar server."""
    import argparse

    parser = argparse.ArgumentParser(description="Context metrics sidecar")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    server = ContextMetricsSidecar(port=args.port)
    write_pid_file()

    def shutdown_handler(signum: int, frame: object) -> None:
        logger.info("Shutting down sidecar (signal %d)", signum)
        # Spawn daemon thread for shutdown — calling server.shutdown() on the
        # main thread deadlocks because serve_forever() holds __is_shut_down
        # and shutdown() waits for it, but serve_forever() can't proceed until
        # this signal handler returns.
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    logger.info("Sidecar listening on port %d", args.port)
    try:
        server.serve_forever()
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
