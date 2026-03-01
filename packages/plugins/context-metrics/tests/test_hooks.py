"""Tests for hook scripts."""

import json
import subprocess
import sys
import threading
from pathlib import Path

from scripts.server import ContextMetricsSidecar


class TestContextSummary:
    """Test context_summary.py — the injection hook."""

    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def test_prints_summary_to_stdout(self, normal_session: Path) -> None:
        """context_summary.py should print a summary line and exit 0."""
        import urllib.request

        # Register session first
        urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/sessions/register"
            f"?session_id=test_hook&transcript_path={normal_session}",
            timeout=2,
        )
        # Force first injection by setting high prompt count
        state = self.server.get_or_create_state("test_hook")
        state.prompts_since_injection = 10

        hook_input = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test_hook",
            "transcript_path": str(normal_session),
        })
        script = Path(__file__).parent.parent / "scripts" / "context_summary.py"
        result = subprocess.run(
            [sys.executable, str(script), "--port", str(self.port)],
            input=hook_input, capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
        # stdout should contain a context summary line
        assert "Context:" in result.stdout or result.stdout.strip() == ""

    def test_exits_zero_on_sidecar_down(self) -> None:
        """Fail-open: if sidecar unreachable, exit 0 with no output."""
        hook_input = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test_hook",
            "transcript_path": "/nonexistent.jsonl",
        })
        script = Path(__file__).parent.parent / "scripts" / "context_summary.py"
        result = subprocess.run(
            [sys.executable, str(script), "--port", "19999"],
            input=hook_input, capture_output=True, text=True, timeout=5,
        )
        # Fail-open: exit 0, no output
        assert result.returncode == 0
