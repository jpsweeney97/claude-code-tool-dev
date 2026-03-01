"""Tests for sidecar HTTP server."""

import json
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

from scripts.server import ContextMetricsSidecar


def _get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _post(url: str, data: dict) -> tuple[int, str]:
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _post_raw(url: str, body: bytes) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


class TestSidecarServer:
    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)  # Random port
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def test_health_check(self) -> None:
        status, body = _get(f"{self.base}/health")
        assert status == 200
        data = json.loads(body)
        assert data["status"] == "ok"

    def test_register_session(self) -> None:
        status, body = _get(
            f"{self.base}/sessions/register?session_id=test1&transcript_path=/tmp/test.jsonl"
        )
        assert status == 200
        data = json.loads(body)
        assert data["registered"] is True

    def test_deregister_session(self) -> None:
        _get(f"{self.base}/sessions/register?session_id=test1&transcript_path=/tmp/test.jsonl")
        status, body = _get(f"{self.base}/sessions/deregister?session_id=test1")
        assert status == 200
        data = json.loads(body)
        assert data["deregistered"] is True

    def test_hook_with_registered_session(self, normal_session: Path) -> None:
        # Register with a real fixture path
        _get(
            f"{self.base}/sessions/register?session_id=test1"
            f"&transcript_path={normal_session}"
        )
        # POST hook input (simplified)
        hook_input = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test1",
            "transcript_path": str(normal_session),
        }
        status, body = _post(f"{self.base}/hooks/context-metrics", hook_input)
        assert status == 200
        data = json.loads(body)
        # Should have a result (may or may not inject based on trigger state)
        assert "inject" in data

    def test_compaction_sets_pending(self, normal_session: Path) -> None:
        """Compaction endpoint sets compaction_pending, enabling compaction trigger."""
        _get(
            f"{self.base}/sessions/register?session_id=test1"
            f"&transcript_path={normal_session}"
        )
        # First hook call: triggers injection (boundary crossing), resets state
        _post(f"{self.base}/hooks/context-metrics", {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test1",
            "transcript_path": str(normal_session),
        })
        # Set compaction pending
        status, body = _get(f"{self.base}/sessions/compaction?session_id=test1")
        assert status == 200
        data = json.loads(body)
        assert data["compaction_pending"] is True
        # Next hook call should trigger compaction format
        status, body = _post(f"{self.base}/hooks/context-metrics", {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test1",
            "transcript_path": str(normal_session),
        })
        data = json.loads(body)
        assert data["inject"] is True
        assert data["format"] == "compaction"
        assert "compaction" in data["triggers"]

    def test_hook_detects_model_window(self, normal_session: Path) -> None:
        """Model field in JSONL triggers context window detection."""
        # normal_session fixture has model: claude-opus-4-6
        _get(
            f"{self.base}/sessions/register?session_id=test_model"
            f"&transcript_path={normal_session}"
        )
        # Before hook: default 200k
        assert self.server.config.context_window == 200_000
        _post(f"{self.base}/hooks/context-metrics", {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test_model",
            "transcript_path": str(normal_session),
        })
        # After hook: detected 1M from claude-opus-4-6
        assert self.server.config.context_window == 1_000_000

    def test_hook_with_unknown_session_fails_open(self) -> None:
        hook_input = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "unknown",
            "transcript_path": "/nonexistent.jsonl",
        }
        status, body = _post(f"{self.base}/hooks/context-metrics", hook_input)
        assert status == 200
        data = json.loads(body)
        assert data["inject"] is False

    # --- Validation path tests (I4) ---

    def test_unknown_get_path_returns_404(self) -> None:
        status, body = _get(f"{self.base}/nonexistent")
        assert status == 404
        data = json.loads(body)
        assert data["error"] == "not found"

    def test_unknown_post_path_returns_404(self) -> None:
        status, body = _post(f"{self.base}/hooks/unknown", {"foo": "bar"})
        assert status == 404
        data = json.loads(body)
        assert data["error"] == "not found"

    def test_register_missing_params_returns_400(self) -> None:
        status, body = _get(f"{self.base}/sessions/register?session_id=test1")
        assert status == 400
        data = json.loads(body)
        assert "required" in data["error"]

    def test_deregister_missing_session_id_returns_400(self) -> None:
        status, body = _get(f"{self.base}/sessions/deregister")
        assert status == 400
        data = json.loads(body)
        assert "required" in data["error"]

    def test_compaction_missing_session_id_returns_400(self) -> None:
        status, body = _get(f"{self.base}/sessions/compaction")
        assert status == 400
        data = json.loads(body)
        assert "required" in data["error"]

    def test_hook_malformed_json_fails_open(self) -> None:
        status, body = _post_raw(
            f"{self.base}/hooks/context-metrics", b"not valid json{{"
        )
        assert status == 200
        data = json.loads(body)
        assert data["inject"] is False
        assert data["reason"] == "invalid input"

    def test_hook_empty_body_fails_open(self) -> None:
        status, body = _post_raw(f"{self.base}/hooks/context-metrics", b"")
        assert status == 200
        data = json.loads(body)
        assert data["inject"] is False
