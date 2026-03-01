"""Integration tests for the full context-metrics pipeline.

Tests the end-to-end flow: sidecar + JSONL fixtures + trigger evaluation + formatting.
"""

import json
import threading
import urllib.request
from pathlib import Path

from scripts.server import ContextMetricsSidecar


class TestEndToEnd:
    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def _register(self, session_id: str, transcript_path: Path) -> None:
        urllib.request.urlopen(
            f"{self.base}/sessions/register?session_id={session_id}"
            f"&transcript_path={transcript_path}",
            timeout=2,
        )

    def _post_hook(self, session_id: str, transcript_path: Path) -> dict:
        payload = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": session_id,
            "transcript_path": str(transcript_path),
        }).encode()
        req = urllib.request.Request(
            f"{self.base}/hooks/context-metrics",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read())

    def test_first_prompt_injects_full(self, normal_session: Path) -> None:
        """First prompt should always inject (boundary crossing triggers)."""
        self._register("e2e_1", normal_session)
        result = self._post_hook("e2e_1", normal_session)
        assert result["inject"] is True
        assert "Context:" in result["summary"]
        assert result["format"] in ("full", "compaction")

    def test_second_prompt_suppressed_if_no_change(self, normal_session: Path) -> None:
        """Second prompt with same file should be suppressed (no delta)."""
        self._register("e2e_2", normal_session)
        self._post_hook("e2e_2", normal_session)  # First: injects
        result = self._post_hook("e2e_2", normal_session)  # Second: suppressed
        assert result["inject"] is False

    def test_heartbeat_fires_after_interval(self, normal_session: Path) -> None:
        """After enough suppressed prompts, heartbeat fires.

        HEARTBEAT_NORMAL = 8. After first injection resets counter to 0,
        need 8 suppressed prompts (counter 1..8) before the 9th sees
        counter == 8 >= 8 and fires heartbeat.
        """
        self._register("e2e_3", normal_session)
        self._post_hook("e2e_3", normal_session)  # First: injects (resets counter)
        # Suppress 8 prompts (counter goes 1..8)
        for _ in range(8):
            self._post_hook("e2e_3", normal_session)
        # 9th prompt after injection: counter == 8 >= HEARTBEAT_NORMAL, fires
        result = self._post_hook("e2e_3", normal_session)
        assert result["inject"] is True
        assert result["format"] == "minimal"
        assert "heartbeat" in result["triggers"]

    def test_near_boundary_uses_headroom_threshold(self, near_boundary: Path) -> None:
        """At 92% occupancy, headroom triggers should activate."""
        self._register("e2e_4", near_boundary)
        result = self._post_hook("e2e_4", near_boundary)
        assert result["inject"] is True
        # At 92%, the 90% boundary crossing should fire
        assert "boundary_crossing" in result["triggers"]

    def test_empty_file_fails_closed(self, empty_session: Path) -> None:
        """Empty JSONL -> no injection (fail-closed data layer)."""
        self._register("e2e_5", empty_session)
        result = self._post_hook("e2e_5", empty_session)
        assert result["inject"] is False
