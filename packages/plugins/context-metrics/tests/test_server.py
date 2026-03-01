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
